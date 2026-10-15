"""Validate and persist Q221 DoD 097 R2 Wayback probe receipts without changing source results."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

RECEIPT_FILENAME = "q221-dod-097-wayback-presence-r2.json"
ATTEMPT_PREFIX = "q221_dod_097_wayback_archive_presence_attempt_"
LATEST_FILENAME = "q221_dod_097_wayback_archive_presence_latest.json"
MANIFEST = {
    "path": "research/evidence/q221_historical_public_boundary_latest.json",
    "git_blob_sha1": "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f",
    "receipt_fingerprint": "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4",
    "expected_transaction_count": 348,
}
ARCHIVE = {
    "filename": "FY2025_097_Contracts_Full_20250106.zip",
    "original_url": "https://files.usaspending.gov/award_data_archive/FY2025_097_Contracts_Full_20250106.zip",
    "wayback_capture_timestamp": "20250128184322",
    "capture_timestamp_utc": "2025-01-28T18:43:22Z",
    "cdx_sha1_base32": "IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB",
    "length_bytes": 13_605_284,
}
ALLOWED_TYPES = {
    "q221_dod_097_wayback_archive_presence_probe",
    "q221_dod_097_wayback_archive_presence_recovery_fallback_receipt",
}
SAFETY_FALSE_KEYS = (
    "live_trading_enabled", "orders_enabled", "scientific_evidence",
    "performance_authorization", "holdout_selection", "ranking", "tuning",
    "promotion", "live_execution",
)


class ReceiptPersistenceError(ValueError):
    """A receipt failed validation or an immutable path would be overwritten."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def canonical_fingerprint(receipt: dict[str, Any]) -> str:
    payload = {key: value for key, value in receipt.items() if key != "receipt_fingerprint"}
    try:
        canonical = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ReceiptPersistenceError("R2_RECEIPT_CANONICALIZATION_FAILED", type(exc).__name__) from exc
    return hashlib.sha256(canonical).hexdigest()


def validate_receipt(receipt: dict[str, Any]) -> None:
    if not isinstance(receipt, dict) or receipt.get("candidate_id") != "Q221":
        raise ReceiptPersistenceError("R2_RECEIPT_IDENTITY_INVALID", "candidate id is not Q221")
    record_type = receipt.get("record_type")
    if record_type not in ALLOWED_TYPES:
        raise ReceiptPersistenceError("R2_RECEIPT_TYPE_INVALID", str(record_type))
    fingerprint = receipt.get("receipt_fingerprint")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise ReceiptPersistenceError("R2_RECEIPT_FINGERPRINT_MISSING", "missing SHA-256 fingerprint")
    if canonical_fingerprint(receipt) != fingerprint:
        raise ReceiptPersistenceError("R2_RECEIPT_FINGERPRINT_MISMATCH", "canonical fingerprint differs")

    safety = receipt.get("safety")
    if not isinstance(safety, dict) or safety.get("paper_only") is not True:
        raise ReceiptPersistenceError("R2_PAPER_ONLY_ASSERTION_MISSING", "PAPER_ONLY is not true")
    for key in SAFETY_FALSE_KEYS:
        if safety.get(key) is not False:
            raise ReceiptPersistenceError("R2_SAFETY_GATE_NOT_CLOSED", key)

    if record_type == "q221_dod_097_wayback_archive_presence_probe":
        if receipt.get("frozen_source_manifest") != MANIFEST:
            raise ReceiptPersistenceError("R2_FROZEN_MANIFEST_PIN_MISMATCH", "source manifest differs")
        archive = receipt.get("archive_capture", {})
        if any(archive.get(key) != value for key, value in ARCHIVE.items()):
            raise ReceiptPersistenceError("R2_ARCHIVE_PIN_MISMATCH", "archive capture pins differ")
        row_selection = receipt.get("frozen_row_selection", {})
        if (
            row_selection.get("expected_transaction_count") != 28
            or row_selection.get("fiscal_year") != 2025
            or row_selection.get("awarding_agency") != "Department of Defense"
            or row_selection.get("agency_exception_class") != "DOD_90_DAY_EXCEPTION_CANDIDATE"
            or row_selection.get("match_fields") != ["PIID", "modification", "action_date", "recipient_uei"]
        ):
            raise ReceiptPersistenceError("R2_FROZEN_ROW_SELECTION_MISMATCH", "row selection differs")
        probe = receipt.get("source_probe", {})
        if (
            probe.get("request_profile") != "R2"
            or probe.get("one_shot_attempt") != 2
            or probe.get("preregistration_path") != "research/preregistrations/q221_dod_097_wayback_archive_presence_r2_2026_10_15.json"
            or probe.get("request_marker_path") != "research/run_requests/q221_dod_097_wayback_archive_presence_r2.trigger"
            or probe.get("request_marker_validated") is not True
            or probe.get("preregistration_validated") is not True
        ):
            raise ReceiptPersistenceError("R2_REQUEST_PROFILE_PROVENANCE_INVALID", "R2 marker/preregistration differs")
        count = probe.get("request_count")
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 2:
            raise ReceiptPersistenceError("R2_SOURCE_REQUEST_COUNT_INVALID", str(count))
        response_bytes = probe.get("response_bytes")
        if isinstance(response_bytes, bool) or not isinstance(response_bytes, int) or not 0 <= response_bytes <= 25_000_000:
            raise ReceiptPersistenceError("R2_RESPONSE_BYTES_INVALID", str(response_bytes))
        responses = probe.get("responses")
        if not isinstance(responses, list) or len(responses) > 2:
            raise ReceiptPersistenceError("R2_RESPONSE_RECORDS_INVALID", "more than two or malformed responses")
    else:
        if (
            receipt.get("probe_attempt_number") != 2
            or receipt.get("recovery_of_workflow_run_id") != 38791554425
        ):
            raise ReceiptPersistenceError("R2_FALLBACK_LINEAGE_INVALID", "fallback does not identify R2 recovery")
        probe = receipt.get("source_probe", {})
        if probe.get("request_count_known") is not False or probe.get("response_outcome_known") is not False:
            raise ReceiptPersistenceError("R2_FALLBACK_MUST_PRESERVE_UNKNOWN_OUTCOME", "unknown source outcome was altered")
        if receipt.get("archive_schema_and_row_presence") is not None:
            raise ReceiptPersistenceError("R2_FALLBACK_RESULT_MUST_REMAIN_UNKNOWN", "fallback contains a row result")


def persist_receipt(artifact_root: Path, output_dir: Path, run_id: int | str) -> dict[str, str]:
    run_text = str(run_id)
    if not run_text.isdigit() or int(run_text) <= 0:
        raise ReceiptPersistenceError("R2_SOURCE_RUN_ID_INVALID", run_text)
    matches = list(artifact_root.rglob(RECEIPT_FILENAME))
    if len(matches) != 1:
        raise ReceiptPersistenceError("R2_RECEIPT_ARTIFACT_COUNT_INVALID", str(len(matches)))
    source = matches[0]
    try:
        raw = source.read_bytes()
        receipt = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReceiptPersistenceError("R2_RECEIPT_ARTIFACT_READ_FAILED", type(exc).__name__) from exc
    if not isinstance(receipt, dict):
        raise ReceiptPersistenceError("R2_RECEIPT_SHAPE_INVALID", "receipt must be an object")
    validate_receipt(receipt)

    output_dir.mkdir(parents=True, exist_ok=True)
    attempt = output_dir / f"{ATTEMPT_PREFIX}{run_text}.json"
    latest = output_dir / LATEST_FILENAME
    if attempt.exists():
        raise ReceiptPersistenceError("IMMUTABLE_R2_ATTEMPT_RECEIPT_ALREADY_EXISTS", str(attempt))
    attempt_tmp = attempt.with_suffix(attempt.suffix + ".tmp")
    latest_tmp = latest.with_suffix(latest.suffix + ".tmp")
    try:
        attempt_tmp.write_bytes(raw)
        latest_tmp.write_bytes(raw)
        attempt_tmp.replace(attempt)
        latest_tmp.replace(latest)
    except OSError as exc:
        attempt_tmp.unlink(missing_ok=True)
        latest_tmp.unlink(missing_ok=True)
        raise ReceiptPersistenceError("R2_RECEIPT_FILE_WRITE_FAILED", type(exc).__name__) from exc
    return {
        "receipt_fingerprint": receipt["receipt_fingerprint"],
        "attempt_path": str(attempt),
        "latest_path": str(latest),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        result = persist_receipt(args.artifact_root, args.output_dir, args.run_id)
    except ReceiptPersistenceError as exc:
        print(json.dumps({"status": exc.code, "message": exc.message}, sort_keys=True))
        return 2
    print(json.dumps({"status": "R2_RECEIPT_VALIDATED_FOR_PERSISTENCE", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
