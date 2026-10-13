"""Verify one frozen Q220 original SEC Feed submission under a 1 GB hard download ceiling."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from automation import q220_primary_source_vintage_forensics as forensic

ROOT = Path(__file__).resolve().parents[1]
REQUEST_DEFAULT = ROOT / "research/run_requests/q220_single_feed_boundary_validation.trigger"
SOURCE_DEFAULT = ROOT / "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json"
OUTPUT_DEFAULT = ROOT / "research/runs/q220-single-feed-boundary-validation/latest/receipt.json"

FROZEN = {
    "RUN_Q220_SINGLE_FEED_BOUNDARY_VALIDATION": "true",
    "REASON": "VERIFY_ONE_FROZEN_SPGI_FEED_TEXT_CLOSING_BOUNDARY",
    "SOURCE_RECEIPT_PATH": "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json",
    "SOURCE_RECEIPT_GIT_BLOB_SHA": "2a3abbff6c6950e4f11d85dba92cb9c57a5c7ee0",
    "SOURCE_RECEIPT_FINGERPRINT": "c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075",
    "SOURCE_POPULATION_RECEIPT_FINGERPRINT": "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543",
    "SOURCE_HASH_FAILURE_COUNT": "55",
    "TARGET_RECORD_KEY": "0000064040|0000064040-19-000059|10-K|2019-02-13",
    "EXPECTED_SHA256": "27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83",
    "EXPECTED_BYTES": "4774458",
    "FROZEN_CAPTURED_SHA256": "08039132d6d6d1692d1f7552193c70a04cad4c1dcadad1cfa3ca2b8b4efe3fdb",
    "FROZEN_CAPTURED_BYTES": "4774458",
    "PRIMARY_FILENAME": "spgi-20181231x10k.htm",
    "FILING_DATE": "2019-02-13",
    "MAX_FEED_ARCHIVE_BYTES": "900000000",
    "MAX_CURRENT_PRIMARY_BYTES": "15000000",
    "MAX_PRIMARY_MEMBER_BYTES": "30000000",
    "MAX_ORIGINAL_SUBMISSION_MEMBER_BYTES": "150000000",
    "MAX_TAR_SCAN_BYTES": "12000000000",
    "MAX_TOTAL_DOWNLOAD_BYTES": "950000000",
    "CENSUS_RESTART": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN) | {"REQUEST_SEQUENCE"}


class BoundedValidationError(ValueError):
    """A single-sample request or source violates its frozen contract."""


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise BoundedValidationError(f"REQUEST_LINE_INVALID:{line_number}")
        key, value = line.split("=", 1)
        if key in values:
            raise BoundedValidationError(f"REQUEST_DUPLICATE_KEY:{key}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise BoundedValidationError("REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN.items():
        if values[key] != expected:
            raise BoundedValidationError(f"REQUEST_PIN_MISMATCH:{key}")
    sequence = values["REQUEST_SEQUENCE"]
    if not re.fullmatch(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ", sequence):
        raise BoundedValidationError("REQUEST_SEQUENCE_INVALID")
    datetime.fromisoformat(sequence.replace("Z", "+00:00"))
    return values


def canonical_receipt_fingerprint(receipt: dict[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_fingerprint", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return forensic.sha256(encoded)


def validate_source(path: Path, request: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = path.read_bytes()
    blob_sha = forensic.git_blob_sha1(raw)
    if blob_sha != request["SOURCE_RECEIPT_GIT_BLOB_SHA"]:
        raise BoundedValidationError(f"SOURCE_RECEIPT_GIT_BLOB_SHA_MISMATCH:{blob_sha}")
    receipt = json.loads(raw.decode("utf-8"))
    if canonical_receipt_fingerprint(receipt) != request["SOURCE_RECEIPT_FINGERPRINT"]:
        raise BoundedValidationError("SOURCE_RECEIPT_FINGERPRINT_MISMATCH")
    if receipt.get("candidate_id") != "Q220" or receipt.get("status") != "Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED":
        raise BoundedValidationError("SOURCE_RECEIPT_STATUS_MISMATCH")
    if receipt.get("source_population_receipt_fingerprint") != request["SOURCE_POPULATION_RECEIPT_FINGERPRINT"]:
        raise BoundedValidationError("SOURCE_POPULATION_FINGERPRINT_MISMATCH")
    if receipt.get("source_hash_failure_count") != int(request["SOURCE_HASH_FAILURE_COUNT"]):
        raise BoundedValidationError("SOURCE_HASH_FAILURE_COUNT_MISMATCH")
    if receipt.get("gate_positive") is not False:
        raise BoundedValidationError("SOURCE_GATE_STATE_MISMATCH")
    rows = receipt.get("source_hash_failures")
    if not isinstance(rows, list) or len(rows) != int(request["SOURCE_HASH_FAILURE_COUNT"]):
        raise BoundedValidationError("SOURCE_FAILURE_ROWS_MISMATCH")
    key = request["TARGET_RECORD_KEY"]
    matches = [row for row in rows if row.get("record_key") == key]
    if len(matches) != 1:
        raise BoundedValidationError("TARGET_RECORD_KEY_NOT_UNIQUE")
    error = str(matches[0].get("error") or "")
    expected = re.search(r"(?:^|:)expected=([0-9a-f]{64})(?:$|:)", error)
    actual = re.search(r"(?:^|:)actual=([0-9a-f]{64})(?:$|:)", error)
    expected_bytes = re.search(r"(?:^|:)expected_bytes=([0-9]+)(?:$|:)", error)
    actual_bytes = re.search(r"(?:^|:)actual_bytes=([0-9]+)(?:$|:)", error)
    primary = re.search(r"(?:^|:)primary=([^:]+)(?:$|:)", error)
    checks = (
        expected is not None and expected.group(1) == request["EXPECTED_SHA256"],
        actual is not None and actual.group(1) == request["FROZEN_CAPTURED_SHA256"],
        expected_bytes is not None and int(expected_bytes.group(1)) == int(request["EXPECTED_BYTES"]),
        actual_bytes is not None and int(actual_bytes.group(1)) == int(request["FROZEN_CAPTURED_BYTES"]),
        primary is not None and primary.group(1) == request["PRIMARY_FILENAME"],
    )
    if not all(checks):
        raise BoundedValidationError("TARGET_RECORD_SOURCE_PIN_MISMATCH")
    return receipt, matches[0]


def _metadata(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key != "body"}


def _write(path: Path, result: dict[str, Any]) -> None:
    forensic._write_receipt(path, result)


def run(
    request_path: Path,
    source_path: Path,
    output_path: Path,
    fetcher: Callable[..., dict[str, Any]] = forensic._bounded_get_with_retry,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q220_single_frozen_sec_feed_boundary_validation",
        "candidate_id": "Q220",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "NOT_STARTED",
        "request_validation_passed": False,
        "source_receipt_fingerprint": None,
        "source_population_receipt_fingerprint": None,
        "target_record_key": FROZEN["TARGET_RECORD_KEY"],
        "max_feed_archive_bytes": int(FROZEN["MAX_FEED_ARCHIVE_BYTES"]),
        "max_current_primary_bytes": int(FROZEN["MAX_CURRENT_PRIMARY_BYTES"]),
        "max_total_download_bytes": int(FROZEN["MAX_TOTAL_DOWNLOAD_BYTES"]),
        "source_download_bytes": 0,
        "comparison": None,
        "gate_positive": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "historical_first_public_observation_proven": False,
        "source_vintage_proven": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "next_gate": "This one-accession source diagnostic cannot clear Q220; exact source/hash reconciliation across the frozen population remains required.",
    }
    try:
        request = read_request(request_path)
        source_receipt, source_row = validate_source(source_path, request)
        result.update({
            "request_validation_passed": True,
            "request_sequence": request["REQUEST_SEQUENCE"],
            "source_receipt_fingerprint": source_receipt["receipt_fingerprint"],
            "source_population_receipt_fingerprint": source_receipt["source_population_receipt_fingerprint"],
            "frozen_expected_sha256": request["EXPECTED_SHA256"],
            "frozen_expected_bytes": int(request["EXPECTED_BYTES"]),
            "frozen_captured_sha256": request["FROZEN_CAPTURED_SHA256"],
            "frozen_captured_bytes": int(request["FROZEN_CAPTURED_BYTES"]),
            "source_row_error": source_row["error"],
        })
    except Exception as exc:
        result.update({
            "status": "REQUEST_REJECTED",
            "error": f"{type(exc).__name__}: {exc}"[:700],
        })
        _write(output_path, result)
        return result

    budget = forensic.DownloadBudget(int(request["MAX_TOTAL_DOWNLOAD_BYTES"]))
    cik, accession, form, filing_date = request["TARGET_RECORD_KEY"].split("|")
    accession_dir = accession.replace("-", "")
    current_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_dir}/{request['PRIMARY_FILENAME']}"
    feed_url = forensic.daily_feed_url(filing_date)
    try:
        current = fetcher(current_url, int(request["MAX_CURRENT_PRIMARY_BYTES"]), budget)
        result["current_primary"] = _metadata(current)
        if current.get("status") != "FETCHED" or current.get("http_status") != 200:
            result.update({
                "status": "SINGLE_FEED_BOUNDARY_COMPARISON_INCOMPLETE",
                "error": "CURRENT_PRIMARY_FETCH_NOT_SUCCESSFUL",
                "source_download_bytes": budget.used,
            })
            _write(output_path, result)
            return result
        feed = fetcher(feed_url, int(request["MAX_FEED_ARCHIVE_BYTES"]), budget)
        result["feed_archive"] = _metadata(feed)
        if feed.get("status") != "FETCHED" or feed.get("http_status") != 200:
            result.update({
                "status": "SINGLE_FEED_BOUNDARY_COMPARISON_INCOMPLETE",
                "error": "DAILY_FEED_FETCH_NOT_SUCCESSFUL_OR_OVER_LIMIT",
                "source_download_bytes": budget.used,
            })
            _write(output_path, result)
            return result
        scan = forensic.scan_daily_feed(
            feed["body"],
            accession,
            request["PRIMARY_FILENAME"],
            max_scan_bytes=int(request["MAX_TAR_SCAN_BYTES"]),
            max_member_bytes=int(request["MAX_PRIMARY_MEMBER_BYTES"]),
            max_submission_bytes=int(request["MAX_ORIGINAL_SUBMISSION_MEMBER_BYTES"]),
        )
        header = scan.get("submission_header") or {}
        control = scan.get("pds_control_block") or {}
        pds_required = control.get("required_for_identity_validation", True) is not False
        header_checks = {
            "accession_matches": header.get("accession") == accession,
            "filer_cik_matches_company_cik": header.get("filer_cik") == cik,
            "form_matches": str(header.get("form") or "").upper() == form,
            "filing_date_matches": header.get("filed_date_iso") == filing_date,
            "pds_control_block_valid": (not pds_required) or control.get("status") == "PDS_CONTROL_BLOCK_VALID",
            "pds_control_block_accession_matches": (not pds_required) or control.get("accession_matches") is True,
            "pds_control_block_submission_type_matches_sgml": (not pds_required) or control.get("submission_type_matches_sgml") is True,
            "sgml_control_block_conflict_absent": header.get("sgml_acceptance_datetime_comparison") != "MISMATCH",
        }
        primary = scan.get("primary") or {}
        variants = primary.get("body_hash_variants") if primary.get("found") is True else {}
        expected_sha = request["EXPECTED_SHA256"]
        variant_matches = sorted(
            name for name, value in (variants or {}).items()
            if isinstance(value, dict) and value.get("sha256") == expected_sha
        )
        identity_valid = bool(
            scan.get("original_member_name")
            and primary.get("found") is True
            and scan.get("scan_complete") is True
            and scan.get("scan_error") is None
            and all(header_checks.values())
        )
        comparison_complete = bool(
            identity_valid
            and current.get("status") == "FETCHED"
            and feed.get("status") == "FETCHED"
        )
        result["comparison"] = {
            "current_primary": {
                "status": current.get("status"),
                "http_status": current.get("http_status"),
                "response_bytes": current.get("response_bytes"),
                "response_sha256": current.get("response_sha256"),
                "matches_frozen_expected_sha256": current.get("response_sha256") == expected_sha,
                "matches_frozen_capture_sha256": current.get("response_sha256") == request["FROZEN_CAPTURED_SHA256"],
                "matches_frozen_capture_bytes": current.get("response_bytes") == int(request["FROZEN_CAPTURED_BYTES"]),
                "last_modified": current.get("last_modified"),
            },
            "feed": {
                "url": feed_url,
                "archive_sha256": scan.get("feed_archive_sha256"),
                "archive_bytes": scan.get("feed_archive_bytes"),
                "original_member_name": scan.get("original_member_name"),
                "original_member_sha256": scan.get("original_member_sha256"),
                "original_member_bytes": scan.get("original_member_bytes"),
                "original_member_declared_bytes": scan.get("original_member_declared_bytes"),
                "scan_complete": scan.get("scan_complete"),
                "scan_error": scan.get("scan_error"),
                "total_uncompressed_member_bytes_scanned": scan.get("total_uncompressed_member_bytes_scanned"),
                "submission_header": header,
                "header_checks": header_checks,
                "identity_validated": identity_valid,
                "primary": primary,
                "frozen_expected_sha256_match_variants": variant_matches,
                "frozen_expected_sha256_match_count": len(variant_matches),
                "frozen_expected_bytes": int(request["EXPECTED_BYTES"]),
                "variant_byte_deltas_vs_frozen_expected": {
                    name: int(info["bytes"]) - int(request["EXPECTED_BYTES"])
                    for name, info in (variants or {}).items() if isinstance(info, dict) and "bytes" in info
                },
                "comparison_complete": comparison_complete,
                "source_vintage_proven": False,
            },
            "meaning": "A hash match would establish reproduction of one frozen body variant for this accession only. It does not clear Q220, prove the full 55-row population, or establish first public observation time.",
        }
        result["status"] = (
            "SINGLE_FEED_BOUNDARY_COMPARISON_COMPLETE"
            if comparison_complete
            else "SINGLE_FEED_BOUNDARY_COMPARISON_INCOMPLETE"
        )
        result["source_download_bytes"] = budget.used
        if variant_matches:
            result["next_gate"] = "Review the single exact hash match; do not modify frozen hashes or unblock Q220 without a separately reviewed full-population reconciliation."
        else:
            result["next_gate"] = "No frozen hash variant matched this one sample; inspect byte-level provenance and keep Q220 blocked."
    except Exception as exc:
        result.update({
            "status": "SINGLE_FEED_BOUNDARY_COMPARISON_ERROR",
            "error": f"{type(exc).__name__}: {exc}"[:700],
            "source_download_bytes": budget.used,
        })
    _write(output_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, default=REQUEST_DEFAULT)
    parser.add_argument("--source-receipt", type=Path, default=SOURCE_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    receipt = run(args.request, args.source_receipt, args.output)
    print(json.dumps({
        "candidate_id": receipt.get("candidate_id"),
        "status": receipt.get("status"),
        "request_validation_passed": receipt.get("request_validation_passed"),
        "source_download_bytes": receipt.get("source_download_bytes"),
        "max_total_download_bytes": receipt.get("max_total_download_bytes"),
        "frozen_expected_sha256_match_count": (
            (receipt.get("comparison") or {}).get("feed") or {}
        ).get("frozen_expected_sha256_match_count"),
        "gate_positive": False,
        "performance_authorization": False,
        "live_execution": False,
        "receipt_fingerprint": receipt.get("receipt_fingerprint"),
    }, sort_keys=True))
    return 0 if receipt.get("status") == "SINGLE_FEED_BOUNDARY_COMPARISON_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
