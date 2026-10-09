"""Targeted retry of missing Q104:I19 SEC acceptance headers; never rescans holdings.

Inputs are immutable shard receipts from one completed census run. Only accession
numbers already present in receipt acceptance_failures are requested again.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from automation.q104_i19_13f_historical_identity_census import (
    CUTOFF,
    HEADER_REQUEST_GAP_SECONDS,
    RateLimiter,
    UA,
    accession_header_url,
    parse_acceptance_header,
)
from automation.q104_i19_13f_historical_identity_census_merge import EXPECTED_SHARDS

MAX_ATTEMPTS = 4
MAX_RETRY_DELAY_SECONDS = 30
RETRYABLE_HTTP = {404, 408, 425, 429, 500, 502, 503, 504}
RECOVERY_UA = "DWR-debug/trading-agent-public Q104-I19 targeted acceptance recovery/1.0"


def _fingerprint(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("receipt_fingerprint", None)
    raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_header_fields(
    body: bytes,
    accession: str,
    archive: dict[str, Any],
) -> dict[str, Any]:
    """Parse acceptance metadata from the official per-accession SEC SGML header.

    The accession was selected by the already-frozen 13F archive scan. As the
    failed run did not retain accession->submission.tsv rows in its artifact,
    this recovery binds filing metadata to the exact accession, checks the
    accession-derived CIK, form, filed date, report period and archive quarter,
    then hashes the raw header bytes. It does not re-run CUSIP/holdings scans.
    """
    text = body.decode("utf-8", "replace")
    acc_match = re.search(r"ACCESSION NUMBER:\\s*([0-9]{10}-[0-9]{2}-[0-9]{6})", text, re.I)
    cik_match = re.search(r"CENTRAL INDEX KEY:\\s*([0-9]{10})", text, re.I)
    form_match = re.search(r"CONFORMED SUBMISSION TYPE:\\s*([^\\s<]+)", text, re.I)
    filed_match = re.search(r"FILED AS OF DATE:\\s*([0-9]{8})", text, re.I)
    period_match = re.search(
        r"(?:CONFORMED PERIOD OF REPORT|PERIOD OF REPORT):\\s*([0-9]{8})", text, re.I
    )
    expected_cik = accession.split("-", 1)[0]
    if not acc_match or acc_match.group(1) != accession:
        raise ValueError("ACCESSION_MISMATCH")
    if not cik_match or cik_match.group(1) != expected_cik:
        raise ValueError("FILER_CIK_MISMATCH")
    if not form_match:
        raise ValueError("CONFORMED_SUBMISSION_TYPE_MISSING")
    form = form_match.group(1).strip().upper()
    if form not in {"13F-HR", "13F-HR/A"}:
        raise ValueError("UNEXPECTED_13F_FORM:" + form)
    if not filed_match:
        raise ValueError("FILED_AS_OF_DATE_MISSING")
    filing_date = datetime.strptime(filed_match.group(1), "%Y%m%d").date()
    if filing_date > CUTOFF:
        raise ValueError("FILING_AFTER_FROZEN_CUTOFF")
    if not period_match:
        raise ValueError("CONFORMED_PERIOD_OF_REPORT_MISSING")
    report_period = datetime.strptime(period_match.group(1), "%Y%m%d").date()
    if report_period > filing_date:
        raise ValueError("REPORT_PERIOD_AFTER_FILING_DATE")

    period_start = date.fromisoformat(str(archive.get("period_start", "")))
    month_after = period_start.month + 3
    quarter_end = date(
        period_start.year + (month_after - 1) // 12,
        ((month_after - 1) % 12) + 1,
        1,
    )
    if not (period_start <= filing_date < quarter_end):
        raise ValueError("FILING_DATE_OUTSIDE_ARCHIVE_QUARTER")

    url = accession_header_url(expected_cik, accession)
    acceptance_datetime = parse_acceptance_header(
        text, expected_cik, accession, form, filing_date.isoformat()
    )
    return {
        "accession": accession,
        "filer_cik": expected_cik,
        "filing_date": filing_date.isoformat(),
        "period": report_period.strftime("%d-%b-%Y").upper(),
        "submission_type": form,
        "acceptance_datetime": acceptance_datetime,
        "acceptance_timezone": "America/New_York",
        "acceptance_clock_basis": "SEC_EDGAR_SGML_ACCEPTANCE_DATETIME",
        "source_url": url,
        "header_sha256": hashlib.sha256(body).hexdigest(),
        "header_bytes": len(body),
    }


def fetch_failed_header(
    accession: str,
    archive: dict[str, Any],
    limiter: RateLimiter,
) -> tuple[str, dict[str, Any]]:
    url = accession_header_url(accession.split("-", 1)[0], accession)
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        limiter.wait()
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": RECOVERY_UA,
                    "Accept": "text/html,text/plain,*/*",
                    "Accept-Encoding": "identity",
                    "Connection": "close",
                },
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                status = int(getattr(response, "status", 200))
                body = response.read()
            if status != 200:
                raise RuntimeError("SEC_HEADER_HTTP_" + str(status))
            return accession, _parse_header_fields(body, accession, archive)
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in RETRYABLE_HTTP or attempt + 1 >= MAX_ATTEMPTS:
                break
            retry_after = 0
            try:
                retry_after = int((exc.headers or {}).get("Retry-After", "0"))
            except (TypeError, ValueError):
                pass
            time.sleep(max(retry_after, min(MAX_RETRY_DELAY_SECONDS, 3 * (2 ** attempt))))
        except (urllib.error.URLError, TimeoutError, OSError, RuntimeError, ValueError) as exc:
            last_error = exc
            if attempt + 1 >= MAX_ATTEMPTS:
                break
            time.sleep(min(MAX_RETRY_DELAY_SECONDS, 3 * (2 ** attempt)))
    raise RuntimeError(f"TARGETED_HEADER_RETRY_FAILED:{accession}:{last_error}")


def collect_failed_accessions(payloads: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if len(payloads) != len(EXPECTED_SHARDS):
        raise ValueError("Q104_I19_RECOVERY_REQUIRES_ALL_SIX_SHARDS")
    by_shard: set[str] = set()
    failures: dict[str, dict[str, Any]] = {}
    for payload in payloads:
        shard = str(payload.get("shard", ""))
        if shard not in EXPECTED_SHARDS or shard in by_shard:
            raise ValueError("Q104_I19_RECOVERY_SHARD_IDENTITY_INVALID:" + shard)
        by_shard.add(shard)
        if payload.get("candidate_id") != "Q104:I19":
            raise ValueError("Q104_I19_RECOVERY_CANDIDATE_MISMATCH:" + shard)
        if payload.get("archive_completeness_for_shard") is not True:
            raise ValueError("Q104_I19_RECOVERY_ARCHIVE_INCOMPLETE:" + shard)
        for archive_record in payload.get("archives", []):
            archive = archive_record.get("archive", {})
            shard_failures = archive_record.get("acceptance_failures", {})
            for accession, reason in shard_failures.items():
                if accession in failures:
                    raise ValueError("Q104_I19_RECOVERY_DUPLICATE_ACCESSION:" + accession)
                eligible_symbols = [
                    symbol for symbol, hit in archive_record.get("target_hits", {}).items()
                    if accession in set(hit.get("accessions", []))
                ]
                if not eligible_symbols:
                    raise ValueError("Q104_I19_RECOVERY_ORPHAN_FAILURE:" + accession)
                if accession in set(archive_record.get("target_hits", {}).get(
                    next(iter(eligible_symbols)), {}
                ).get("acceptance_records", {})):
                    raise ValueError("Q104_I19_RECOVERY_ACCESSION_ALREADY_HAS_RECORD:" + accession)
                failures[accession] = {
                    "original_error": str(reason),
                    "shard": shard,
                    "archive_url": str(archive.get("url", "")),
                    "archive_sha256": str(archive_record.get("archive_sha256", "")),
                    "archive_period_start": str(archive.get("period_start", "")),
                    "target_symbols": eligible_symbols,
                }
    if by_shard != EXPECTED_SHARDS:
        raise ValueError("Q104_I19_RECOVERY_MISSING_SHARDS")
    return failures


def apply_recovered_records(
    payloads: list[dict[str, Any]],
    recovered: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for original in payloads:
        payload = json.loads(json.dumps(original))
        for archive_record in payload.get("archives", []):
            archive_failures = archive_record.setdefault("acceptance_failures", {})
            for accession, record in recovered.items():
                meta = None
                for item in archive_record.get("target_hits", {}).values():
                    if accession in set(item.get("accessions", [])):
                        meta = record
                        existing = item.setdefault("acceptance_records", {})
                        if accession in existing and existing[accession] != record:
                            raise ValueError("Q104_I19_RECOVERY_RECORD_CONFLICT:" + accession)
                        existing[accession] = record
                if meta is not None:
                    archive_failures.pop(accession, None)
            for hit in archive_record.get("target_hits", {}).values():
                accessions = set(str(x) for x in hit.get("accessions", []))
                records = hit.setdefault("acceptance_records", {})
                hit["acceptance_complete"] = (
                    accessions == set(records)
                    and not any(accession in archive_failures for accession in accessions)
                )
            target_accessions = {
                str(accession)
                for hit in archive_record.get("target_hits", {}).values()
                for accession in hit.get("accessions", [])
            }
            archive_record["target_unique_accession_count"] = len(target_accessions)
            archive_record["acceptance_record_count"] = len({
                accession
                for hit in archive_record.get("target_hits", {}).values()
                for accession in hit.get("acceptance_records", {})
            })
        payload["acceptance_failures"] = {
            accession: reason
            for archive_record in payload.get("archives", [])
            for accession, reason in archive_record.get("acceptance_failures", {}).items()
        }
        payload["acceptance_time_join"] = {
            "target_unique_accessions": sum(
                int(archive_record.get("target_unique_accession_count", 0))
                for archive_record in payload.get("archives", [])
            ),
            "records_checked": sum(
                int(archive_record.get("acceptance_record_count", 0))
                for archive_record in payload.get("archives", [])
            ),
            "failures": len(payload["acceptance_failures"]),
            "complete": not payload["acceptance_failures"] and all(
                hit.get("acceptance_complete") is True
                for archive_record in payload.get("archives", [])
                for hit in archive_record.get("target_hits", {}).values()
            ),
            "timezone_inference": False,
        }
        payload.pop("receipt_fingerprint", None)
        payload["receipt_fingerprint"] = _fingerprint(payload)
        outputs.append(payload)
    return outputs


def run_recovery(
    input_dir: Path,
    output_dir: Path,
    report_path: Path,
    source_run_id: str | None = None,
    source_run_sha: str | None = None,
) -> dict[str, Any]:
    input_paths = sorted(input_dir.rglob("shard_receipt.json"))
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in input_paths]
    failed = collect_failed_accessions(payloads)
    initial_errors = Counter(item["original_error"] for item in failed.values())
    results: dict[str, dict[str, Any]] = {}
    remaining: dict[str, str] = {}
    if failed:
        # Two workers share one limiter; after the six-shard run ends this keeps
        # retries deliberately slower than the original parallel census.
        limiter = RateLimiter(max(1.1, HEADER_REQUEST_GAP_SECONDS))
        archive_by_accession = {
            accession: {
                "period_start": detail["archive_period_start"],
                "url": detail["archive_url"],
            }
            for accession, detail in failed.items()
        }
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(fetch_failed_header, accession, archive, limiter): accession
                for accession, archive in archive_by_accession.items()
            }
            completed = 0
            for future in as_completed(futures):
                accession = futures[future]
                completed += 1
                try:
                    key, record = future.result()
                    results[key] = record
                except Exception as exc:  # unresolved items stay fail-closed
                    remaining[accession] = str(exc)
                if completed % 50 == 0 or completed == len(failed):
                    print(json.dumps({
                        "phase": "targeted_acceptance_recovery",
                        "completed": completed,
                        "total": len(failed),
                        "recovered": len(results),
                        "remaining": len(remaining),
                    }, sort_keys=True), flush=True)

    patched = apply_recovered_records(payloads, results)
    # Emit exactly one receipt per frozen shard under a path the existing merger accepts.
    output_dir.mkdir(parents=True, exist_ok=True)
    for payload in patched:
        shard = str(payload["shard"])
        target = output_dir / shard / "shard_receipt.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    remaining_by_original_error = Counter(
        failed[accession]["original_error"] for accession in remaining
    )
    report = {
        "schema_version": "1.0",
        "record_type": "q104_i19_targeted_acceptance_recovery",
        "candidate_id": "Q104:I19",
        "status": (
            "NO_ACCEPTANCE_RETRIES_NEEDED"
            if not failed else
            "TARGETED_ACCEPTANCE_RECOVERY_COMPLETE"
            if not remaining else
            "TARGETED_ACCEPTANCE_RECOVERY_PARTIAL"
        ),
        "source_census_run_id": str(source_run_id or ""),
        "source_census_head_sha": str(source_run_sha or ""),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "recovery_method": "Only accession headers present in immutable shard acceptance_failures were re-requested; no full holdings scan was run.",
        "frozen_archive_scans_reused": True,
        "archive_redownloads": 0,
        "initial_failed_accessions": len(failed),
        "initial_failures_by_reason": dict(sorted(initial_errors.items())),
        "recovered_accessions": len(results),
        "unresolved_accessions": len(remaining),
        "unresolved_by_original_reason": dict(sorted(remaining_by_original_error.items())),
        "unresolved_details": [
            {
                "accession": accession,
                "original_error": failed[accession]["original_error"],
                "retry_error": remaining[accession],
                "shard": failed[accession]["shard"],
                "archive_url": failed[accession]["archive_url"],
            }
            for accession in sorted(remaining)
        ],
        "recovered_header_fingerprints": {
            accession: {
                "header_sha256": record["header_sha256"],
                "acceptance_datetime": record["acceptance_datetime"],
                "source_url": record["source_url"],
                "shard": failed[accession]["shard"],
            }
            for accession, record in sorted(results.items())
        },
        "recovered_shard_fingerprints": {
            str(payload["shard"]): str(payload["receipt_fingerprint"])
            for payload in patched
        },
        "merge_ready": len(remaining) == 0,
        "performance_authorized": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "initial_failed_accessions": report["initial_failed_accessions"],
        "recovered_accessions": report["recovered_accessions"],
        "unresolved_accessions": report["unresolved_accessions"],
        "merge_ready": report["merge_ready"],
    }, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--source-run-id", default="")
    parser.add_argument("--source-run-sha", default="")
    args = parser.parse_args()
    try:
        run_recovery(
            args.input_dir,
            args.output_dir,
            args.report,
            args.source_run_id,
            args.source_run_sha,
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
