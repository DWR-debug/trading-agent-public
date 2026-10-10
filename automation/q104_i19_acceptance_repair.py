"""Targeted Q104:I19 acceptance-header recovery; never rescans successful shards."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

from automation import q104_i19_13f_historical_identity_census as census
from automation.q104_i19_13f_historical_identity_census_merge import (
    EXPECTED_SHARDS,
    canonical_fingerprint,
)

TRANSIENT_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}
MAX_HEADER_RETRIES = 3
RETRYABLE_REASON = re.compile(
    r"(SEC_HEADER_HTTP_(408|425|429|500|502|503|504)|"
    r"timeout|timed out|urlerror|connection reset|connection aborted|"
    r"remote disconnected|temporary failure|network is unreachable)",
    re.IGNORECASE,
)


def is_transient_failure(reason: str) -> bool:
    """Retry only network/temporary server failures, never identity mismatches."""
    return bool(RETRYABLE_REASON.search(str(reason or "")))


def is_repairable_failure(reason: str) -> bool:
    """Repair retryable transport failures and known-missing legacy header routes.

    SEC documents that pre-2015 submissions may lack the HTML index-header endpoint;
    those accessions require the same filing's .hdr.sgml source instead.
    """
    value = str(reason or "").strip()
    return (
        is_transient_failure(value)
        or value == "SEC_HEADER_HTTP_404"
        or value in {
            "MISSING_ACCEPTANCE_DATETIME",
            "HEADER_VALIDATION:MISSING_ACCEPTANCE_DATETIME",
        }
    )


def accession_hdr_sgml_url(cik: str, accession: str) -> str:
    """Canonical SEC archive URL for the raw SGML header, including accession dashes."""
    cik10 = str(cik).strip().zfill(10)
    acc = str(accession).strip()
    if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", acc):
        raise ValueError("SEC_ACCESSION_UNPARSEABLE:" + acc)
    normalized = acc.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik10)}/"
        f"{normalized}/{acc}.hdr.sgml"
    )


def _failure_description(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"SEC_HEADER_HTTP_{exc.code}"
    if isinstance(exc, TimeoutError):
        return "TimeoutError:" + str(exc)
    if isinstance(exc, urllib.error.URLError):
        return "URLError:" + str(exc.reason)
    return f"{type(exc).__name__}:{exc}"


def resolve_accession_header(
    accession: str,
    meta: dict[str, str],
    rate_limiter: Any,
    *,
    retries: int = MAX_HEADER_RETRIES,
    urlopen: Callable[..., Any] | None = None,
    sleep: Callable[[float], None] | None = None,
    prefer_sgml: bool = False,
) -> tuple[dict[str, Any] | None, str | None, int]:
    """Resolve exact SEC acceptance time; use archived .hdr.sgml when the HTML header route is absent."""
    if retries < 1:
        raise ValueError("Q104_I19_REPAIR_RETRIES_MUST_BE_POSITIVE")
    opener = urlopen or urllib.request.urlopen
    sleeper = sleep or time.sleep
    index_url = census.accession_header_url(meta.get("filer_cik", ""), accession)
    sgml_url = accession_hdr_sgml_url(meta.get("filer_cik", ""), accession)
    routes = (
        [("sec_hdr_sgml_fallback", sgml_url)]
        if prefer_sgml
        else [("sec_index_headers", index_url), ("sec_hdr_sgml_fallback", sgml_url)]
    )
    attempts_total = 0
    last_error = "Q104_I19_REPAIR_NO_ATTEMPT"

    for source_type, url in routes:
        missing_route = False
        for attempt in range(1, retries + 1):
            rate_limiter.wait()
            attempts_total += 1
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": census.UA,
                    "Accept": "text/html,text/plain,*/*",
                    "Accept-Encoding": "identity",
                    "Connection": "close",
                },
            )
            try:
                with opener(req, timeout=45) as response:
                    body = response.read()
                    status = int(getattr(response, "status", 200))
            except urllib.error.HTTPError as exc:
                last_error = _failure_description(exc)
                if exc.code == 404 and source_type == "sec_index_headers":
                    missing_route = True
                    break
                if exc.code == 404 and source_type == "sec_hdr_sgml_fallback":
                    return None, "SEC_HEADER_FALLBACK_HTTP_404", attempts_total
                if exc.code not in TRANSIENT_HTTP_CODES or attempt == retries:
                    return None, last_error, attempts_total
                try:
                    retry_after = float((exc.headers or {}).get("Retry-After", "0"))
                except (AttributeError, TypeError, ValueError):
                    retry_after = 0.0
                sleeper(max(1.0, min(15.0, retry_after or float(2 ** attempt))))
                continue
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = _failure_description(exc)
                if attempt == retries:
                    return None, last_error, attempts_total
                sleeper(min(15.0, float(2 ** attempt)))
                continue

            if status != 200:
                last_error = f"SEC_HEADER_HTTP_{status}"
                if status == 404 and source_type == "sec_index_headers":
                    missing_route = True
                    break
                if status == 404 and source_type == "sec_hdr_sgml_fallback":
                    return None, "SEC_HEADER_FALLBACK_HTTP_404", attempts_total
                if status not in TRANSIENT_HTTP_CODES or attempt == retries:
                    return None, last_error, attempts_total
                sleeper(min(15.0, float(2 ** attempt)))
                continue

            try:
                accepted = census.parse_acceptance_header(
                    body.decode("utf-8", "replace"),
                    meta["filer_cik"],
                    accession,
                    meta["submission_type"],
                    meta["filing_date"],
                )
            except (ValueError, KeyError) as exc:
                validation_error = str(exc)
                if (
                    source_type == "sec_index_headers"
                    and validation_error == "MISSING_ACCEPTANCE_DATETIME"
                ):
                    last_error = "HEADER_VALIDATION:" + validation_error
                    missing_route = True
                    break
                # Identity, form, accession and filing-date mismatches never fall
                # back to a second source: contradictory identity is a hard stop.
                return None, "HEADER_VALIDATION:" + validation_error, attempts_total

            record = {
                "accession": accession,
                "filer_cik": str(meta["filer_cik"]).zfill(10),
                "filing_date": meta["filing_date"],
                "period": meta.get("period"),
                "submission_type": meta["submission_type"],
                "acceptance_datetime": accepted,
                "acceptance_timezone": "America/New_York",
                "acceptance_clock_basis": "SEC_EDGAR_SGML_ACCEPTANCE_DATETIME",
                "source_url": url,
                "header_source_type": source_type,
                "header_sha256": hashlib.sha256(body).hexdigest(),
                "header_bytes": len(body),
            }
            return record, None, attempts_total

        if missing_route:
            if source_type == "sec_index_headers":
                continue
            break
        # A transient failure that exhausts its bounded retries is final. Do not
        # silently switch source route after a live server/network failure.
        return None, last_error, attempts_total

    if last_error == "SEC_HEADER_HTTP_404":
        last_error = "SEC_HEADER_FALLBACK_HTTP_404"
    return None, last_error, attempts_total


def _archive_accession_metadata(
    blob: bytes,
    pending: set[str],
    archive_record: dict[str, Any],
) -> dict[str, dict[str, str]]:
    """Recover expected CIK/form/date from the exact archived submission.tsv vintage."""
    found: dict[str, dict[str, str]] = {}
    expected_dates = {
        str(value)
        for hit in archive_record.get("target_hits", {}).values()
        for value in hit.get("filing_dates", [])
    }
    expected_periods = {
        str(value)
        for hit in archive_record.get("target_hits", {}).values()
        for value in hit.get("periods", [])
    }
    with zipfile.ZipFile(BytesIO(blob)) as zf:
        for row in census.tsv(zf, "submission.tsv"):
            accession = census.field(row, "ACCESSION_NUMBER")
            if accession not in pending:
                continue
            raw_filing_date = census.field(row, "FILING_DATE")
            cik = census.field(row, "CIK")
            form = census.field(row, "SUBMISSIONTYPE")
            period = census.field(row, "PERIODOFREPORT")
            if not raw_filing_date or not cik or not form:
                continue
            filing_date = census.parse_date(raw_filing_date).isoformat()
            cik = str(cik).strip().zfill(10)
            if accession.split("-", 1)[0] != cik:
                raise ValueError("Q104_I19_REPAIR_ARCHIVE_CIK_MISMATCH:" + accession)
            if filing_date not in expected_dates:
                raise ValueError("Q104_I19_REPAIR_FILING_DATE_NOT_IN_FROZEN_TARGET_HITS:" + accession)
            if period and expected_periods and period not in expected_periods:
                raise ValueError("Q104_I19_REPAIR_PERIOD_NOT_IN_FROZEN_TARGET_HITS:" + accession)
            found[accession] = {
                "filing_date": filing_date,
                "period": period,
                "filer_cik": cik,
                "submission_type": form,
            }
    return found


def repair_shard_payload(
    payload: dict[str, Any],
    *,
    rate_limiter: Any | None = None,
    archive_fetcher: Callable[[str, Any], bytes] | None = None,
    header_resolver: Callable[..., tuple[dict[str, Any] | None, str | None, int]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Repair only failed acceptance headers, retaining all frozen archive identities."""
    original_fingerprint = payload.get("receipt_fingerprint")
    if original_fingerprint != canonical_fingerprint(payload):
        raise ValueError("Q104_I19_REPAIR_INPUT_FINGERPRINT_INVALID:" + str(payload.get("shard")))
    receipt = json.loads(json.dumps(payload))
    expected_failures = set(str(x) for x in receipt.get("acceptance_failures", {}))
    archive_failure_keys = {
        str(accession)
        for archive_record in receipt.get("archives", [])
        for accession in archive_record.get("acceptance_failures", {})
    }
    if expected_failures != archive_failure_keys:
        raise ValueError("Q104_I19_REPAIR_TOP_LEVEL_FAILURE_SET_MISMATCH:" + str(receipt.get("shard")))
    limiter = rate_limiter or census.RateLimiter(census.HEADER_REQUEST_GAP_SECONDS)
    fetcher = archive_fetcher or (lambda url, limiter: census.fetch(url, rate_limiter=limiter))
    resolver = header_resolver or (
        lambda accession, meta, rate_limiter: resolve_accession_header(
            accession, meta, rate_limiter
        )
    )
    entries: list[dict[str, Any]] = []

    for archive_record in receipt.get("archives", []):
        failures = dict(archive_record.get("acceptance_failures", {}))
        if not failures:
            continue
        all_accessions = {
            str(accession)
            for hit in archive_record.get("target_hits", {}).values()
            for accession in hit.get("accessions", [])
        }
        if not set(failures).issubset(all_accessions):
            raise ValueError("Q104_I19_REPAIR_FAILURE_SET_NOT_IN_ARCHIVE_TARGETS:" + str(archive_record.get("archive", {}).get("url", "")))

        retryable = {accession for accession, reason in failures.items() if is_repairable_failure(reason)}
        if not retryable:
            for accession, reason in failures.items():
                entries.append({
                    "shard": receipt.get("shard"),
                    "accession": accession,
                    "source_archive": archive_record.get("archive", {}).get("url"),
                    "original_failure": reason,
                    "attempts": 0,
                    "status": "NOT_RETRIED_NONTRANSIENT",
                    "final_error": reason,
                })
            continue

        archive_meta = archive_record.get("archive", {})
        archive_url = str(archive_meta.get("url", ""))
        if not archive_url.startswith("https://www.sec.gov/"):
            raise ValueError("Q104_I19_REPAIR_INVALID_ARCHIVE_URL:" + archive_url)
        blob = fetcher(archive_url, limiter)
        actual_archive_hash = hashlib.sha256(blob).hexdigest()
        if actual_archive_hash != archive_record.get("archive_sha256"):
            raise ValueError("Q104_I19_REPAIR_ARCHIVE_HASH_MISMATCH:" + archive_url)

        metadata = _archive_accession_metadata(blob, retryable, archive_record)
        existing_records: dict[str, dict[str, Any]] = {}
        for hit in archive_record.get("target_hits", {}).values():
            for accession, record in hit.get("acceptance_records", {}).items():
                if accession in existing_records and existing_records[accession] != record:
                    raise ValueError("Q104_I19_REPAIR_EXISTING_RECORD_CONFLICT:" + accession)
                existing_records[str(accession)] = record

        for accession in sorted(retryable):
            original_error = str(failures[accession])
            meta = metadata.get(accession)
            if meta is None:
                failures[accession] = "Q104_I19_REPAIR_ACCESSION_METADATA_NOT_FOUND"
                entries.append({
                    "shard": receipt.get("shard"),
                    "accession": accession,
                    "source_archive": archive_url,
                    "original_failure": original_error,
                    "attempts": 0,
                    "status": "UNRESOLVED",
                    "final_error": failures[accession],
                })
                continue

            if header_resolver is None:
                prefer_sgml = (
                    original_error == "SEC_HEADER_HTTP_404"
                    or original_error in {
                        "MISSING_ACCEPTANCE_DATETIME",
                        "HEADER_VALIDATION:MISSING_ACCEPTANCE_DATETIME",
                    }
                )
                record, error, attempts = resolve_accession_header(
                    accession, meta, limiter, prefer_sgml=prefer_sgml
                )
            else:
                record, error, attempts = resolver(accession, meta, limiter)
            if record is not None:
                existing_records[accession] = record
                failures.pop(accession, None)
                entries.append({
                    "shard": receipt.get("shard"),
                    "accession": accession,
                    "source_archive": archive_url,
                    "source_archive_sha256": archive_record.get("archive_sha256"),
                    "original_failure": original_error,
                    "attempts": attempts,
                    "status": "REPAIRED",
                    "acceptance_datetime": record["acceptance_datetime"],
                    "header_sha256": record["header_sha256"],
                })
            else:
                final_error = str(error or "Q104_I19_REPAIR_HEADER_UNRESOLVED")
                failures[accession] = final_error
                entries.append({
                    "shard": receipt.get("shard"),
                    "accession": accession,
                    "source_archive": archive_url,
                    "source_archive_sha256": archive_record.get("archive_sha256"),
                    "original_failure": original_error,
                    "attempts": attempts,
                    "status": "UNRESOLVED",
                    "final_error": final_error,
                })

        archive_record["acceptance_failures"] = failures
        for hit in archive_record.get("target_hits", {}).values():
            accessions = {str(x) for x in hit.get("accessions", [])}
            hit["acceptance_records"] = {
                accession: existing_records[accession]
                for accession in sorted(accessions)
                if accession in existing_records
            }
            hit["acceptance_complete"] = (
                set(hit["acceptance_records"]) == accessions
                and not (accessions & set(failures))
            )
        archive_accessions = {
            str(accession)
            for hit in archive_record.get("target_hits", {}).values()
            for accession in hit.get("accessions", [])
        }
        archive_record["acceptance_record_count"] = len(existing_records)
        archive_record["target_unique_accession_count"] = len(archive_accessions)

    receipt["acceptance_failures"] = {
        accession: reason
        for archive_record in receipt.get("archives", [])
        for accession, reason in archive_record.get("acceptance_failures", {}).items()
    }
    records_checked = sum(int(x.get("acceptance_record_count", 0)) for x in receipt.get("archives", []))
    target_count = sum(int(x.get("target_unique_accession_count", 0)) for x in receipt.get("archives", []))
    receipt["acceptance_time_join"] = {
        "records_checked": records_checked,
        "target_unique_accessions": target_count,
        "failures": len(receipt["acceptance_failures"]),
        "complete": target_count == records_checked and not receipt["acceptance_failures"],
        "timezone_inference": False,
    }
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    return receipt, entries


def _locate(root: Path, filename: str) -> Path:
    matches = sorted(root.rglob(filename))
    if len(matches) != 1:
        raise ValueError(f"Q104_I19_REPAIR_EXPECTED_ONE_{filename.upper()}_FOUND_{len(matches)}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--source-snapshot-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--shard-recovery-run-id", required=True)
    args = parser.parse_args()

    try:
        snapshot_receipt_path = _locate(args.source_snapshot_dir, "source_page_receipt.json")
        snapshot_html_path = _locate(args.source_snapshot_dir, "source_page.html")
        snapshot_receipt = json.loads(snapshot_receipt_path.read_text(encoding="utf-8"))
        source_page_hash = hashlib.sha256(snapshot_html_path.read_bytes()).hexdigest()
        if snapshot_receipt.get("source_page_sha256") != source_page_hash:
            raise ValueError("Q104_I19_REPAIR_SOURCE_SNAPSHOT_HASH_MISMATCH")

        shard_paths = sorted(args.input_dir.rglob("shard_receipt.json"))
        payloads = [json.loads(path.read_text(encoding="utf-8")) for path in shard_paths]
        shards = [str(payload.get("shard", "")) for payload in payloads]
        if len(payloads) != len(EXPECTED_SHARDS) or set(shards) != EXPECTED_SHARDS or len(shards) != len(set(shards)):
            raise ValueError("Q104_I19_REPAIR_MISSING_OR_DUPLICATE_SHARD_ARTIFACTS")
        if any(payload.get("source_page_sha256") != source_page_hash for payload in payloads):
            raise ValueError("Q104_I19_REPAIR_SOURCE_PAGE_LINEAGE_MISMATCH")

        args.output_dir.mkdir(parents=True, exist_ok=True)
        all_entries: list[dict[str, Any]] = []
        original_fingerprints: dict[str, str] = {}
        repaired_fingerprints: dict[str, str] = {}
        for payload in sorted(payloads, key=lambda item: str(item["shard"])):
            shard = str(payload["shard"])
            original_fingerprints[shard] = str(payload["receipt_fingerprint"])
            fixed, entries = repair_shard_payload(payload)
            repaired_fingerprints[shard] = str(fixed["receipt_fingerprint"])
            all_entries.extend(entries)
            target = args.output_dir / shard / "shard_receipt.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(fixed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        recovery = {
            "schema_version": "1.0",
            "record_type": "q104_i19_targeted_acceptance_header_recovery",
            "status": "RECOVERY_COMPLETE" if all(x.get("status") == "REPAIRED" for x in all_entries) else ("RECOVERY_COMPLETE" if not all_entries else "RECOVERY_INCOMPLETE"),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_run_id": str(args.source_run_id),
            "shard_recovery_run_id": str(args.shard_recovery_run_id),
            "official_source": census.PAGE,
            "source_page_sha256": source_page_hash,
            "original_shard_receipt_fingerprints": original_fingerprints,
            "repaired_shard_receipt_fingerprints": repaired_fingerprints,
            "failed_accession_set": sorted(
                str(x["accession"]) for x in all_entries if x.get("original_failure")
            ),
            "repaired_accession_set": sorted(
                str(x["accession"]) for x in all_entries if x.get("status") == "REPAIRED"
            ),
            "unresolved_accession_set": sorted(
                str(x["accession"]) for x in all_entries if x.get("status") in {"UNRESOLVED", "NOT_RETRIED_NONTRANSIENT"}
            ),
            "attempts": all_entries,
            "summary": {
                "shards": len(payloads),
                "original_failed_accessions": sum(1 for x in all_entries if x.get("original_failure")),
                "repaired": sum(1 for x in all_entries if x.get("status") == "REPAIRED"),
                "unresolved": sum(1 for x in all_entries if x.get("status") in {"UNRESOLVED", "NOT_RETRIED_NONTRANSIENT"}),
                "retry_attempts_total": sum(int(x.get("attempts", 0)) for x in all_entries),
            },
            "scientific_boundary": {
                "performance_authorized": False,
                "holdout_selection_allowed": False,
                "ranking_allowed": False,
                "parameter_search_allowed": False,
                "threshold_search_allowed": False,
                "horizon_search_allowed": False,
                "promotion_allowed": False,
                "live_execution_allowed": False,
            },
            "safety": {
                "paper_only": True,
                "live_trading_enabled": False,
                "orders_enabled": False,
                "automatic_promotion": False,
            },
        }
        args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_output.write_text(json.dumps(recovery, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": recovery["status"], **recovery["summary"]}, sort_keys=True))
        return 0 if recovery["status"] == "RECOVERY_COMPLETE" else 2
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, zipfile.BadZipFile) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
