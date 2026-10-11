from pathlib import Path

from automation.q220_receipt_chain import evaluate_q220_receipt_chain


ROOT = Path(__file__).resolve().parents[1]


def test_current_q220_source_pit_receipt_chain_is_positive_without_performance_authority():
    state = evaluate_q220_receipt_chain(ROOT)

    assert state["population_positive"] is True
    assert state["compiler_positive"] is True
    assert state["independent_positive"] is True
    assert state["current_milestone"] == "Bounded adversarial robustness review + formal trial-governance reconciliation"
    assert state["current_milestone_status"] == "ready"
    assert state["record_count"] == 55
    assert state["no_textblock_observed_count"] == 5
    assert state["scientific_evidence"] is False
    assert state["performance_authorization_allowed"] is False
    assert "no performance authorization" in state["next_gate"]


def test_q220_receipt_chain_fails_closed_when_current_source_files_are_missing(tmp_path):
    state = evaluate_q220_receipt_chain(tmp_path)

    assert state["population_positive"] is False
    assert state["compiler_positive"] is False
    assert state["independent_positive"] is False
    assert state["current_milestone_status"] == "blocked"
    assert state["performance_authorization_allowed"] is False
