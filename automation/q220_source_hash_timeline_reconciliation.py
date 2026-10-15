"""Offline reconciliation of Q220's historical positive and later blocked hash states.

Reads only committed JSON receipts. Does not make network requests, fetch source bodies,
or change any frozen hash, gate, or candidate state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = "research/evidence/q220_complete_submission_representation_audit_38619590525.json"
AUDIT_GIT_BLOB_SHA1 = "a33d72025c091ebb6ed93c601df7e0e24551b521"
AUDIT_CAPTURE_RECEIPT_FP = "3d3514a8fcbcc5d711da2cd15a3cf506ba16192022e0f9f15c8f1b9ef8f6a6f3"
LINEAGE_PATH = "research/evidence/q220_source_hash_lineage_latest.json"
LINEAGE_GIT_BLOB_SHA1 = "ead271b6afd6fea8964856c70bbd4cc9d0fe0bb1"
LINEAGE_RECEIPT_FP = "acdec97252ba86d844f97fea2b11b755bef91769cd7badd53a5fedcc811bd059"
LINEAGE_ANALYSIS_FP = "380bc17bdec6c390c4f282ff25cbabbd1c6dcb2a2847a9af6d60711df3dac35e"
EXPECTED_SHA = "27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83"
EXPECTED_BYTES = 4_774_458
POSITIVE_RUN_ID = 38182963418
INDEPENDENT_RUN_ID = 38183038217
FIRST_NEGATIVE_RUN_ID = 38210402239
SAME_CODE_OLDER_BLOB = "17d3464605138e5035718664fb02ff1a56dcf5cc"
SAME_CODE_SHA256 = "62ef075c9fe5ccc2527e5a918f9653a5a6d1602359d4bb795a0e97a5370ddcc1"
COMPILER_CODE_SHA256 = "6a8fb9496181fb2a46393d4d9dc348660b068d50255d807401bb8eff0da686ed"
COMPILER_CODE_BLOB = "c4587f75551297c1ceae9ed151196681eddfbdb8"
POPULATION_FP = "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


class TimelineError(ValueError):
    """Raised when committed source evidence no longer matches its frozen contract."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def read_pinned_json(root: Path, relative_path: str, expected_blob_sha1: str) -> tuple[dict[str, Any], str]:
    path = root / relative_path
    if not path.is_file():
        raise TimelineError(f"PINNED_INPUT_MISSING:{relative_path}")
    data = path.read_bytes()
    actual_blob = git_blob_sha1(data)
    if actual_blob != expected_blob_sha1:
        raise TimelineError(
            f"PINNED_INPUT_GIT_BLOB_MISMATCH:{relative_path}:"
            f"expected={expected_blob_sha1}:actual={actual_blob}"
        )
    try:
        obj = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TimelineError(f"PINNED_INPUT_INVALID_JSON:{relative_path}") from exc
    if not isinstance(obj, dict):
        raise TimelineError(f"PINNED_INPUT_NOT_OBJECT:{relative_path}")
    return obj, actual_blob


def build_analysis(audit: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    history = audit.get("historical_population_hash_drift")
    if not isinstance(history, dict):
        raise TimelineError("HISTORICAL_DRIFT_SECTION_MISSING")
    if history.get("status") != "SAME_CODE_FIVE_BYTE_SHIFT_ACROSS_ALL_55_PRIMARY_DOCUMENTS":
        raise TimelineError("HISTORICAL_SAME_CODE_SHIFT_STATUS_MISMATCH")
    if audit.get("capture_run", {}).get("capture_receipt_fingerprint") != AUDIT_CAPTURE_RECEIPT_FP:
        raise TimelineError("HISTORICAL_AUDIT_CAPTURE_RECEIPT_FINGERPRINT_MISMATCH")
    if audit.get("upstream", {}).get("source_population_receipt_fingerprint") != POPULATION_FP:
        raise TimelineError("HISTORICAL_AUDIT_POPULATION_FINGERPRINT_MISMATCH")
    if current.get("receipt_fingerprint") != LINEAGE_RECEIPT_FP or sha256_json(
        {k: v for k, v in current.items() if k != "receipt_fingerprint"}
    ) != LINEAGE_RECEIPT_FP:
        raise TimelineError("CURRENT_LINEAGE_RECEIPT_FINGERPRINT_MISMATCH")
    if current.get("analysis_fingerprint") != LINEAGE_ANALYSIS_FP:
        raise TimelineError("CURRENT_LINEAGE_ANALYSIS_FINGERPRINT_MISMATCH")
    if current.get("status") != "Q220_SOURCE_HASH_LINEAGE_UNRESOLVED_MULTIPLE_OBSERVED_HASHES":
        raise TimelineError("CURRENT_LINEAGE_STATUS_MISMATCH")
    if current.get("candidate_id") != "Q220":
        raise TimelineError("CURRENT_LINEAGE_CANDIDATE_MISMATCH")
    if current.get("source_receipts", {}).get("compiler_source_population_fingerprint") != POPULATION_FP:
        raise TimelineError("CURRENT_LINEAGE_POPULATION_FINGERPRINT_MISMATCH")

    timeline = history.get("compiler_representation_timeline")
    if not isinstance(timeline, dict) or timeline.get("status") != "TIME_VARYING_PRIMARY_RESPONSE_REPRESENTATIONS_OBSERVED":
        raise TimelineError("COMPILER_TIMELINE_STATUS_MISMATCH")
    positive = timeline.get("known_positive_compiler_observation", {})
    negative = timeline.get("earliest_known_blocked_observation", {})
    window = timeline.get("first_observed_transition_window", {})
    independent = history.get("historical_independent_reproduction", {})
    same_code = history.get("snapshots", [])
    first_negative_run_id = negative.get("workflow_run_id")

    if (
        positive.get("workflow_run_id") != POSITIVE_RUN_ID
        or positive.get("gate_positive") is not True
        or positive.get("verified_primary_document_count") != 55
        or positive.get("source_hash_failure_count") != 0
        or positive.get("receipt_fingerprint") != "1b34b3ac2f3a6fc3ff90fa42cd8ea1c7b73297b5cbd71414a0877bb25d9b203c"
    ):
        raise TimelineError("HISTORICAL_POSITIVE_COMPILER_ATTESTATION_MISMATCH")
    if (
        independent.get("workflow_run", {}).get("id") != INDEPENDENT_RUN_ID
        or independent.get("receipt_status") != "Q220_INDEPENDENT_PIT_REPRODUCED"
        or independent.get("historical_gate_positive") is not True
        or independent.get("record_count") != 55
        or independent.get("source_hash_failure_count") != 0
        or independent.get("present_gate_clearance") is not False
    ):
        raise TimelineError("HISTORICAL_INDEPENDENT_RECEIPT_MISMATCH")
    if (
        first_negative_run_id != FIRST_NEGATIVE_RUN_ID
        or negative.get("source_hash_failure_count") != 55
        or negative.get("verified_primary_document_count") != 0
        or negative.get("gate_positive") is not False
        or negative.get("compiler_code_sha256") != positive.get("compiler_code_sha256")
        or negative.get("compiler_source_git_blob_sha1") != positive.get("compiler_source_git_blob_sha1")
        or negative.get("compiler_code_sha256") != COMPILER_CODE_SHA256
        or negative.get("compiler_source_git_blob_sha1") != COMPILER_CODE_BLOB
    ):
        raise TimelineError("FIRST_NEGATIVE_COMPILER_ATTESTATION_MISMATCH")
    if window.get("elapsed_from_positive_compiler_receipt_seconds") != 24830.828977:
        raise TimelineError("TRANSITION_WINDOW_DURATION_MISMATCH")
    if history.get("code_path_comparison", {}).get("root_cause_proven") is not False:
        raise TimelineError("ROOT_CAUSE_MUST_REMAIN_UNPROVEN")

    snapshots = {row.get("commit"): row for row in same_code}
    before = snapshots.get("65f725a4cde933750d2b06bd4345ab314018bab9")
    after = snapshots.get("3d41bfbf18e525522da7c274e68ed692ef54c8d1")
    if not before or not after:
        raise TimelineError("SAME_CODE_CAPTURE_SNAPSHOTS_MISSING")
    if (
        before.get("gate_code_sha256") != SAME_CODE_SHA256
        or after.get("gate_code_sha256") != SAME_CODE_SHA256
        or before.get("gate_code_git_blob_sha1") != SAME_CODE_OLDER_BLOB
        or after.get("gate_code_git_blob_sha1") != SAME_CODE_OLDER_BLOB
        or after.get("changed_primary_hash_count") != 55
        or after.get("changed_primary_byte_length_count") != 55
        or after.get("primary_byte_delta_distribution") != {"-5": 55}
    ):
        raise TimelineError("SAME_CODE_CAPTURE_SHIFT_CONTRACT_MISMATCH")

    current_observations = [
        row for row in current.get("observations", [])
        if row.get("scope") == "whole_primary_document"
    ]
    current_hashes = sorted({row.get("sha256") for row in current_observations if row.get("sha256")})
    if len(current_observations) != 4 or len(current_hashes) != 4:
        raise TimelineError("CURRENT_WHOLE_PRIMARY_OBSERVATION_COUNT_MISMATCH")
    expected_in_current = EXPECTED_SHA in current_hashes
    if expected_in_current is not False:
        raise TimelineError("CURRENT_OBSERVATIONS_UNEXPECTEDLY_CONTAIN_FROZEN_EXPECTED_HASH")
    if current.get("classification", {}).get("frozen_expected_hash_reproduced") is not False:
        raise TimelineError("CURRENT_LINEAGE_CLASSIFICATION_CHANGED")

    # This is the crucial distinction: the frozen hash was historically attested by
    # a successful compiler and independent-reproduction receipt, but those runs did
    # not preserve raw whole-document bodies for a later byte-for-byte audit.
    core = {
        "schema_version": 1,
        "record_type": "q220_source_hash_timeline_reconciliation",
        "candidate_id": "Q220",
        "status": "HISTORICAL_HASH_MATCH_ATTESTED_CURRENT_LINEAGE_UNRESOLVED",
        "frozen_expected": {
            "sha256": EXPECTED_SHA,
            "bytes": EXPECTED_BYTES,
            "historical_match_attested": True,
            "historical_raw_body_preserved": False,
            "present_in_current_whole_primary_observation_set": False,
            "interpretation": (
                "A historical successful compiler receipt and independent reproduction "
                "attest that all 55 expected hashes matched on 2026-10-11. The raw "
                "whole-document bodies were not retained, so the historical bytes cannot "
                "now be independently re-hashed from the receipt alone."
            ),
        },
        "historical_positive": {
            "compiler_run_id": POSITIVE_RUN_ID,
            "compiler_receipt_fingerprint": positive["receipt_fingerprint"],
            "compiler_receipt_generated_at_utc": positive["generated_at_utc"],
            "verified_primary_document_count": positive["verified_primary_document_count"],
            "source_hash_failure_count": positive["source_hash_failure_count"],
            "compiler_code_sha256": positive["compiler_code_sha256"],
            "compiler_source_git_blob_sha1": positive["compiler_source_git_blob_sha1"],
            "independent_run_id": INDEPENDENT_RUN_ID,
            "independent_receipt_generated_at_utc": independent["receipt_generated_at_utc"],
            "independent_receipt_status": independent["receipt_status"],
            "independent_artifact_id": independent["immutable_artifact"]["id"],
            "independent_artifact_sha256": independent["immutable_artifact"]["sha256"],
            "independent_source_code_git_blob_sha1": independent["independent_retrieval_source_code"]["git_blob_sha1"],
        },
        "first_known_blocked": {
            "compiler_run_id": first_negative_run_id,
            "compiler_receipt_fingerprint": negative["receipt_fingerprint"],
            "compiler_receipt_generated_at_utc": negative["receipt_generated_at_utc"],
            "verified_primary_document_count": negative["verified_primary_document_count"],
            "source_hash_failure_count": negative["source_hash_failure_count"],
            "compiler_code_sha256": negative["compiler_code_sha256"],
            "compiler_source_git_blob_sha1": negative["compiler_source_git_blob_sha1"],
            "same_compiler_code_as_last_positive": True,
        },
        "first_observed_transition_window": {
            "last_known_positive_utc": window["last_known_positive_compiler_receipt_utc"],
            "first_known_negative_utc": window["first_known_negative_compiler_receipt_utc"],
            "elapsed_seconds": window["elapsed_from_positive_compiler_receipt_seconds"],
            "observation_bounds_only": True,
            "server_side_transition_time_proven": False,
        },
        "same_code_population_capture_shift": {
            "earlier_snapshot_utc": before["observed_at_utc"],
            "later_snapshot_utc": after["observed_at_utc"],
            "collector_code_git_blob_sha1": SAME_CODE_OLDER_BLOB,
            "collector_code_sha256": SAME_CODE_SHA256,
            "changed_hash_rows": after["changed_primary_hash_count"],
            "changed_byte_length_rows": after["changed_primary_byte_length_count"],
            "byte_delta_distribution": after["primary_byte_delta_distribution"],
            "header_hash_rows_changed": history["same_code_receipt_diff_field_counts"]["fields_changed"][0]["removed_values"],
            "directory_index_hashes_unchanged": history["same_code_receipt_diff_field_counts"]["observed_unchanged_fields"]["directory_index_sha256"],
            "root_cause_proven": False,
        },
        "current_observation_state": {
            "current_lineage_receipt_fingerprint": LINEAGE_RECEIPT_FP,
            "current_lineage_analysis_fingerprint": LINEAGE_ANALYSIS_FP,
            "whole_primary_observation_count": len(current_observations),
            "distinct_whole_primary_hash_count": len(current_hashes),
            "whole_primary_sha256": current_hashes,
            "frozen_expected_sha256_present_in_current_observation_set": expected_in_current,
            "current_lineage_status": current["status"],
            "all_55_current_compiler_hash_failures_remain": True,
        },
        "source_pins": {
            "historical_audit_path": AUDIT_PATH,
            "historical_audit_git_blob_sha1": AUDIT_GIT_BLOB_SHA1,
            "historical_capture_receipt_fingerprint": AUDIT_CAPTURE_RECEIPT_FP,
            "current_lineage_path": LINEAGE_PATH,
            "current_lineage_git_blob_sha1": LINEAGE_GIT_BLOB_SHA1,
            "current_lineage_receipt_fingerprint": LINEAGE_RECEIPT_FP,
            "current_lineage_analysis_fingerprint": LINEAGE_ANALYSIS_FP,
            "source_population_receipt_fingerprint": POPULATION_FP,
        },
        "interpretation_scope": {
            "historical_hash_match_attested": True,
            "historical_raw_body_rehashable": False,
            "authoritative_source_vintage_proven": False,
            "exact_server_or_intermediary_root_cause_proven": False,
            "current_gate_positive": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": SAFETY,
        "next_gate": (
            "Locate an authoritative pinned source-vintage record or preserve Q220 as BLOCKED. "
            "Do not redownload SEC Feeds or primary documents, rewrite expected hashes, or "
            "restart the census to force a match."
        ),
    }
    return core


def run(root: Path, output: Path, expected_analysis_fingerprint: str | None = None) -> dict[str, Any]:
    audit, audit_blob = read_pinned_json(root, AUDIT_PATH, AUDIT_GIT_BLOB_SHA1)
    current, current_blob = read_pinned_json(root, LINEAGE_PATH, LINEAGE_GIT_BLOB_SHA1)
    if audit_blob != AUDIT_GIT_BLOB_SHA1 or current_blob != LINEAGE_GIT_BLOB_SHA1:
        raise TimelineError("INPUT_GIT_BLOB_PIN_MISMATCH")
    core = build_analysis(audit, current)
    analysis_fp = sha256_json(core)
    if expected_analysis_fingerprint and analysis_fp != expected_analysis_fingerprint:
        raise TimelineError(
            f"ANALYSIS_FINGERPRINT_MISMATCH:expected={expected_analysis_fingerprint}:actual={analysis_fp}"
        )
    result = dict(core)
    result["analysis_fingerprint"] = analysis_fp
    result["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["receipt_fingerprint"] = sha256_json(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-analysis-fingerprint", default=None)
    args = parser.parse_args()
    try:
        result = run(args.repo_root, args.output, args.expected_analysis_fingerprint)
    except TimelineError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps({
        "status": result["status"],
        "analysis_fingerprint": result["analysis_fingerprint"],
        "receipt_fingerprint": result["receipt_fingerprint"],
        "historical_hash_match_attested": result["frozen_expected"]["historical_match_attested"],
        "current_hash_in_observed_set": result["frozen_expected"]["present_in_current_whole_primary_observation_set"],
        "root_cause_proven": result["same_code_population_capture_shift"]["root_cause_proven"],
        "current_gate_positive": result["interpretation_scope"]["current_gate_positive"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
