import copy
import json
from pathlib import Path

import pytest

from automation.build_q104_i19_residual_filing_date_sidecar import (
    SidecarError,
    build_sidecar,
)
from automation.project_integrity_check import ROOT


SOURCE_PATH = ROOT / "research/evidence/q104_i19_residual_policy_applicability_latest.json"
REVIEW_PATH = ROOT / "research/evidence/q104_i19_residual_policy_independent_admissibility_review_latest.json"
SIDECAR_PATH = ROOT / "research/evidence/q104_i19_residual_filing_date_sidecar_latest.json"


@pytest.fixture
def inputs():
    return (
        json.loads(SOURCE_PATH.read_text(encoding="utf-8")),
        json.loads(REVIEW_PATH.read_text(encoding="utf-8")),
    )


def test_checked_in_sidecar_matches_deterministic_rebuild(inputs):
    source, review = inputs
    expected = build_sidecar(source, review)
    actual = json.loads(SIDECAR_PATH.read_text(encoding="utf-8"))
    assert actual == expected


def test_exact_36_rows_preserve_bulk_date_and_keep_clocks_separate(inputs):
    source, review = inputs
    sidecar = build_sidecar(source, review)

    assert sidecar["status"] == "RESEARCH_SIDECAR_READY_NON_PRODUCTION"
    assert sidecar["scope"] == "EXACT_36_FROZEN_SOURCE_VERIFIED_DATE_MISMATCH_CASES_ONLY"
    assert sidecar["counts"]["rows"] == 36
    assert sidecar["counts"]["date_mismatches"] == 36
    assert sidecar["counts"]["identity_validations"] == 36
    assert sidecar["counts"]["header_filing_date_cross_route_agreement"] == 36
    assert sidecar["counts"]["acceptance_datetime_cross_route_agreement"] == 36
    assert sidecar["counts"]["successful_header_route_counts_by_case"] == {"2": 5, "3": 31}
    assert sidecar["counts"]["r7_allowlisted_index_header_404_cases"] == 4
    assert sidecar["counts"]["frozen_unresolved_accessions_total"] == 53
    assert sidecar["counts"]["identity_conflict_accessions_excluded"] == 7
    assert sidecar["counts"]["complete_submission_http_404_accessions_excluded"] == 10
    assert sidecar["counts"]["date_change_observed"] == 17
    assert sidecar["counts"]["date_change_equals_header_date"] == 2
    assert sidecar["counts"]["date_change_differs_from_header_date"] == 15
    assert sidecar["counts"]["date_change_not_observed"] == 19

    source_by_accession = {row["accession"]: row for row in source["date_mismatch_cases"]}
    assert len(sidecar["rows"]) == 36
    for row in sidecar["rows"]:
        frozen = source_by_accession[row["accession"]]
        assert row["bulk_filing_date"] == frozen["bulk_filing_date"]
        assert row["edgar_header_filing_date"] == frozen["edgar_header_filing_date"]
        assert row["bulk_filing_date_provenance"] == "FROZEN_BULK_DATASET_VALUE_UNMODIFIED"
        assert row["filing_date_discrepancy"] is True
        assert row["filing_date_discrepancy_method"] == "STRING_VALUE_COMPARISON_ONLY_NO_DATE_ARITHMETIC"
        assert row["acceptance_datetime_semantics"] == "EDGAR_ACCEPTANCE_EVENT_ONLY_NOT_FIRST_PUBLIC_OBSERVATION"
        assert row["identity_fields_consistent"] is True
        assert row["header_filing_date_routes_agree"] is True
        assert row["acceptance_routes_agree"] is True


def test_date_change_field_is_not_substituted_for_filing_or_acceptance_clock(inputs):
    source, review = inputs
    sidecar = build_sidecar(source, review)
    observed = [row for row in sidecar["rows"] if row["date_change_observed"]]
    assert len(observed) == 17
    assert sum(row["date_change_relation_to_edgar_header_date"] == "EQUALS_EDGAR_HEADER_DATE" for row in observed) == 2
    assert sum(row["date_change_relation_to_edgar_header_date"] == "DIFFERS_FROM_EDGAR_HEADER_DATE" for row in observed) == 15
    assert all(row["date_change_routes_agree_where_observed"] is True for row in observed)
    assert sidecar["field_semantics"]["date_of_filing_date_change"].startswith("Separate post-acceptance metadata")


def test_sidecar_rejects_mutated_source_receipt_or_review(inputs):
    source, review = inputs
    mutated_source = copy.deepcopy(source)
    mutated_source["date_mismatch_cases"][0]["bulk_filing_date"] = "2099-01-01"
    with pytest.raises(SidecarError):
        build_sidecar(mutated_source, review)

    mutated_review = copy.deepcopy(review)
    mutated_review["decision"]["production_field_precedence_authorized"] = True
    with pytest.raises(SidecarError):
        build_sidecar(source, mutated_review)


def test_sidecar_never_authorizes_production_or_pit(inputs):
    source, review = inputs
    sidecar = build_sidecar(source, review)
    guardrails = sidecar["guardrails"]
    assert guardrails["bulk_filing_dates_overwritten"] is False
    assert guardrails["source_receipt_modified"] is False
    assert guardrails["independent_review_receipt_modified"] is False
    assert guardrails["source_network_requests"] == 0
    assert guardrails["census_restarted"] is False
    assert guardrails["production_field_precedence_applied"] is False
    assert guardrails["production_field_precedence_authorized"] is False
    assert guardrails["production_join_changed"] is False
    assert guardrails["production_join_change_authorized"] is False
    assert guardrails["historical_first_public_observation_proven"] is False
    assert guardrails["historical_pit_authorized"] is False
    assert guardrails["scientific_evidence_created"] is False
    assert guardrails["performance_authorized"] is False
    assert guardrails["holdout_selection"] is False
    assert guardrails["ranking"] is False
    assert guardrails["tuning"] is False
    assert guardrails["promotion"] is False
    assert guardrails["live_execution"] is False
    assert guardrails["paper_only"] is True
    assert guardrails["live_trading_enabled"] is False
    assert guardrails["orders_enabled"] is False
    assert guardrails["automatic_promotion"] is False
    assert guardrails["paid_api_budget_usd"] == 0
