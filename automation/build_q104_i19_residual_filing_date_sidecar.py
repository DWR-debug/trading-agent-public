"""Build a strictly bounded, provenance-preserving Q104:I19 filing-date sidecar.

The builder is entirely offline. It consumes only the frozen R7 source receipt and
its checked-in independent admissibility review, and does not mutate either input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from automation.q104_i19_residual_policy_independent_review import ReviewError, build_review

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RECEIPT_PATH = Path("research/evidence/q104_i19_residual_policy_applicability_latest.json")
INDEPENDENT_REVIEW_PATH = Path(
    "research/evidence/q104_i19_residual_policy_independent_admissibility_review_latest.json"
)
DEFAULT_OUTPUT_PATH = ROOT / "research/evidence/q104_i19_residual_filing_date_sidecar_latest.json"
EXPECTED_SOURCE_RECEIPT_FINGERPRINT = (
    "de6c5feca4e27f020b77890a6b00e67a87735d6572070f263ba56d8ee24d0444"
)
EXPECTED_REVIEW_STATUS = "INDEPENDENT_REVIEW_COMPLETE"
EXPECTED_DISPOSITION = (
    "NON_DESTRUCTIVE_RESEARCH_REPRESENTATION_ADMISSIBLE_PRODUCTION_PRECEDENCE_NOT_AUTHORIZED"
)
EXPECTED_ROUTE_COUNTS = {"2": 5, "3": 31}


class SidecarError(ValueError):
    """Raised when the frozen source/review evidence does not support the sidecar."""


def _canonical_sha256(value: Mapping[str, Any], *, excluded_key: str | None = None) -> str:
    payload = dict(value)
    if excluded_key is not None:
        payload.pop(excluded_key, None)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_sidecar(
    source_receipt: Mapping[str, Any],
    independent_review: Mapping[str, Any],
) -> dict[str, Any]:
    """Create a deterministic 36-row sidecar, refusing stale or non-admissible inputs."""
    if not isinstance(source_receipt, Mapping) or not isinstance(independent_review, Mapping):
        raise SidecarError("SOURCE_AND_REVIEW_MUST_BE_OBJECTS")
    if (
        source_receipt.get("record_type") != "q104_i19_residual_policy_applicability_review"
        or source_receipt.get("status")
        != "Q104_I19_RESIDUAL_POLICY_APPLICABILITY_REVIEW_COMPLETE_PROPOSAL_NOT_APPLIED"
    ):
        raise SidecarError("SOURCE_RECEIPT_RECORD_TYPE_OR_STATUS_INVALID")

    source_fp = source_receipt.get("receipt_fingerprint")
    if source_fp != EXPECTED_SOURCE_RECEIPT_FINGERPRINT:
        raise SidecarError("SOURCE_RECEIPT_PIN_MISMATCH")
    try:
        calculated_source_fp = _canonical_sha256(source_receipt, excluded_key="receipt_fingerprint")
    except (TypeError, ValueError) as exc:
        raise SidecarError("SOURCE_RECEIPT_FINGERPRINT_RECOMPUTE_FAILED") from exc
    if calculated_source_fp != source_fp:
        raise SidecarError("SOURCE_RECEIPT_FINGERPRINT_INVALID")

    try:
        recomputed_review = build_review(source_receipt)
    except (ReviewError, TypeError, KeyError) as exc:
        raise SidecarError("SOURCE_RECEIPT_FAILED_INDEPENDENT_REVIEW_INVARIANTS") from exc
    if dict(independent_review) != recomputed_review:
        raise SidecarError("INDEPENDENT_REVIEW_DOES_NOT_MATCH_RECOMPUTED_RESULT")
    if (
        independent_review.get("review_status") != EXPECTED_REVIEW_STATUS
        or independent_review.get("disposition") != EXPECTED_DISPOSITION
        or independent_review.get("input_evidence", {}).get("receipt_fingerprint") != source_fp
    ):
        raise SidecarError("INDEPENDENT_REVIEW_STATUS_DISPOSITION_OR_PIN_INVALID")

    cases = source_receipt.get("date_mismatch_cases")
    assessments = independent_review.get("case_assessments")
    counts = source_receipt.get("counts")
    provenance = source_receipt.get("capture_provenance")
    interpretation = source_receipt.get("interpretation_scope")
    safety = source_receipt.get("safety")
    if not all(isinstance(section, Mapping) for section in (counts, provenance, interpretation, safety)):
        raise SidecarError("SOURCE_EVIDENCE_SECTIONS_INVALID")
    if not isinstance(cases, list) or len(cases) != 36:
        raise SidecarError("EXACT_36_SOURCE_CASE_SET_REQUIRED")
    if not isinstance(assessments, list) or len(assessments) != 36:
        raise SidecarError("EXACT_36_REVIEW_ASSESSMENTS_REQUIRED")

    source_by_accession = {
        row.get("accession"): row
        for row in cases
        if isinstance(row, Mapping) and isinstance(row.get("accession"), str)
    }
    review_by_accession = {
        row.get("accession"): row
        for row in assessments
        if isinstance(row, Mapping) and isinstance(row.get("accession"), str)
    }
    if (
        len(source_by_accession) != 36
        or len(review_by_accession) != 36
        or set(source_by_accession) != set(review_by_accession)
    ):
        raise SidecarError("SOURCE_REVIEW_ACCESSION_SET_MISMATCH")

    route_counts: dict[str, int] = {}
    date_change_observed = 0
    date_change_equal = 0
    date_change_different = 0
    sidecar_rows: list[dict[str, Any]] = []
    for accession in sorted(source_by_accession):
        source_case = source_by_accession[accession]
        reviewed_case = review_by_accession[accession]
        for flag in (
            "identity_fields_consistent",
            "header_filing_date_routes_agree",
            "acceptance_routes_agree",
        ):
            if source_case.get(flag) is not True:
                raise SidecarError(f"SOURCE_CASE_VALIDATION_FAILED:{accession}:{flag}")
        bulk_date = source_case.get("bulk_filing_date")
        header_date = source_case.get("edgar_header_filing_date")
        acceptance = source_case.get("acceptance_datetime")
        if (
            not isinstance(bulk_date, str)
            or not isinstance(header_date, str)
            or bulk_date == header_date
            or not isinstance(acceptance, str)
            or not acceptance
        ):
            raise SidecarError(f"DATE_MISMATCH_OR_ACCEPTANCE_MISSING:{accession}")
        if (
            reviewed_case.get("bulk_filing_date") != bulk_date
            or reviewed_case.get("edgar_header_filing_date") != header_date
            or reviewed_case.get("acceptance_datetime") != acceptance
            or reviewed_case.get("identity_verified") is not True
            or reviewed_case.get("header_routes_agree") is not True
            or reviewed_case.get("acceptance_routes_agree") is not True
        ):
            raise SidecarError(f"SOURCE_REVIEW_ROW_MISMATCH:{accession}")

        route_count = source_case.get("successful_header_route_count")
        route_key = str(route_count)
        if route_key not in EXPECTED_ROUTE_COUNTS:
            raise SidecarError(f"SUCCESSFUL_ROUTE_COUNT_INVALID:{accession}")
        route_counts[route_key] = route_counts.get(route_key, 0) + 1

        date_change_flag = source_case.get("date_change_observed")
        date_change_value = source_case.get("date_of_filing_date_change")
        if date_change_flag is True:
            date_change_observed += 1
            if not isinstance(date_change_value, str) or not date_change_value:
                raise SidecarError(f"OBSERVED_DATE_CHANGE_VALUE_MISSING:{accession}")
            if source_case.get("date_change_routes_agree_where_observed") is not True:
                raise SidecarError(f"DATE_CHANGE_ROUTE_DISAGREEMENT:{accession}")
            relation = (
                "EQUALS_EDGAR_HEADER_DATE"
                if date_change_value == header_date
                else "DIFFERS_FROM_EDGAR_HEADER_DATE"
            )
            if date_change_value == header_date:
                date_change_equal += 1
            else:
                date_change_different += 1
        elif date_change_flag is False:
            if date_change_value is not None:
                raise SidecarError(f"UNOBSERVED_DATE_CHANGE_HAS_VALUE:{accession}")
            relation = "NOT_OBSERVED"
        else:
            raise SidecarError(f"DATE_CHANGE_OBSERVATION_FLAG_INVALID:{accession}")

        sidecar_rows.append({
            "accession": accession,
            "bulk_filing_date": bulk_date,
            "bulk_filing_date_provenance": "FROZEN_BULK_DATASET_VALUE_UNMODIFIED",
            "edgar_header_filing_date": header_date,
            "filing_date_discrepancy": True,
            "filing_date_discrepancy_method": "STRING_VALUE_COMPARISON_ONLY_NO_DATE_ARITHMETIC",
            "acceptance_datetime": acceptance,
            "acceptance_datetime_semantics": "EDGAR_ACCEPTANCE_EVENT_ONLY_NOT_FIRST_PUBLIC_OBSERVATION",
            "date_change_observed": date_change_flag,
            "date_of_filing_date_change": date_change_value,
            "date_change_relation_to_edgar_header_date": relation,
            "date_change_routes_agree_where_observed": source_case.get("date_change_routes_agree_where_observed"),
            "identity_fields_consistent": source_case.get("identity_fields_consistent"),
            "header_filing_date_routes_agree": source_case.get("header_filing_date_routes_agree"),
            "acceptance_routes_agree": source_case.get("acceptance_routes_agree"),
            "successful_header_route_count": route_count,
            "source_evidence": source_case.get("source_evidence"),
            "source_archive_name": source_case.get("source_archive_name"),
            "source_archive_pin_status": source_case.get("source_archive_pin_status"),
            "original_recovery_failure": source_case.get("original_recovery_failure"),
        })

    if route_counts != EXPECTED_ROUTE_COUNTS:
        raise SidecarError("SUCCESSFUL_ROUTE_COUNT_AGGREGATE_INVALID")
    if (date_change_observed, date_change_equal, date_change_different) != (17, 2, 15):
        raise SidecarError("DATE_CHANGE_AGGREGATE_INVALID")
    if (
        counts.get("frozen_unresolved_accessions") != 53
        or counts.get("frozen_identity_conflict_accessions") != 7
        or counts.get("frozen_complete_submission_http_404") != 10
        or counts.get("unique_source_verified_date_mismatch_rows") != 36
        or counts.get("identity_fields_validated") != 36
        or counts.get("acceptance_datetime_present_and_cross_route_consistent") != 36
        or counts.get("bulk_filing_date_differs_from_edgar_header_date") != 36
        or counts.get("date_change_observed_rows") != 17
        or counts.get("date_change_equals_edgar_header_date_where_observed") != 2
        or counts.get("date_change_differs_from_edgar_header_date_where_observed") != 15
        or counts.get("successful_header_route_counts_by_case") != EXPECTED_ROUTE_COUNTS
    ):
        raise SidecarError("SOURCE_AGGREGATE_COUNT_MISMATCH")
    if provenance.get("offline_source_requests_made") != 0 or provenance.get("source_capture_receipt_modified") is not False:
        raise SidecarError("SOURCE_CAPTURE_PROVENANCE_INVARIANT_FAILED")
    if any(interpretation.get(flag) is not False for flag in (
        "field_precedence_applied", "production_join_changed", "acceptance_time_gate_cleared",
        "historical_archive_gate_cleared", "scientific_evidence", "performance_authorization",
        "holdout_selection", "ranking", "tuning", "promotion", "live_execution",
    )):
        raise SidecarError("SOURCE_GATE_OR_INTERPRETATION_FLAG_CHANGED")
    if (
        safety.get("paper_only") is not True
        or any(safety.get(flag) is not False for flag in (
            "live_trading_enabled", "orders_enabled", "automatic_promotion",
            "performance_authorization", "holdout_selection", "ranking", "tuning",
            "promotion", "live_execution",
        ))
        or safety.get("paid_api_budget_usd") != 0
    ):
        raise SidecarError("PAPER_ONLY_SAFETY_INVARIANT_FAILED")

    cross_arch = source_receipt.get("cross_arch_reproduction", {})
    if (
        not isinstance(cross_arch, Mapping)
        or cross_arch.get("same_analysis_fingerprint") is not True
        or not cross_arch.get("x64_analysis_fingerprint")
        or cross_arch.get("x64_analysis_fingerprint") != cross_arch.get("arm64_analysis_fingerprint")
        or cross_arch.get("network_requests_made_on_arm64") != 0
    ):
        raise SidecarError("CROSS_ARCH_REPRODUCTION_INVARIANT_FAILED")

    return {
        "schema_version": 1,
        "record_type": "q104_i19_residual_filing_date_sidecar",
        "candidate_id": "Q104:I19",
        "status": "RESEARCH_SIDECAR_READY_NON_PRODUCTION",
        "scope": "EXACT_36_FROZEN_SOURCE_VERIFIED_DATE_MISMATCH_CASES_ONLY",
        "input_evidence": {
            "source_receipt_path": SOURCE_RECEIPT_PATH.as_posix(),
            "source_receipt_fingerprint": source_fp,
            "independent_review_path": INDEPENDENT_REVIEW_PATH.as_posix(),
            "independent_review_status": independent_review.get("review_status"),
            "independent_review_disposition": independent_review.get("disposition"),
            "source_capture_run_id": provenance.get("source_capture_run_id"),
            "source_capture_receipt_fingerprint": provenance.get("source_capture_receipt_fingerprint"),
            "source_capture_head_sha": provenance.get("source_capture_head_sha"),
            "analysis_fingerprint": cross_arch.get("x64_analysis_fingerprint"),
        },
        "counts": {
            "rows": len(sidecar_rows),
            "date_mismatches": len(sidecar_rows),
            "identity_validations": len(sidecar_rows),
            "header_filing_date_cross_route_agreement": len(sidecar_rows),
            "acceptance_datetime_cross_route_agreement": len(sidecar_rows),
            "successful_header_route_counts_by_case": route_counts,
            "r7_allowlisted_index_header_404_cases": 4,
            "frozen_unresolved_accessions_total": 53,
            "identity_conflict_accessions_excluded": 7,
            "complete_submission_http_404_accessions_excluded": 10,
            "date_change_observed": date_change_observed,
            "date_change_equals_header_date": date_change_equal,
            "date_change_differs_from_header_date": date_change_different,
            "date_change_not_observed": len(sidecar_rows) - date_change_observed,
        },
        "field_semantics": {
            "bulk_filing_date": "Preserve the frozen bulk dataset value unchanged as source provenance.",
            "edgar_header_filing_date": "Separate source-qualified EDGAR header date; keep alongside the bulk date with an explicit discrepancy flag.",
            "filing_date_discrepancy": "Exact string inequality only; no date parsing, subtraction, shifting, or inferred correction.",
            "acceptance_datetime": "EDGAR submission acceptance event timestamp only; it is not historical first-public-observation time.",
            "date_of_filing_date_change": "Separate post-acceptance metadata; never substitute it for filing date or acceptance time.",
        },
        "rows": sidecar_rows,
        "guardrails": {
            "bulk_filing_dates_overwritten": False,
            "source_receipt_modified": False,
            "independent_review_receipt_modified": False,
            "source_network_requests": 0,
            "census_restarted": False,
            "production_field_precedence_applied": False,
            "production_field_precedence_authorized": False,
            "production_join_changed": False,
            "production_join_change_authorized": False,
            "historical_first_public_observation_proven": False,
            "historical_pit_authorized": False,
            "scientific_evidence_created": False,
            "performance_authorized": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "paid_api_budget_usd": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / SOURCE_RECEIPT_PATH)
    parser.add_argument("--review", type=Path, default=ROOT / INDEPENDENT_REVIEW_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    try:
        source_receipt = json.loads(args.source.read_text(encoding="utf-8"))
        independent_review = json.loads(args.review.read_text(encoding="utf-8"))
        sidecar = build_sidecar(source_receipt, independent_review)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(sidecar, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError, SidecarError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "status": sidecar["status"],
        "rows": sidecar["counts"]["rows"],
        "source_receipt_fingerprint": sidecar["input_evidence"]["source_receipt_fingerprint"],
        "bulk_filing_dates_overwritten": sidecar["guardrails"]["bulk_filing_dates_overwritten"],
        "production_field_precedence_authorized": sidecar["guardrails"]["production_field_precedence_authorized"],
        "historical_pit_authorized": sidecar["guardrails"]["historical_pit_authorized"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
