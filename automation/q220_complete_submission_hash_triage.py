"""Bounded Q220 comparison of frozen hashes to current complete SEC submissions.

This is a diagnostic only. It does not claim original-vintage identity, update the
frozen expected hashes, or open any PIT/scientific/performance gate.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation import q220_primary_source_vintage_forensics as feed_forensics

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RECEIPT_PATH = "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json"
SOURCE_REQUEST_PATH = "research/run_requests/q220_primary_source_vintage_forensics.trigger"
SOURCE_RECEIPT_GIT_BLOB_SHA = "2a3abbff6c6950e4f11d85dba92cb9c57a5c7ee0"
SOURCE_RECEIPT_FINGERPRINT = "c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075"
SOURCE_POPULATION_RECEIPT_FINGERPRINT = "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
EXPECTED_SOURCE_HASH_FAILURE_COUNT = 55

SAMPLE_EXPECTED_HASHES = {
    "0000064040|0000064040-19-000059|10-K|2019-02-13": "27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83",
    "0001090012|0001564590-19-003382|10-K|2019-02-20": "b024964aa602547d102af1f9cd51c61a3d723ab25b21ef5686b02ac8d4f40dd1",
    "0000064040|0000064040-25-000052|10-K|2025-02-11": "afe05282d5d5af7f3068287cceaa679db962264d5d704d2d32ac19e2c4d3531d",
}
SAMPLE_PRIMARY_NAMES = {
    "0000064040|0000064040-19-000059|10-K|2019-02-13": "spgi-20181231x10k.htm",
    "0001090012|0001564590-19-003382|10-K|2019-02-20": "dvn-10k_20181231.htm",
    "0000064040|0000064040-25-000052|10-K|2025-02-11": "spgi-20241231.htm",
}
SAMPLE_KEYS = tuple(SAMPLE_EXPECTED_HASHES)
MAX_CURRENT_PRIMARY_BYTES = 15_000_000
MAX_COMPLETE_SUBMISSION_BYTES = 30_000_000
MAX_TOTAL_DOWNLOAD_BYTES = 140_000_000
REQUEST_TIMEOUT_SECONDS = 90
REQUEST_GAP_SECONDS = 1.0
USER_AGENT = "DWR-debug/trading-agent-public Q220 complete-submission hash triage research@example.invalid"

FROZEN_REQUEST_VALUES = {
    "RUN_Q220_COMPLETE_SUBMISSION_HASH_TRIAGE": "true",
    "REASON": "COMPARE_FROZEN_Q220_HASHES_TO_THREE_BOUNDED_COMPLETE_SEC_SUBMISSIONS",
    "SOURCE_RECEIPT_PATH": SOURCE_RECEIPT_PATH,
    "SOURCE_RECEIPT_GIT_BLOB_SHA": SOURCE_RECEIPT_GIT_BLOB_SHA,
    "SOURCE_RECEIPT_FINGERPRINT": SOURCE_RECEIPT_FINGERPRINT,
    "SOURCE_POPULATION_RECEIPT_FINGERPRINT": SOURCE_POPULATION_RECEIPT_FINGERPRINT,
    "SOURCE_HASH_FAILURE_COUNT": str(EXPECTED_SOURCE_HASH_FAILURE_COUNT),
    "SAMPLE_COUNT": str(len(SAMPLE_KEYS)),
    "SAMPLE_RECORD_KEYS": ";".join(SAMPLE_KEYS),
    "MAX_CURRENT_PRIMARY_BYTES": str(MAX_CURRENT_PRIMARY_BYTES),
    "MAX_COMPLETE_SUBMISSION_BYTES": str(MAX_COMPLETE_SUBMISSION_BYTES),
    "MAX_TOTAL_DOWNLOAD_BYTES": str(MAX_TOTAL_DOWNLOAD_BYTES),
    "CENSUS_RESTART": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN_REQUEST_VALUES) | {"REQUEST_SEQUENCE"}


class BoundedSourceError(ValueError):
    """Request or source exceeded an explicitly frozen identity/resource boundary."""


class DownloadBudget:
    def __init__(self, maximum: int):
        self.maximum = maximum
        self.used = 0
        self.last_request_monotonic = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delay = REQUEST_GAP_SECONDS - (now - self.last_request_monotonic)
        if delay > 0:
            time.sleep(delay)
        self.last_request_monotonic = time.monotonic()

    def add(self, amount: int) -> None:
        if amount < 0:
            raise BoundedSourceError("Q220_TRIAGE_NEGATIVE_DOWNLOAD_BYTES")
        if self.used + amount > self.maximum:
            self.used += amount
            raise BoundedSourceError("Q220_TRIAGE_TOTAL_DOWNLOAD_BUDGET_EXCEEDED")
        self.used += amount


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def git_blob_sha1(body: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(body)).encode("ascii") + b"\0" + body).hexdigest()


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.strip() != line or "=" not in line:
            raise BoundedSourceError(f"Q220_TRIAGE_REQUEST_INVALID_LINE:{number}")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not value:
            raise BoundedSourceError(f"Q220_TRIAGE_REQUEST_INVALID_KEY_VALUE:{number}")
        if key in values:
            raise BoundedSourceError("Q220_TRIAGE_REQUEST_DUPLICATE_KEY:" + key)
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise BoundedSourceError("Q220_TRIAGE_REQUEST_KEY_SET_MISMATCH")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise BoundedSourceError("Q220_TRIAGE_REQUEST_SEQUENCE_INVALID")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values[key] != expected:
            raise BoundedSourceError("Q220_TRIAGE_REQUEST_VALUE_MISMATCH:" + key)
    return values


def validate_frozen_inputs(request_path: Path, source_request_path: Path, receipt_path: Path) -> tuple[dict[str, str], dict[str, Any]]:
    request = read_request(request_path)
    request_blob = git_blob_sha1(receipt_path.read_bytes())
    if request_blob != request["SOURCE_RECEIPT_GIT_BLOB_SHA"]:
        raise BoundedSourceError("Q220_TRIAGE_SOURCE_RECEIPT_BLOB_MISMATCH:" + request_blob)
    source_request, receipt = feed_forensics.validate_frozen_source(source_request_path, receipt_path)
    if source_request["SOURCE_RECEIPT_FINGERPRINT"] != request["SOURCE_RECEIPT_FINGERPRINT"]:
        raise BoundedSourceError("Q220_TRIAGE_SOURCE_RECEIPT_FINGERPRINT_MISMATCH")
    if source_request["SOURCE_POPULATION_RECEIPT_FINGERPRINT"] != request["SOURCE_POPULATION_RECEIPT_FINGERPRINT"]:
        raise BoundedSourceError("Q220_TRIAGE_POPULATION_FINGERPRINT_MISMATCH")
    if receipt.get("source_hash_failure_count") != EXPECTED_SOURCE_HASH_FAILURE_COUNT or receipt.get("gate_positive") is not False:
        raise BoundedSourceError("Q220_TRIAGE_SOURCE_GATE_STATE_MISMATCH")
    if request["SAMPLE_RECORD_KEYS"].split(";") != list(SAMPLE_KEYS):
        raise BoundedSourceError("Q220_TRIAGE_SAMPLE_ORDER_MISMATCH")
    return request, receipt


def complete_submission_url(cik: str, accession: str) -> str:
    if not re.fullmatch(r"\d{10}", cik):
        raise BoundedSourceError("Q220_TRIAGE_INVALID_COMPANY_CIK")
    if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
        raise BoundedSourceError("Q220_TRIAGE_INVALID_ACCESSION")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession.replace('-', '')}/{accession}.txt"
    )


def current_primary_url(cik: str, accession: str, filename: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,200}", filename):
        raise BoundedSourceError("Q220_TRIAGE_INVALID_PRIMARY_FILENAME")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession.replace('-', '')}/{filename}"
    )


def bounded_get(url: str, max_bytes: int, budget: DownloadBudget) -> dict[str, Any]:
    if budget.used >= budget.maximum:
        return {"requested_url": url, "status": "TOTAL_DOWNLOAD_BUDGET_EXHAUSTED", "response_bytes": 0, "body": b""}
    remaining = budget.maximum - budget.used
    per_request_limit = min(max_bytes, remaining)
    budget.wait()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,text/plain,*/*",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            headers = response.headers
            length_header = headers.get("Content-Length")
            declared_length = int(length_header) if length_header and str(length_header).isdigit() else None
            metadata = {
                "requested_url": url,
                "final_url": str(response.geturl()),
                "http_status": int(getattr(response, "status", 200)),
                "content_type": str(headers.get("Content-Type", "")),
                "content_encoding": str(headers.get("Content-Encoding", "")),
                "content_length_header": declared_length,
                "last_modified": str(headers.get("Last-Modified", "")),
                "etag": str(headers.get("ETag", "")),
            }
            if declared_length is not None and declared_length > max_bytes:
                return {**metadata, "status": "SKIPPED_DECLARED_LENGTH_OVER_LIMIT", "body": b"", "response_bytes": 0}
            if declared_length is not None and declared_length > remaining:
                return {**metadata, "status": "SKIPPED_DECLARED_LENGTH_OVER_TOTAL_BUDGET", "body": b"", "response_bytes": 0}
            read_limit = min(max_bytes + 1, remaining)
            body = response.read(read_limit)
            budget.add(len(body))
            if len(body) > max_bytes:
                return {**metadata, "status": "SKIPPED_ACTUAL_LENGTH_OVER_LIMIT", "body": b"", "response_bytes": len(body)}
            if len(body) == remaining and remaining <= max_bytes and declared_length is None:
                return {**metadata, "status": "TOTAL_DOWNLOAD_BUDGET_EDGE_REACHED", "body": b"", "response_bytes": len(body)}
            return {**metadata, "status": "FETCHED", "body": body, "response_bytes": len(body), "response_sha256": sha256(body)}
    except urllib.error.HTTPError as exc:
        return {
            "requested_url": url,
            "final_url": str(getattr(exc, "url", url)),
            "http_status": int(exc.code),
            "content_type": str((exc.headers or {}).get("Content-Type", "")),
            "content_encoding": str((exc.headers or {}).get("Content-Encoding", "")),
            "content_length_header": None,
            "last_modified": str((exc.headers or {}).get("Last-Modified", "")),
            "etag": str((exc.headers or {}).get("ETag", "")),
            "status": "HTTP_ERROR",
            "response_bytes": 0,
            "body": b"",
            "error": f"HTTP_{exc.code}",
        }
    except (urllib.error.URLError, TimeoutError, OSError, BoundedSourceError) as exc:
        return {"requested_url": url, "status": "FETCH_ERROR", "response_bytes": 0, "body": b"", "error": f"{type(exc).__name__}: {exc}"[:500]}


def _metadata_without_body(value: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in value.items() if k != "body"}


def _parse_frozen_sample(receipt: dict[str, Any], key: str) -> dict[str, Any]:
    rows = {
        str(row.get("record_key")): row
        for row in receipt.get("source_hash_failures", [])
        if isinstance(row, dict)
    }
    row = rows.get(key)
    if row is None:
        raise BoundedSourceError("Q220_TRIAGE_SAMPLE_MISSING_FROM_RECEIPT:" + key)
    expected_error = str(row.get("error") or "")
    parsed = {}
    for name, pattern in {
        "expected_sha256": r"(?:^|:)expected=([0-9a-f]{64})(?:$|:)",
        "actual_sha256": r"(?:^|:)actual=([0-9a-f]{64})(?:$|:)",
        "expected_bytes": r"(?:^|:)expected_bytes=([0-9]+)(?:$|:)",
        "actual_bytes": r"(?:^|:)actual_bytes=([0-9]+)(?:$|:)",
        "primary": r"(?:^|:)primary=([^:]+)(?:$|:)",
    }.items():
        match = re.search(pattern, expected_error)
        parsed[name] = int(match.group(1)) if match and name.endswith("_bytes") else match.group(1) if match else None
    if parsed["expected_sha256"] != SAMPLE_EXPECTED_HASHES[key] or parsed["primary"] != SAMPLE_PRIMARY_NAMES[key]:
        raise BoundedSourceError("Q220_TRIAGE_SAMPLE_RECEIPT_PIN_MISMATCH:" + key)
    if not parsed["actual_sha256"] or not parsed["expected_bytes"] or not parsed["actual_bytes"]:
        raise BoundedSourceError("Q220_TRIAGE_SAMPLE_ACTUAL_RECEIPT_FIELDS_MISSING:" + key)
    return {"row": row, **parsed}


def run(request_path: Path, source_request_path: Path, receipt_path: Path, output_path: Path) -> dict[str, Any]:
    receipt_out: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q220_bounded_complete_submission_hash_triage",
        "candidate_id": "Q220",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "NOT_STARTED",
        "request_validation_passed": False,
        "source_receipt_fingerprint": None,
        "source_hash_failure_count": None,
        "sample_count": 0,
        "samples": [],
        "download_bytes_total": 0,
        "original_source_vintage_proven": False,
        "historical_first_public_observation_proven": False,
        "gate_positive": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "next_gate": "reconcile frozen primary hashes with bounded complete-submission observations; never change hashes or reopen Q220 automatically",
    }
    try:
        request, frozen = validate_frozen_inputs(request_path, source_request_path, receipt_path)
        receipt_out.update({
            "request_validation_passed": True,
            "request_sequence": request["REQUEST_SEQUENCE"],
            "source_receipt_path": SOURCE_RECEIPT_PATH,
            "source_receipt_git_blob_sha": request["SOURCE_RECEIPT_GIT_BLOB_SHA"],
            "source_receipt_fingerprint": frozen["receipt_fingerprint"],
            "source_population_receipt_fingerprint": frozen["source_population_receipt_fingerprint"],
            "source_hash_failure_count": frozen["source_hash_failure_count"],
            "sample_record_keys": list(SAMPLE_KEYS),
            "request_mode": "THREE_COMPLETE_SEC_SUBMISSION_TEXTS_AND_THREE_CURRENT_PRIMARY_DOCUMENTS; BYTE_BOUNDED_READ_ONLY",
            "maximum_complete_submission_bytes": MAX_COMPLETE_SUBMISSION_BYTES,
            "maximum_current_primary_bytes": MAX_CURRENT_PRIMARY_BYTES,
            "maximum_total_download_bytes": MAX_TOTAL_DOWNLOAD_BYTES,
            "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        })
    except Exception as exc:
        receipt_out.update({
            "status": "REQUEST_REJECTED",
            "error": f"{type(exc).__name__}: {exc}"[:700],
            "next_gate": "repair exact frozen inputs/request; no SEC HTTP request was made",
        })
        write_receipt(output_path, receipt_out)
        return receipt_out

    budget = DownloadBudget(MAX_TOTAL_DOWNLOAD_BYTES)
    failures = {str(x.get("record_key")): x for x in frozen["source_hash_failures"] if isinstance(x, dict)}
    all_complete = True
    for key in SAMPLE_KEYS:
        parts = key.split("|")
        cik, accession, form, filed_date = parts
        try:
            frozen_sample = _parse_frozen_sample(frozen, key)
        except Exception as exc:
            receipt_out["samples"].append({"record_key": key, "status": "SAMPLE_PIN_REJECTED", "error": f"{type(exc).__name__}: {exc}"[:500]})
            all_complete = False
            continue
        sample = {
            "record_key": key,
            "company_cik": cik,
            "accession": accession,
            "form": form,
            "filed_date": filed_date,
            "primary_filename": SAMPLE_PRIMARY_NAMES[key],
            "frozen_expected_sha256": frozen_sample["expected_sha256"],
            "frozen_actual_sha256": frozen_sample["actual_sha256"],
            "frozen_expected_bytes": frozen_sample["expected_bytes"],
            "frozen_actual_bytes": frozen_sample["actual_bytes"],
            "frozen_error": frozen_sample["row"].get("error"),
            "current_primary": None,
            "complete_submission": None,
            "identity_checks": {},
            "body_hash_variants": {},
            "classification": "UNRESOLVED",
            "original_source_vintage_proven": False,
        }
        # Directly observe the current filing-specific primary path and its headers.
        primary = bounded_get(current_primary_url(cik, accession, SAMPLE_PRIMARY_NAMES[key]), MAX_CURRENT_PRIMARY_BYTES, budget)
        sample["current_primary"] = _metadata_without_body(primary)
        if primary.get("status") == "FETCHED":
            sample["current_primary"]["matches_frozen_actual_sha256"] = primary["response_sha256"] == frozen_sample["actual_sha256"]
            sample["current_primary"]["matches_frozen_actual_bytes"] = primary["response_bytes"] == frozen_sample["actual_bytes"]
            sample["current_primary"]["matches_frozen_expected_sha256"] = primary["response_sha256"] == frozen_sample["expected_sha256"]
        else:
            sample["current_primary"]["matches_frozen_actual_sha256"] = False

        # Fetch exactly the complete submission text for this pinned accession; no tar/ZIP/whole-day feed is downloaded.
        submission = bounded_get(complete_submission_url(cik, accession), MAX_COMPLETE_SUBMISSION_BYTES, budget)
        sample["complete_submission"] = _metadata_without_body(submission)
        identity_ok = False
        if submission.get("status") == "FETCHED":
            header = feed_forensics.parse_submission_header(submission["body"])
            checks = {
                "accession_matches": header.get("accession") == accession,
                "company_cik_matches": header.get("filer_cik") == cik,
                "form_matches": str(header.get("form") or "").upper() == form,
                "filed_date_matches": header.get("filed_date_iso") == filed_date,
                "acceptance_datetime_present": bool(header.get("acceptance_datetime")),
            }
            identity_ok = all(checks.values())
            sample["identity_checks"] = {**checks, "header": header}
            if identity_ok:
                embedded = feed_forensics.extract_primary_document(submission["body"], SAMPLE_PRIMARY_NAMES[key])
                sample["embedded_primary"] = {k: v for k, v in embedded.items() if k not in {"body", "raw_body"}}
                if embedded.get("found") is True:
                    sample["body_hash_variants"] = embedded.get("body_hash_variants", {})
                    expected = frozen_sample["expected_sha256"]
                    matched = sorted(
                        name for name, info in sample["body_hash_variants"].items()
                        if isinstance(info, dict) and info.get("sha256") == expected
                    )
                    current_sha = primary.get("response_sha256") if primary.get("status") == "FETCHED" else None
                    if matched and current_sha != expected:
                        sample["classification"] = "FROZEN_HASH_MATCHES_EMBEDDED_SUBMISSION_BODY_VARIANT_CURRENT_PRIMARY_DIFFERS"
                    elif matched:
                        sample["classification"] = "FROZEN_HASH_MATCHES_EMBEDDED_SUBMISSION_BODY_VARIANT_AND_CURRENT_PRIMARY"
                    elif current_sha == expected:
                        sample["classification"] = "FROZEN_HASH_MATCHES_CURRENT_PRIMARY_ONLY"
                    else:
                        sample["classification"] = "FROZEN_HASH_MATCHES_NEITHER_OBSERVED_BODY"
                else:
                    sample["classification"] = "EMBEDDED_PRIMARY_EXTRACTION_INCOMPLETE"
            else:
                sample["classification"] = "COMPLETE_SUBMISSION_HEADER_IDENTITY_MISMATCH"
        else:
            sample["classification"] = str(submission.get("status") or "COMPLETE_SUBMISSION_FETCH_FAILED")

        sample["comparison_complete"] = bool(
            primary.get("status") == "FETCHED"
            and submission.get("status") == "FETCHED"
            and identity_ok
            and sample.get("embedded_primary", {}).get("found") is True
        )
        if not sample["comparison_complete"]:
            all_complete = False
        receipt_out["samples"].append(sample)

    receipt_out["sample_count"] = len(receipt_out["samples"])
    receipt_out["completed_sample_count"] = sum(x.get("comparison_complete") is True for x in receipt_out["samples"])
    receipt_out["download_bytes_total"] = budget.used
    if receipt_out["completed_sample_count"] == len(SAMPLE_KEYS) and all_complete:
        receipt_out["status"] = "COMPLETE_SUBMISSION_TRIAGE_COMPLETE"
        receipt_out["next_gate"] = (
            "compare observed body variants with frozen provenance; current complete submissions do not prove original historical vintage or first-public time"
        )
    else:
        receipt_out["status"] = "COMPLETE_SUBMISSION_TRIAGE_INCOMPLETE"
        receipt_out["next_gate"] = (
            "inspect the exact bounded fetch/identity errors; do not broaden downloads, change expected hashes, or reopen the PIT gate"
        )
    receipt_out["original_source_vintage_proven"] = False
    receipt_out["historical_first_public_observation_proven"] = False
    receipt_out["gate_positive"] = False
    receipt_out["scientific_evidence"] = False
    receipt_out["performance_authorization"] = False
    receipt_out["source_failures_by_classification"] = {}
    for sample in receipt_out["samples"]:
        label = str(sample.get("classification") or "UNKNOWN")
        receipt_out["source_failures_by_classification"][label] = receipt_out["source_failures_by_classification"].get(label, 0) + 1
    write_receipt(output_path, receipt_out)
    return receipt_out


def write_receipt(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source-request", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.request, args.source_request, args.receipt, args.output)
    print(json.dumps({
        "status": result.get("status"),
        "candidate_id": result.get("candidate_id"),
        "sample_count": result.get("sample_count"),
        "completed_sample_count": result.get("completed_sample_count"),
        "download_bytes_total": result.get("download_bytes_total"),
        "gate_positive": result.get("gate_positive"),
        "receipt_fingerprint": result.get("receipt_fingerprint"),
    }, sort_keys=True))
    raise SystemExit(0 if result.get("status") == "COMPLETE_SUBMISSION_TRIAGE_COMPLETE" else 2)
