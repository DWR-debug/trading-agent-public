import copy
import json
from pathlib import Path

import pytest

from automation.q104_i19_residual_policy_independent_review import (
    EXPECTED_R7_INDEX_404_ACCESSIONS,
    ReviewError,
    build_review,
)
from automation.project_integrity_check import ROOT


INPUT = ROOT / "research/evidence/q104_i19_residual_policy_applicability_latest.json"
OUTPUT = ROOT / "research/evidence/q104_i19_residual_policy_independent_admissibility_review_latest.json"


@pytest.fixture
def source_receipt():
    return json.loads(INPUT.read_text(encoding="utf-8"))


def test_checked_in_review_matches_recomputed_independent_audit(source_receipt):
    expected = build_review(source_receipt)
    actual = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert actual == expected


def test_review_covers_exactly_36_rows_and_keeps_unresolved_branches_separate(source_receipt):
    review = build_review(source_receipt)
    assert review["counts"]["verified_date_mismatch_cases"] == 36
    assert review["counts"]["exact_identity_validations"] == 36
    assert review["counts"]["cross_route_header_date_agreement"] == 36
    assert review["counts"]["acceptance_datetime_present_and_cross_route_consistent"] == 36
    assert review["counts"]["successful_header_route_counts_by_case"] == {"2": 5, "3": 31}
    assert review["counts"]["r7_allowlisted_index_header_404_cases"] == 4
    assert review["counts"]["identity_conflicts_excluded"] == 7
    assert review["counts"]["complete_submission_404_cases_excluded"] == 10
    assert review["counts"]["date_change_observed_rows"] == 17
    assert review["counts"]["date_change_equals_edgar_header_date"] == 2
    assert review["counts"]["date_change_differs_from_edgar_header_date"] == 15


def test_admissibility_is_sidecar_only_and_never_authorizes_precedence_or_pit(source_receipt):
    review = build_review(source_receipt)
    decision = review["decision"]
    assert decision["admissible_scope"] == "NON_DESTRUCTIVE_RESEARCH_SIDE_CAR_ONLY"
    assert decision["production_field_precedence_authorized"] is False
    assert decision["production_join_change_authorized"] is False
    assert decision["acceptance_datetime_is_first_public_observation_clock"] is False
    assert decision["historical_pit_authorized"] is False
    assert decision["scientific_evidence_created"] is False
    assert decision["performance_authorized"] is False
    assert decision["promotion"] is False
    assert decision["live_execution"] is False


def test_four_r7_two_route_exceptions_are_exactly_the_frozen_allowlist(source_receipt):
    review = build_review(source_receipt)
    r7_two_route = {
        row["accession"]
        for row in review["case_assessments"]
        if row["source_evidence"] == "R7_BOUNDED_THREE_ROUTE_CAPTURE"
        and row["successful_header_route_count"] == 2
    }
    assert r7_two_route == EXPECTED_R7_INDEX_404_ACCESSIONS


def test_rejects_identity_or_acceptance_route_disagreement(source_receipt):
    altered = copy.deepcopy(source_receipt)
    altered["date_mismatch_cases"][0]["acceptance_routes_agree"] = False
    with pytest.raises(ReviewError, match="CASE_SOURCE_VALIDATION_FAILED"):
        build_review(altered)


def test_rejects_allowlist_widening(source_receipt):
    altered = copy.deepcopy(source_receipt)
    altered["capture_provenance"]["known_index_header_404_accessions"].append("0000950123-15-003218")
    with pytest.raises(ReviewError, match="R7_INDEX_404_ALLOWLIST_CHANGED"):
        build_review(altered)


def test_rejects_any_production_or_research_gate_change(source_receipt):
    altered = copy.deepcopy(source_receipt)
    altered["interpretation_scope"]["field_precedence_applied"] = True
    with pytest.raises(ReviewError, match="NON_AUTHORIZING_SCOPE_FLAG_INVALID"):
        build_review(altered)


def test_rejects_mutated_date_change_aggregate(source_receipt):
    altered = copy.deepcopy(source_receipt)
    observed = next(case for case in altered["date_mismatch_cases"] if case["date_change_observed"] is True)
    observed["date_of_filing_date_change"] = observed["edgar_header_filing_date"]
    with pytest.raises(ReviewError, match="DATE_CHANGE_AGGREGATE_INVALID"):
        build_review(altered)
