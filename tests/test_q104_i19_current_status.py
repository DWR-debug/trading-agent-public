import copy
import json
from pathlib import Path

from automation.sync_current_operational_status import (
    generate,
    q104_i19_independent_admissibility_status,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "research/evidence/q104_i19_residual_policy_applicability_latest.json"
REVIEW_PATH = ROOT / "research/evidence/q104_i19_residual_policy_independent_admissibility_review_latest.json"


def _inputs():
    return (
        json.loads(SOURCE_PATH.read_text(encoding="utf-8")),
        json.loads(REVIEW_PATH.read_text(encoding="utf-8")),
    )


def test_q104_independent_admissibility_is_surfaced_by_generated_status():
    payload, doc = generate(
        source_master_sha="abc123",
        workflow_run_id=None,
        github_state_path=None,
    )
    state = payload["q104_i19_independent_admissibility_review"]
    focus = payload["chat_handoff"]["next_research_focus"]

    assert state["review_status"] == "INDEPENDENT_REVIEW_COMPLETE"
    assert state["admissible_scope"] == "NON_DESTRUCTIVE_RESEARCH_SIDE_CAR_ONLY"
    assert state["verified_date_mismatch_cases"] == 36
    assert state["exact_identity_validations"] == 36
    assert state["successful_header_route_counts_by_case"] == {"2": 5, "3": 31}
    assert state["r7_allowlisted_index_header_404_cases"] == 4
    assert state["identity_conflicts_excluded"] == 7
    assert state["complete_submission_404_cases_excluded"] == 10
    assert state["date_change_observed_rows"] == 17
    assert state["date_change_equals_edgar_header_date"] == 2
    assert state["date_change_differs_from_edgar_header_date"] == 15
    assert "Q104:I19 independent admissibility review [PR #1484] is current" in focus
    assert "Production precedence/joins" in focus and "remain blocked" in focus
    assert "first-public-time clearance" in focus
    assert "full residual set: the 36 verified date-mismatch rows are admissible only for a non-destructive sidecar" in focus
    assert "Q104:I19 independent admissibility review [PR #1484] is current" in doc
    assert state["production_field_precedence_authorized"] is False
    assert state["production_join_change_authorized"] is False
    assert state["historical_pit_authorized"] is False
    assert state["performance_authorized"] is False
    assert state["holdout_selection"] is False
    assert state["ranking"] is False
    assert state["tuning"] is False
    assert state["promotion"] is False
    assert state["live_execution"] is False


def test_q104_status_fails_closed_when_source_receipt_fingerprint_is_stale():
    source, review = _inputs()
    altered_source = copy.deepcopy(source)
    altered_source["receipt_fingerprint"] = "f" * 64

    status = q104_i19_independent_admissibility_status(review, altered_source)

    assert status["review_status"] == "REVIEW_MISSING_STALE_OR_INVALID"
    assert status.get("admissible_scope") is None
    assert status["production_field_precedence_authorized"] is False
    assert status["historical_pit_authorized"] is False
    assert "all historical PIT" in status["summary"]


def test_q104_status_fails_closed_when_review_attempts_to_authorize_production():
    source, review = _inputs()
    altered_review = copy.deepcopy(review)
    altered_review["decision"]["production_field_precedence_authorized"] = True

    status = q104_i19_independent_admissibility_status(altered_review, source)

    assert status["review_status"] == "REVIEW_MISSING_STALE_OR_INVALID"
    assert status["production_field_precedence_authorized"] is False
    assert status["production_join_change_authorized"] is False
    assert status["historical_pit_authorized"] is False


def test_q104_status_fails_closed_if_any_row_no_longer_matches_the_review():
    source, review = _inputs()
    altered_review = copy.deepcopy(review)
    altered_review["case_assessments"][0]["edgar_header_filing_date"] = "2099-01-01"

    status = q104_i19_independent_admissibility_status(altered_review, source)

    assert status["review_status"] == "REVIEW_MISSING_STALE_OR_INVALID"
    assert status["verified_date_mismatch_cases"] == 0
    assert status["production_field_precedence_authorized"] is False
