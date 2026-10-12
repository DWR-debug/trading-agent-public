from pathlib import Path

from automation.q220_receipt_chain import evaluate_q220_receipt_chain


ROOT = Path(__file__).resolve().parents[1]


def test_current_q220_receipt_chain_fails_closed_on_latest_negative_compiler_receipt():
    import json

    state = evaluate_q220_receipt_chain(ROOT)
    compiler = json.loads((ROOT / "research/evidence/q220_historical_representation_pit_latest.json").read_text(encoding="utf-8"))

    assert state["population_positive"] is True
    assert state["compiler_positive"] is False
    assert state["independent_positive"] is False
    assert state["current_milestone"] == "Historical prefix / representation-gap PIT compiler"
    assert state["current_milestone_status"] == "blocked"
    assert state["record_count"] == 55
    assert state["no_textblock_observed_count"] is None
    assert state["scientific_evidence"] is False
    assert state["performance_authorization_allowed"] is False
    assert compiler["status"] == "Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED"
    assert compiler["gate_positive"] is False
    assert compiler["source_hash_failure_count"] == 55
    assert state["compiler_receipt_fingerprint"] == compiler["receipt_fingerprint"]
    assert state["next_gate"] == compiler["next_gate"]
    assert "repair source hash mismatches" in state["next_gate"]
def test_q220_receipt_chain_fails_closed_when_current_source_files_are_missing(tmp_path):
    state = evaluate_q220_receipt_chain(tmp_path)

    assert state["population_positive"] is False
    assert state["compiler_positive"] is False
    assert state["independent_positive"] is False
    assert state["current_milestone_status"] == "blocked"
    assert state["performance_authorization_allowed"] is False
