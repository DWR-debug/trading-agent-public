"""Review the expanded Q104:I19 filing-date proposal against 14 pinned cross-vintage rows.

This is deterministic metadata-only analysis of two immutable workflow artifacts. It
does not query SEC, change field precedence, mutate source receipts, or clear any gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SOURCE_RUN_ID = "38557631541"
X64_ARTIFACT = "q104-cross-vintage-38557631541-1"
X64_FP = "95644cd88172dad43cb311ad5b217b4f082185fd3280f7cd5735089eb82ba8cd"
ARM64_ARTIFACT = "q104-cross-vintage-ubuntu-arm-38557631541-1"
ARM64_FP = "1b9236ed4848b51016426e6a9ad6e1623ea318c9455f66f70736286e602cc8cf"
ANALYSIS_FP = "9bff9c1b1b0da2f1415c7aabaa66a5ce97b14abd89015f9d47d61a287189e12b"
PRIOR_FP = "17fa46e3f49b4bb296122a1f6e80b7fbe7e3c134868803b2ddb910f898521412"
R1_FP = "c0881b295d37fa34925103b30acbb893a78bbbe230af6e637576dfda4fac86f7"
R2_FP = "d85ad092296b38f29fa25147537f52804f9a32d9969051c7f9e9cadff283fe04"
R3_FP = "f4c309fe9f5389fdd726fbdb9aa969a46e376d1bd212c3654cc7ec1a6682015a"

FROZEN = {
    "RUN_Q104_I19_CROSS_VINTAGE_PRECEDENCE_REVIEW": "true",
    "REASON": "REVIEW_ONLY_EXPAND_Q104_FILED_DATE_PROPOSAL_TO_FROZEN_14_ROW_AGGREGATE",
    "SOURCE_RUN_ID": SOURCE_RUN_ID,
    "SOURCE_X64_ARTIFACT": X64_ARTIFACT,
    "SOURCE_X64_RECEIPT_FINGERPRINT": X64_FP,
    "SOURCE_ARM64_ARTIFACT": ARM64_ARTIFACT,
    "SOURCE_ARM64_RECEIPT_FINGERPRINT": ARM64_FP,
    "ANALYSIS_FINGERPRINT": ANALYSIS_FP,
    "SOURCE_PRIOR_RECEIPT_FINGERPRINT": PRIOR_FP,
    "R1_RECEIPT_FINGERPRINT": R1_FP,
    "R2_RECEIPT_FINGERPRINT": R2_FP,
    "R3_LINEAGE_RECEIPT_FINGERPRINT": R3_FP,
    "SAMPLE_COUNT": "14",
    "APPLY_FIELD_PRECEDENCE": "false",
    "CHANGE_SOURCE_RECEIPTS": "false",
    "CENSUS_RESTART": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN) | {"REQUEST_SEQUENCE"}


class ReviewError(ValueError):
    pass


def fingerprint(value: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    payload = dict(value)
    payload.pop(field, None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.strip() != line or "=" not in line:
            raise ReviewError(f"REQUEST_INVALID_LINE:{number}")
        key, value = line.split("=", 1)
        if not key or not value or key in values:
            raise ReviewError(f"REQUEST_INVALID_KEY_VALUE:{number}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise ReviewError("REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN.items():
        if values[key] != expected:
            raise ReviewError("REQUEST_VALUE_MISMATCH:" + key)
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise ReviewError("REQUEST_SEQUENCE_INVALID")
    return values


def find_receipt(root: Path) -> Path:
    if root.is_file():
        return root
    found = sorted(root.rglob("receipt.json"))
    if len(found) != 1:
        raise ReviewError(f"AGGREGATE_RECEIPT_COUNT_INVALID:{len(found)}")
    return found[0]


def validate_aggregate(receipt: dict[str, Any], expected_receipt_fp: str) -> dict[str, Any]:
    if receipt.get("record_type") != "q104_i19_cross_vintage_date_change_aggregate":
        raise ReviewError("AGGREGATE_RECORD_TYPE_MISMATCH")
    if receipt.get("status") != "FIELD_PRECEDENCE_EXTENDED_DIAGNOSTIC_ONLY_NOT_APPLIED":
        raise ReviewError("AGGREGATE_STATUS_MISMATCH")
    if receipt.get("receipt_fingerprint") != expected_receipt_fp or fingerprint(receipt) != expected_receipt_fp:
        raise ReviewError("AGGREGATE_RECEIPT_FINGERPRINT_MISMATCH")
    if receipt.get("analysis_fingerprint") != ANALYSIS_FP:
        raise ReviewError("AGGREGATE_ANALYSIS_FINGERPRINT_MISMATCH")
    if (
        receipt.get("source_prior_receipt_fingerprint") != PRIOR_FP
        or receipt.get("source_r1_receipt_fingerprint") != R1_FP
        or receipt.get("source_r2_receipt_fingerprint") != R2_FP
        or receipt.get("source_r3_lineage_receipt_fingerprint") != R3_FP
    ):
        raise ReviewError("AGGREGATE_UPSTREAM_PIN_MISMATCH")
    if receipt.get("source_prior_run_id") != "38304249742":
        raise ReviewError("AGGREGATE_PRIOR_RUN_ID_MISMATCH")
    scope = receipt.get("interpretation_scope") or {}
    for key in (
        "field_precedence_applied", "source_receipts_modified", "acceptance_time_gate_cleared",
        "historical_archive_gate_cleared", "production_join_changed", "census_restarted",
        "performance_authorization", "holdout_selection", "ranking", "tuning", "promotion", "live_execution",
    ):
        if scope.get(key) is not False:
            raise ReviewError("AGGREGATE_SCOPE_VIOLATION:" + key)
    rows = receipt.get("samples")
    counts = receipt.get("counts") or {}
    expected_counts = {
        "sample_count": 14,
        "bulk_date_differs_from_header": 14,
        "header_filing_date_routes_agree": 14,
        "acceptance_routes_agree": 14,
        "date_change_observed": 14,
        "date_change_routes_agree_where_observed": 14,
        "date_change_equals_header_filing_date": 2,
        "date_change_differs_from_header_filing_date": 12,
    }
    if not isinstance(rows, list) or len(rows) != 14 or len({x.get("accession") for x in rows}) != 14:
        raise ReviewError("AGGREGATE_SAMPLE_SET_MISMATCH")
    if counts != expected_counts:
        raise ReviewError("AGGREGATE_COUNTS_MISMATCH")
    for row in rows:
        if not (
            row.get("identity_fields_consistent") is True
            and row.get("header_filing_date_routes_agree") is True
            and row.get("acceptance_routes_agree") is True
            and row.get("date_change_observed") is True
            and row.get("date_change_routes_agree_where_observed") is True
            and row.get("bulk_date_differs_from_header") is True
            and len(row.get("edgar_header_filing_dates") or []) == 1
            and len(row.get("acceptance_datetimes") or []) == 1
            and len(row.get("date_change_values") or []) == 1
            and row.get("edgar_header_filing_date_route_count") == 3
            and row.get("acceptance_route_count") == 3
        ):
            raise ReviewError("AGGREGATE_ROW_CONTRACT_MISMATCH:" + str(row.get("accession")))
    return receipt


def build_review(x64: dict[str, Any], arm64: dict[str, Any]) -> dict[str, Any]:
    validate_aggregate(x64, X64_FP)
    validate_aggregate(arm64, ARM64_FP)
    if x64["analysis_fingerprint"] != arm64["analysis_fingerprint"]:
        raise ReviewError("CROSS_ARCH_ANALYSIS_FINGERPRINT_MISMATCH")
    counts = dict(x64["counts"])
    return {
        "schema_version": 1,
        "record_type": "q104_i19_cross_vintage_filing_date_precedence_review",
        "candidate_id": "Q104:I19",
        "status": "FIELD_PRECEDENCE_REVIEW_PROPOSAL_READY_NOT_APPLIED",
        "source_run_id": SOURCE_RUN_ID,
        "source_x64_artifact": X64_ARTIFACT,
        "source_x64_receipt_fingerprint": X64_FP,
        "source_arm64_artifact": ARM64_ARTIFACT,
        "source_arm64_receipt_fingerprint": ARM64_FP,
        "analysis_fingerprint": ANALYSIS_FP,
        "independent_analysis_fingerprint_match": True,
        "source_prior_receipt_fingerprint": PRIOR_FP,
        "source_r1_receipt_fingerprint": R1_FP,
        "source_r2_receipt_fingerprint": R2_FP,
        "source_r3_lineage_receipt_fingerprint": R3_FP,
        "counts": counts,
        "archive_vintage_count": len({row["source_label"] for row in x64["samples"]}),
        "samples": x64["samples"],
        "proposal": {
            "acceptance_event_clock": "Use EDGAR ACCEPTANCE-DATETIME as a distinct event clock only after exact accession/CIK/form validation and cross-route agreement.",
            "filed_date": "Retain the bulk Form 13F FILING_DATE unchanged as source provenance; use the consistent EDGAR header/index filed date as a separate filed-date field, with an explicit discrepancy flag.",
            "date_of_filing_date_change": "Retain as separate post-acceptance-change metadata; never substitute it for acceptance time or silently overwrite either filing-date source.",
            "arithmetic_or_imputation": "None. No date shifting, timezone arithmetic, imputation, or blanket correction.",
            "application_boundary": "Proposal only. Do not alter the production join until a separately reviewed validation covers the exact unresolved accession population and its source-vintage conflicts.",
        },
        "limitations": [
            "Fourteen preselected observations across five archive vintages are not a prevalence estimate for the 53 unresolved accessions.",
            "This review does not resolve accession identity conflicts, missing historical source records, or first-public-observation time.",
            "The two architecture outputs reproduce the same deterministic analysis; they are not independent source observations.",
        ],
        "interpretation_scope": {
            "descriptive_review_only": True,
            "source_precedence_applied": False,
            "source_receipts_modified": False,
            "production_join_changed": False,
            "acceptance_time_gate_cleared": False,
            "historical_archive_gate_cleared": False,
            "census_restarted": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def run(request_path: Path, x64_dir: Path, arm64_dir: Path, output: Path) -> dict[str, Any]:
    request = read_request(request_path)
    x64 = json.loads(find_receipt(x64_dir).read_text(encoding="utf-8"))
    arm64 = json.loads(find_receipt(arm64_dir).read_text(encoding="utf-8"))
    core = build_review(x64, arm64)
    result = {
        **core,
        "request_sequence": request["REQUEST_SEQUENCE"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    result["receipt_fingerprint"] = fingerprint(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "analysis_fingerprint": result["analysis_fingerprint"],
        "receipt_fingerprint": result["receipt_fingerprint"],
        "counts": result["counts"],
        "source_precedence_applied": result["interpretation_scope"]["source_precedence_applied"],
    }, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--x64-artifact", type=Path, required=True)
    parser.add_argument("--arm64-artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.request, args.x64_artifact, args.arm64_artifact, args.output)
    if result["status"] != "FIELD_PRECEDENCE_REVIEW_PROPOSAL_READY_NOT_APPLIED":
        raise ReviewError("REVIEW_PATTERN_INCOMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
