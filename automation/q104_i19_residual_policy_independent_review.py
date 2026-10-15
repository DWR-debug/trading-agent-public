"""Independent admissibility review for the bounded Q104:I19 date-mismatch evidence.

This module consumes the already-published R7 review receipt only. It performs no
network requests, source capture, census restart, receipt rewrite, or production change.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "research/evidence/q104_i19_residual_policy_applicability_latest.json"
DEFAULT_OUTPUT = ROOT / "research/evidence/q104_i19_residual_policy_independent_admissibility_review_latest.json"
SOURCE_RECEIPT_STATUS = "Q104_I19_RESIDUAL_POLICY_APPLICABILITY_REVIEW_COMPLETE_PROPOSAL_NOT_APPLIED"
EXPECTED_DATE_MISMATCH_COUNT = 36
EXPECTED_ROUTE_COUNTS = {"2": 5, "3": 31}
EXPECTED_R7_INDEX_404_ACCESSIONS = frozenset({
    "0000950123-13-006949",
    "0000950123-13-006978",
    "0000950123-13-006995",
    "0000950123-13-007038",
})
REQUIRED_FALSE_INTERPRETATION_FLAGS = (
    "field_precedence_applied",
    "source_receipts_modified",
    "production_join_changed",
    "census_restarted",
    "source_capture_receipt_modified",
    "acceptance_time_gate_cleared",
    "historical_archive_gate_cleared",
    "scientific_evidence",
    "performance_authorization",
    "holdout_selection",
    "ranking",
    "tuning",
    "promotion",
    "live_execution",
)


class ReviewError(ValueError):
    """Raised when the frozen evidence fails an independent review invariant."""


def build_review(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic, non-authorizing review from the published receipt."""
    if receipt.get("record_type") != "q104_i19_residual_policy_applicability_review":
        raise ReviewError("SOURCE_RECEIPT_RECORD_TYPE_INVALID")
    if receipt.get("status") != SOURCE_RECEIPT_STATUS:
        raise ReviewError("SOURCE_RECEIPT_STATUS_INVALID")

    counts = receipt.get("counts")
    cases = receipt.get("date_mismatch_cases")
    provenance = receipt.get("capture_provenance")
    interpretation = receipt.get("interpretation_scope")
    safety = receipt.get("safety")
    if not all(isinstance(value, dict) for value in (counts, provenance, interpretation, safety)):
        raise ReviewError("SOURCE_RECEIPT_SECTIONS_INVALID")
    if not isinstance(cases, list) or len(cases) != EXPECTED_DATE_MISMATCH_COUNT:
        raise ReviewError("EXACT_36_CASE_SET_INVALID")

    accessions = [case.get("accession") for case in cases if isinstance(case, dict)]
    if len(accessions) != EXPECTED_DATE_MISMATCH_COUNT or len(set(accessions)) != EXPECTED_DATE_MISMATCH_COUNT:
        raise ReviewError("CASE_ACCESSION_SET_INVALID")

    allowlist = frozenset(provenance.get("known_index_header_404_accessions", []))
    if allowlist != EXPECTED_R7_INDEX_404_ACCESSIONS:
        raise ReviewError("R7_INDEX_404_ALLOWLIST_CHANGED")

    route_counts: dict[str, int] = {}
    date_change_observed = 0
    date_change_equal = 0
    date_change_different = 0
    case_assessments: list[dict[str, Any]] = []
    r7_two_route_exceptions: set[str] = set()

    for case in sorted(cases, key=lambda item: item["accession"]):
        accession = case["accession"]
        for flag in ("identity_fields_consistent", "header_filing_date_routes_agree", "acceptance_routes_agree"):
            if case.get(flag) is not True:
                raise ReviewError(f"CASE_SOURCE_VALIDATION_FAILED:{accession}:{flag}")

        bulk_date = case.get("bulk_filing_date")
        header_date = case.get("edgar_header_filing_date")
        acceptance = case.get("acceptance_datetime")
        if not isinstance(bulk_date, str) or not isinstance(header_date, str) or bulk_date == header_date:
            raise ReviewError(f"CASE_DATE_MISMATCH_MISSING:{accession}")
        if not isinstance(acceptance, str) or not acceptance:
            raise ReviewError(f"CASE_ACCEPTANCE_DATETIME_MISSING:{accession}")

        successful_routes = case.get("successful_header_route_count")
        route_key = str(successful_routes)
        if route_key not in EXPECTED_ROUTE_COUNTS:
            raise ReviewError(f"CASE_ROUTE_COUNT_INVALID:{accession}")
        route_counts[route_key] = route_counts.get(route_key, 0) + 1

        if successful_routes == 2 and case.get("source_evidence") == "R7_BOUNDED_THREE_ROUTE_CAPTURE":
            r7_two_route_exceptions.add(accession)

        observed = case.get("date_change_observed")
        date_change_value = case.get("date_of_filing_date_change")
        if observed is True:
            date_change_observed += 1
            if not isinstance(date_change_value, str) or not date_change_value:
                raise ReviewError(f"OBSERVED_DATE_CHANGE_VALUE_MISSING:{accession}")
            if case.get("date_change_routes_agree_where_observed") is not True:
                raise ReviewError(f"DATE_CHANGE_ROUTE_CONFLICT:{accession}")
            if date_change_value == header_date:
                date_change_equal += 1
            else:
                date_change_different += 1
        elif observed is False:
            if date_change_value is not None:
                raise ReviewError(f"UNOBSERVED_DATE_CHANGE_HAS_VALUE:{accession}")
        else:
            raise ReviewError(f"DATE_CHANGE_OBSERVATION_FLAG_INVALID:{accession}")

        case_assessments.append({
            "accession": accession,
            "source_evidence": case.get("source_evidence"),
            "bulk_filing_date": bulk_date,
            "edgar_header_filing_date": header_date,
            "acceptance_datetime": acceptance,
            "identity_verified": True,
            "header_routes_agree": True,
            "acceptance_routes_agree": True,
            "successful_header_route_count": successful_routes,
            "date_change_observed": observed,
            "date_of_filing_date_change": date_change_value,
        })

    if r7_two_route_exceptions != EXPECTED_R7_INDEX_404_ACCESSIONS:
        raise ReviewError("R7_TWO_ROUTE_EXCEPTION_SET_INVALID")
    if route_counts != EXPECTED_ROUTE_COUNTS:
        raise ReviewError("HEADER_ROUTE_AGGREGATE_INVALID")
    if (date_change_observed, date_change_equal, date_change_different) != (17, 2, 15):
        raise ReviewError("DATE_CHANGE_AGGREGATE_INVALID")

    expected_counts = {
        "frozen_unresolved_accessions": 53,
        "frozen_date_mismatch_accessions": 36,
        "frozen_identity_conflict_accessions": 7,
        "frozen_complete_submission_http_404": 10,
        "unique_source_verified_date_mismatch_rows": 36,
        "bulk_filing_date_differs_from_edgar_header_date": 36,
        "identity_fields_validated": 36,
        "acceptance_datetime_present_and_cross_route_consistent": 36,
        "date_change_observed_rows": 17,
        "date_change_equals_edgar_header_date_where_observed": 2,
        "date_change_differs_from_edgar_header_date_where_observed": 15,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            raise ReviewError(f"SOURCE_RECEIPT_COUNT_MISMATCH:{key}")

    if provenance.get("offline_source_requests_made") != 0:
        raise ReviewError("OFFLINE_REVIEW_SOURCE_REQUEST_COUNT_NONZERO")
    if provenance.get("source_capture_receipt_modified") is not False:
        raise ReviewError("ORIGINAL_CAPTURE_RECEIPT_WAS_MODIFIED")
    cross_arch = receipt.get("cross_arch_reproduction", {})
    x64_fingerprint = cross_arch.get("x64_analysis_fingerprint")
    arm64_fingerprint = cross_arch.get("arm64_analysis_fingerprint")
    if (
        cross_arch.get("same_analysis_fingerprint") is not True
        or not x64_fingerprint
        or x64_fingerprint != arm64_fingerprint
        or cross_arch.get("network_requests_made_on_arm64") != 0
    ):
        raise ReviewError("CROSS_ARCH_REPRODUCTION_INVALID")

    for flag in REQUIRED_FALSE_INTERPRETATION_FLAGS:
        if interpretation.get(flag) is not False:
            raise ReviewError(f"NON_AUTHORIZING_SCOPE_FLAG_INVALID:{flag}")
    if safety.get("paper_only") is not True:
        raise ReviewError("PAPER_ONLY_INVARIANT_INVALID")
    for flag in ("live_trading_enabled", "orders_enabled", "automatic_promotion",
                 "performance_authorization", "holdout_selection", "ranking", "tuning",
                 "promotion", "live_execution"):
        if safety.get(flag) is not False:
            raise ReviewError(f"SAFETY_FLAG_INVALID:{flag}")
    if safety.get("paid_api_budget_usd") != 0:
        raise ReviewError("PAID_API_BUDGET_MUST_REMAIN_ZERO")

    return {
        "schema_version": 1,
        "record_type": "q104_i19_residual_policy_independent_admissibility_review",
        "candidate_id": "Q104:I19",
        "review_status": "INDEPENDENT_REVIEW_COMPLETE",
        "disposition": "NON_DESTRUCTIVE_RESEARCH_REPRESENTATION_ADMISSIBLE_PRODUCTION_PRECEDENCE_NOT_AUTHORIZED",
        "reviewed_repository": "DWR-debug/trading-agent-public",
        "reviewed_master_sha": "9e08d2366142f653dcd30311ff7fc6cf0155f0c3",
        "input_evidence": {
            "path": "research/evidence/q104_i19_residual_policy_applicability_latest.json",
            "receipt_fingerprint": receipt.get("receipt_fingerprint"),
            "analysis_fingerprint": x64_fingerprint,
            "source_capture_run_id": provenance.get("source_capture_run_id"),
            "source_capture_receipt_fingerprint": provenance.get("source_capture_receipt_fingerprint"),
            "source_capture_head_sha": provenance.get("source_capture_head_sha"),
        },
        "counts": {
            "verified_date_mismatch_cases": EXPECTED_DATE_MISMATCH_COUNT,
            "exact_identity_validations": EXPECTED_DATE_MISMATCH_COUNT,
            "cross_route_header_date_agreement": EXPECTED_DATE_MISMATCH_COUNT,
            "acceptance_datetime_present_and_cross_route_consistent": EXPECTED_DATE_MISMATCH_COUNT,
            "bulk_date_differs_from_edgar_header_date": EXPECTED_DATE_MISMATCH_COUNT,
            "successful_header_route_counts_by_case": route_counts,
            "r7_allowlisted_index_header_404_cases": len(r7_two_route_exceptions),
            "identity_conflicts_excluded": counts["frozen_identity_conflict_accessions"],
            "complete_submission_404_cases_excluded": counts["frozen_complete_submission_http_404"],
            "date_change_observed_rows": date_change_observed,
            "date_change_equals_edgar_header_date": date_change_equal,
            "date_change_differs_from_edgar_header_date": date_change_different,
        },
        "case_assessments": case_assessments,
        "decision": {
            "admissible_scope": "NON_DESTRUCTIVE_RESEARCH_SIDE_CAR_ONLY",
            "production_field_precedence_authorized": False,
            "production_join_change_authorized": False,
            "acceptance_datetime_is_first_public_observation_clock": False,
            "historical_pit_authorized": False,
            "scientific_evidence_created": False,
            "performance_authorized": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
            "field_treatment": {
                "bulk_filing_date": "Preserve the frozen bulk value unchanged as source provenance.",
                "edgar_header_filing_date": "Keep as a separate, source-qualified header field and record the discrepancy; do not overwrite the bulk value.",
                "acceptance_datetime": "Keep as a separate EDGAR acceptance event clock only; its presence does not prove when the filing first became publicly observable.",
                "date_of_filing_date_change": "Keep as separate post-acceptance metadata; do not substitute it for the filing date or acceptance timestamp.",
                "arithmetic_or_imputation": "None: no date shifting, timezone arithmetic, imputation, blanket correction, or automatic override.",
            },
            "reasoning": [
                "All 36 frozen date-mismatch cases pass accession/CIK/form identity checks, header filing-date agreement, acceptance-datetime agreement, and non-null date-difference checks in the source receipt.",
                "The evidence is sufficient to admit a non-destructive, provenance-preserving research-sidecar representation for this exact frozen subset only.",
                "DATE-OF-FILING-DATE-CHANGE is heterogeneous in the observed subset: 15 of 17 observed values differ from the EDGAR header filing date and 2 equal it. It is not an interchangeable substitute field.",
                "The known four R7 index-header 404 cases remain limited to the exact frozen allowlist and pass the recorded two-route identity/date/acceptance agreement exception.",
                "Header acceptance metadata is not evidence of the historical first-public-observation boundary. PIT/acceptance-time gates and any production field precedence therefore remain blocked.",
                "The seven CIK/form identity conflicts and ten complete-submission HTTP 404 records remain outside this review; no conclusion is extended to those branches.",
            ],
            "gates": {
                "exact_36_row_identity_and_date_consistency": "PASS_FOR_NON_DESTRUCTIVE_RESEARCH_REPRESENTATION",
                "known_r7_index_404_exception_scope": "PASS_EXACT_FROZEN_ALLOWLIST_ONLY",
                "date_of_filing_date_change_as_substitute": "REJECTED",
                "historical_first_public_observation": "BLOCKED_NOT_PROVEN",
                "production_field_precedence": "NOT_AUTHORIZED",
                "production_join": "NOT_AUTHORIZED",
                "performance_holdout_ranking_tuning_promotion_live_execution": "BLOCKED",
            },
        },
        "external_semantics_reference": {
            "url": "https://www.sec.gov/about/webmaster-frequently-asked-questions",
            "authority": "SEC EDGAR Webmaster FAQ",
            "definitions_consulted": {
                "FILED_AS_OF_DATE": "EDGAR-assigned official filing date, or post-acceptance new filing date for a post-acceptance correction.",
                "DATE_AS_OF_CHANGE": "Date when the last post-acceptance occurred.",
                "ACCEPTANCE_DATETIME": "Date/time the submission was accepted by EDGAR.",
            },
            "limitation": "These definitions do not themselves establish historical first-public-observation time or authorize overwriting the original bulk-dataset field.",
        },
        "review_execution": {
            "source_network_requests": 0,
            "source_receipt_modified": False,
            "field_precedence_applied": False,
            "production_join_changed": False,
            "census_restarted": False,
            "acceptance_time_gate_cleared": False,
            "historical_archive_gate_cleared": False,
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        receipt = json.loads(args.input.read_text(encoding="utf-8"))
        review = build_review(receipt)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(review, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError, ReviewError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "review_status": review["review_status"],
        "disposition": review["disposition"],
        "verified_date_mismatch_cases": review["counts"]["verified_date_mismatch_cases"],
        "production_field_precedence_authorized": review["decision"]["production_field_precedence_authorized"],
        "historical_pit_authorized": review["decision"]["historical_pit_authorized"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
