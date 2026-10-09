"""Repair only the frozen Q104:I19 SEC acceptance-header failures from one census run.

This does not download or rescan any 13F archive. It retries only the accession headers
listed in two immutable, fingerprint-pinned shard receipts. Other shards must already
be complete and clock-clean or this script stops without sending SEC requests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation.q104_i19_13f_historical_identity_census import (
    HEADER_REQUEST_GAP_SECONDS,
    UA,
    RateLimiter,
    accession_header_url,
    parse_acceptance_header,
)

EXPECTED_RUN_ID = 37931811984
EXPECTED_SHARDS = {"2013-2016", "2017-2018", "2019-2020", "2021-2022", "2023", "2024-2025-09"}
EXPECTED_SOURCE_HASH = "6a112b137e853ec63a8939e60c1e3c92ffce4046fb079cc417b18a8c934ffbd3"
RETRYABLE_FAILURES = {"SEC_HEADER_HTTP_503", "The read operation timed out"}
MAX_ATTEMPTS = 4
REQUEST_GAP_SECONDS = 1.5
TIMEOUT_SECONDS = 45
RETRYABLE_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}
EXPECTED_RECOVERY_INPUTS = {
    "2023": {
        "receipt_fingerprint": "57d5ea86765db5cd580103a351cd66820775d0c6e33fab4185af7c9bc010c130",
        "failures": 268,
        "checked": 14234,
        "targets": 14502,
    },
    "2021-2022": {
        "receipt_fingerprint": "4efa0d3c191abe46b3f8be56edcc15da9d5d7910cf59fdde74fad5edafe1645b",
        "failures": 437,
        "checked": 25408,
        "targets": 25845,
    },
}
EXPECTED_SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def fingerprint(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("receipt_fingerprint", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def seal(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    payload.pop("receipt_fingerprint", None)
    payload["receipt_fingerprint"] = fingerprint(payload)
    return payload


def one_header_value(text: str, pattern: str, label: str) -> str:
    match = re.search(pattern, text, re.I | re.M)
    if not match:
        raise ValueError(label + "_MISSING")
    return match.group(1).strip()


def record_from_header(body: bytes, accession: str) -> dict[str, Any]:
    """Build one provenance-bearing receipt from a single official SEC header response."""
    text = body.decode("utf-8", "replace")
    cik = accession[:10]
    header_accession = one_header_value(
        text, r"^ACCESSION NUMBER:\s*([0-9]{10}-[0-9]{2}-[0-9]{6})", "ACCESSION"
    )
    header_cik = one_header_value(text, r"^CENTRAL INDEX KEY:\s*([0-9]{10})", "CIK")
    form = one_header_value(text, r"^CONFORMED SUBMISSION TYPE:\s*([^\s<]+)", "FORM")
    filed_raw = one_header_value(text, r"^FILED AS OF DATE:\s*([0-9]{8})", "FILED_DATE")
    period_raw = one_header_value(text, r"^CONFORMED PERIOD OF REPORT:\s*([0-9]{8}|[0-9]{2}-[A-Z]{3}-[0-9]{4})", "PERIOD")

    if header_accession != accession:
        raise ValueError("ACCESSION_MISMATCH")
    if header_cik != cik:
        raise ValueError("FILER_CIK_MISMATCH")
    filing_date = f"{filed_raw[:4]}-{filed_raw[4:6]}-{filed_raw[6:8]}"
    filed_dt = datetime.strptime(filing_date, "%Y-%m-%d").date()
    if accession[11:13] != filed_raw[2:4]:
        raise ValueError("ACCESSION_YEAR_FILED_DATE_MISMATCH")
    if re.fullmatch(r"\d{8}", period_raw):
        period_dt = datetime.strptime(period_raw, "%Y%m%d").date()
        period = period_dt.strftime("%d-%b-%Y").upper()
    else:
        period = period_raw.upper()
        datetime.strptime(period, "%d-%b-%Y")
    acceptance = parse_acceptance_header(text, cik, accession, form, filing_date)
    if filed_dt.year < 1993 or filed_dt.year > datetime.now(timezone.utc).year:
        raise ValueError("FILED_DATE_OUT_OF_RANGE")
    url = accession_header_url(cik, accession)
    return {
        "accession": accession,
        "filer_cik": cik,
        "filing_date": filing_date,
        "period": period,
        "submission_type": form,
        "acceptance_datetime": acceptance,
        "acceptance_timezone": "America/New_York",
        "acceptance_clock_basis": "SEC_EDGAR_SGML_ACCEPTANCE_DATETIME",
        "source_url": url,
        "header_sha256": hashlib.sha256(body).hexdigest(),
        "header_bytes": len(body),
    }


def fetch_one(accession: str, limiter: RateLimiter) -> tuple[dict[str, Any] | None, str | None, int]:
    cik = accession[:10]
    url = accession_header_url(cik, accession)
    last_error = "UNKNOWN"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        limiter.wait()
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA + " targeted acceptance-clock recovery",
                "Accept": "text/html,text/plain,*/*",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                if int(getattr(response, "status", 200)) != 200:
                    raise RuntimeError("SEC_HEADER_HTTP_" + str(response.status))
                body = response.read()
            try:
                return record_from_header(body, accession), None, attempt
            except (ValueError, UnicodeError) as exc:
                # A retrieved but inconsistent header is evidence of a data problem;
                # it is not silently accepted as a transient fetch failure.
                return None, "HEADER_VALIDATION:" + str(exc), attempt
        except urllib.error.HTTPError as exc:
            last_error = "SEC_HEADER_HTTP_" + str(exc.code)
            if exc.code not in RETRYABLE_HTTP_CODES or attempt == MAX_ATTEMPTS:
                return None, last_error, attempt
            try:
                retry_after = int((exc.headers or {}).get("Retry-After", "0"))
            except (AttributeError, TypeError, ValueError):
                retry_after = 0
            time.sleep(max(retry_after, min(20, 2 ** attempt)))
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            last_error = "The read operation timed out" if isinstance(exc, (TimeoutError, socket.timeout)) else "URL_OR_OS_ERROR:" + type(exc).__name__
            if attempt == MAX_ATTEMPTS:
                return None, last_error, attempt
            time.sleep(min(20, 2 ** attempt))
    return None, last_error, MAX_ATTEMPTS


def load_receipts(input_dir: Path) -> dict[str, tuple[Path, dict[str, Any]]]:
    found: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in input_dir.rglob("shard_receipt.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        shard = str(payload.get("shard", ""))
        if shard in found:
            raise ValueError("DUPLICATE_SHARD_ARTIFACT:" + shard)
        found[shard] = (path, payload)
    if set(found) != EXPECTED_SHARDS:
        raise ValueError("WAIT_FOR_ALL_SIX_SHARDS: found=" + ",".join(sorted(found)))
    return found


def validate_shard_base(payload: dict[str, Any], shard: str) -> None:
    if payload.get("shard") != shard or payload.get("candidate_id") != "Q104:I19":
        raise ValueError("SHARD_IDENTITY_MISMATCH:" + shard)
    if payload.get("status") != "13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_SOURCE_ONLY":
        raise ValueError("SHARD_STATUS_UNEXPECTED:" + shard)
    if payload.get("source_page_sha256") != EXPECTED_SOURCE_HASH:
        raise ValueError("SOURCE_PAGE_FINGERPRINT_MISMATCH:" + shard)
    if fingerprint(payload) != payload.get("receipt_fingerprint"):
        raise ValueError("INPUT_RECEIPT_FINGERPRINT_INVALID:" + shard)
    if payload.get("safety") != EXPECTED_SAFETY:
        raise ValueError("SAFETY_BOUNDARY_INVALID:" + shard)
    if payload.get("identity_conflicts"):
        raise ValueError("IDENTITY_CONFLICTS_PRESENT:" + shard)
    if payload.get("archive_completeness_for_shard") is not True:
        raise ValueError("ARCHIVE_COMPLETENESS_FAILED:" + shard)
    if not payload.get("synthetic") or any(value is not True for value in payload["synthetic"].values()):
        raise ValueError("SYNTHETIC_GATE_FAILED:" + shard)
    if not payload.get("archives") or int(payload.get("selected_archive_count", -1)) != len(payload["archives"]):
        raise ValueError("ARCHIVE_SET_INVALID:" + shard)
    targets = set()
    for archive in payload["archives"]:
        hits = archive.get("target_hits", {})
        for symbol, hit in hits.items():
            accessions = set(str(x) for x in hit.get("accessions", []))
            targets.update(accessions)
            records = hit.get("acceptance_records", {})
            if not set(records).issubset(accessions):
                raise ValueError("ACCEPTANCE_RECORD_NOT_IN_TARGET_SET:" + shard + ":" + symbol)
            if any(record.get("accession") != acc for acc, record in records.items()):
                raise ValueError("ACCEPTANCE_ACCESSION_MISMATCH:" + shard + ":" + symbol)
    if not targets:
        raise ValueError("EMPTY_TARGET_ACCESSION_SET:" + shard)


def validate_scope(receipts: dict[str, tuple[Path, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    source_hashes = set()
    for shard, (_, payload) in receipts.items():
        validate_shard_base(payload, shard)
        source_hashes.add(payload["source_page_sha256"])
    if len(source_hashes) != 1:
        raise ValueError("MIXED_SOURCE_SNAPSHOTS")

    for shard, (_, payload) in receipts.items():
        join = payload.get("acceptance_time_join", {})
        if shard in EXPECTED_RECOVERY_INPUTS:
            expected = EXPECTED_RECOVERY_INPUTS[shard]
            if payload.get("receipt_fingerprint") != expected["receipt_fingerprint"]:
                raise ValueError("TARGET_RECEIPT_FINGERPRINT_NOT_THE_FROZEN_RUN:" + shard)
            if len(payload.get("acceptance_failures", {})) != expected["failures"]:
                raise ValueError("TARGET_FAILURE_COUNT_CHANGED:" + shard)
            if int(join.get("records_checked", -1)) != expected["checked"] or int(join.get("target_unique_accessions", -1)) != expected["targets"]:
                raise ValueError("TARGET_ACCEPTANCE_COUNTS_CHANGED:" + shard)
            if join.get("complete") is not False or int(join.get("failures", -1)) != expected["failures"]:
                raise ValueError("TARGET_FAILURE_JOIN_INCONSISTENT:" + shard)
            if not set(payload["acceptance_failures"].values()).issubset(RETRYABLE_FAILURES):
                raise ValueError("TARGET_FAILURE_CLASS_OUT_OF_SCOPE:" + shard)
        else:
            if payload.get("acceptance_failures") or join.get("complete") is not True or int(join.get("failures", -1)) != 0:
                raise ValueError("NON_TARGET_SHARD_NOT_CLOCK_COMPLETE:" + shard)
            records_checked = int(join.get("records_checked", -1))
            targets = int(join.get("target_unique_accessions", -1))
            if records_checked <= 0 or records_checked != targets or join.get("timezone_inference") is not False:
                raise ValueError("NON_TARGET_SHARD_JOIN_INVALID:" + shard)
    return {
        shard: {
            "input_receipt_fingerprint": payload["receipt_fingerprint"],
            "failure_count_before": len(payload.get("acceptance_failures", {})),
            "target_unique_accessions": int(payload["acceptance_time_join"]["target_unique_accessions"]),
        }
        for shard, (_, payload) in receipts.items()
    }


def apply_recovered_records(payload: dict[str, Any], records: dict[str, dict[str, Any]], unresolved: dict[str, str]) -> dict[str, Any]:
    payload = json.loads(json.dumps(payload))
    original_failures = dict(payload.get("acceptance_failures", {}))
    current_failures: dict[str, str] = {}
    for archive in payload["archives"]:
        archive_accessions = set()
        for hit in archive["target_hits"].values():
            archive_accessions.update(str(x) for x in hit.get("accessions", []))
        for hit in archive["target_hits"].values():
            acceptance = dict(hit.get("acceptance_records", {}))
            for accession in hit.get("accessions", []):
                accession = str(accession)
                if accession in records:
                    existing = acceptance.get(accession)
                    if existing is not None and existing != records[accession]:
                        raise ValueError("RECOVERY_RECORD_CONFLICT:" + accession)
                    acceptance[accession] = records[accession]
            hit["acceptance_records"] = acceptance
            hit["acceptance_complete"] = len(acceptance) == len(set(hit.get("accessions", [])))
        archive_failures = {}
        for accession in archive_accessions:
            if accession in unresolved:
                archive_failures[accession] = unresolved[accession]
            elif accession in original_failures and accession not in records:
                archive_failures[accession] = original_failures[accession]
        archive["acceptance_failures"] = archive_failures
        archive_records: dict[str, dict[str, Any]] = {}
        for hit in archive["target_hits"].values():
            for accession, record in hit["acceptance_records"].items():
                if accession in archive_records and archive_records[accession] != record:
                    raise ValueError("CROSS_SYMBOL_ACCEPTANCE_RECORD_CONFLICT:" + accession)
                archive_records[accession] = record
        archive["acceptance_record_count"] = len(archive_records)
        archive["target_unique_accession_count"] = len(archive_accessions)
        current_failures.update(archive_failures)

    payload["acceptance_failures"] = current_failures
    checked = sum(int(archive.get("acceptance_record_count", 0)) for archive in payload["archives"])
    targets = sum(int(archive.get("target_unique_accession_count", 0)) for archive in payload["archives"])
    payload["acceptance_time_join"] = {
        "records_checked": checked,
        "target_unique_accessions": targets,
        "failures": len(current_failures),
        "complete": targets == checked and not current_failures,
        "timezone_inference": False,
    }
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload["acceptance_recovery"] = {
        "record_type": "q104_i19_targeted_acceptance_header_recovery",
        "recovered_at_utc": payload["generated_at_utc"],
        "original_receipt_fingerprint": payload.get("receipt_fingerprint"),
        "scope": "retry only the frozen acceptance_failures accession list; no archive download or rescan",
        "initial_failure_count": len(original_failures),
        "resolved_count": sum(1 for accession in original_failures if accession in records),
        "unresolved_count": len(current_failures),
        "request_gap_seconds": REQUEST_GAP_SECONDS,
        "max_attempts_per_accession": MAX_ATTEMPTS,
    }
    payload["receipt_fingerprint"] = fingerprint(payload)
    return payload


def run(input_dir: Path, output_dir: Path) -> dict[str, Any]:
    receipts = load_receipts(input_dir)
    source_context = validate_scope(receipts)
    start = datetime.now(timezone.utc).isoformat()
    limiter = RateLimiter(REQUEST_GAP_SECONDS)
    outcomes: dict[str, dict[str, Any]] = {}
    recovered: dict[str, dict[str, dict[str, Any]]] = {}

    # One shared limiter, one worker: avoid recreating the SEC request burst
    # that coincided with the original transient 503/time-out cluster.
    for shard in sorted(EXPECTED_RECOVERY_INPUTS):
        _, payload = receipts[shard]
        records: dict[str, dict[str, Any]] = {}
        unresolved: dict[str, str] = {}
        for accession, original_error in sorted(payload["acceptance_failures"].items()):
            if original_error not in RETRYABLE_FAILURES:
                raise ValueError("OUT_OF_SCOPE_FAILURE:" + shard + ":" + accession)
            record, error, attempts = fetch_one(str(accession), limiter)
            outcomes[str(accession)] = {
                "shard": shard,
                "initial_error": original_error,
                "attempts": attempts,
                "status": "RECOVERED" if record is not None else "UNRESOLVED",
                "error": error,
                "header_sha256": record["header_sha256"] if record else None,
            }
            if record is not None:
                records[str(accession)] = record
            else:
                unresolved[str(accession)] = error or "UNKNOWN"
            if len(outcomes) % 25 == 0:
                print(json.dumps({
                    "phase": "targeted_acceptance_header_recovery",
                    "completed": len(outcomes),
                    "targeted_total": sum(v["failure_count_before"] for v in source_context.values()),
                }, sort_keys=True), flush=True)
        recovered[shard] = records
        receipts[shard] = (receipts[shard][0], apply_recovered_records(payload, records, unresolved))

    output_dir.mkdir(parents=True, exist_ok=True)
    for shard, (_, payload) in receipts.items():
        path = output_dir / shard / "shard_receipt.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    unresolved_total = sum(1 for item in outcomes.values() if item["status"] != "RECOVERED")
    summary = seal({
        "schema_version": "1.0",
        "record_type": "q104_i19_targeted_acceptance_header_recovery",
        "original_census_run_id": EXPECTED_RUN_ID,
        "captured_at_utc": start,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_shards": source_context,
        "targeted_initial_failures": len(outcomes),
        "resolved": len(outcomes) - unresolved_total,
        "unresolved": unresolved_total,
        "request_gap_seconds": REQUEST_GAP_SECONDS,
        "max_attempts_per_accession": MAX_ATTEMPTS,
        "accession_outcomes": outcomes,
        "updated_shard_receipt_fingerprints": {
            shard: payload["receipt_fingerprint"] for shard, (_, payload) in receipts.items()
        },
        "scientific_boundary": {
            "performance_authorized": False,
            "ranking_allowed": False,
            "tuning_allowed": False,
            "promotion_allowed": False,
            "live_execution_allowed": False,
        },
        "safety": EXPECTED_SAFETY,
    })
    (output_dir / "recovery_receipt.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": "TARGETED_RECOVERY_COMPLETE" if unresolved_total == 0 else "TARGETED_RECOVERY_INCOMPLETE",
        "targeted_initial_failures": len(outcomes),
        "resolved": len(outcomes) - unresolved_total,
        "unresolved": unresolved_total,
        "updated_shards": sorted(EXPECTED_RECOVERY_INPUTS),
        "output_dir": str(output_dir),
        "recovery_receipt_fingerprint": summary["receipt_fingerprint"],
    }, sort_keys=True), flush=True)
    if unresolved_total:
        raise RuntimeError("TARGETED_RECOVERY_INCOMPLETE:" + str(unresolved_total))
    # Validate that the recovered shards are fully clock closed before a merger can consume them.
    for shard in EXPECTED_RECOVERY_INPUTS:
        payload = receipts[shard][1]
        join = payload["acceptance_time_join"]
        if payload["acceptance_failures"] or join["complete"] is not True or join["records_checked"] != join["target_unique_accessions"]:
            raise RuntimeError("REPAIRED_SHARD_NOT_CLOCK_COMPLETE:" + shard)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.input_dir, args.output_dir)
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
