import pytest

from research.evidence_contract import (
    EvidenceContractError,
    EvidenceSnapshot,
    GateResult,
    compare_evidence_versions,
    evaluate_evidence,
    merge_gate_results,
)


def snapshot(**overrides):
    values = {
        "trial_id": "T-TEST-001",
        "strategy_id": "fixed_candidate",
        "status": "VALIDATED_PASS",
        "artifact_id": 12345,
        "artifact_digest_sha256": "a" * 64,
        "report_fingerprint_sha256": "b" * 64,
        "manifest_fingerprint_sha256": "c" * 64,
        "code_commit_sha": "d" * 40,
        "research_count": 2798,
        "holdout_count": 700,
        "holdout_used_for_selection": False,
        "gates": (
            GateResult("research_dd", True),
            GateResult("rolling_pf", True),
            GateResult("holdout_pf", True),
        ),
    }
    values.update(overrides)
    return EvidenceSnapshot(**values)


def test_valid_snapshot_is_eligible():
    decision = evaluate_evidence(snapshot())
    assert decision.eligible is True
    assert decision.reason == "ALL_DECLARED_GATES_PASSED"
    assert decision.failed_gates == ()


def test_holdout_selection_is_always_blocked():
    decision = evaluate_evidence(snapshot(holdout_used_for_selection=True))
    assert decision.eligible is False
    assert decision.status == "BLOCKED"
    assert decision.reason == "HOLDOUT_USED_FOR_SELECTION"


def test_declared_gate_failure_blocks():
    decision = evaluate_evidence(
        snapshot(gates=(GateResult("research_dd", True), GateResult("rolling_pf", False)))
    )
    assert decision.eligible is False
    assert decision.status == "VALIDATED_FAIL"
    assert decision.failed_gates == ("rolling_pf",)


def test_non_pass_trial_status_cannot_be_promoted():
    decision = evaluate_evidence(snapshot(status="BLOCKED"))
    assert decision.eligible is False
    assert decision.reason == "TRIAL_NOT_VALIDATED_PASS"


def test_empty_gate_set_is_blocked():
    with pytest.raises(EvidenceContractError):
        snapshot(gates=())


def test_safety_contract_cannot_be_relaxed():
    with pytest.raises(EvidenceContractError):
        snapshot(live_trading_enabled=True)


def test_invalid_digest_is_rejected():
    with pytest.raises(EvidenceContractError):
        snapshot(report_fingerprint_sha256="not-a-digest")


def test_provenance_changes_are_explicit():
    previous = snapshot()
    current = snapshot(code_commit_sha="e" * 40, artifact_id=12346)
    changes = compare_evidence_versions(previous, current)
    assert changes == ("artifact_id", "code_commit_sha")


def test_missing_previous_evidence_is_explicit():
    assert compare_evidence_versions(None, snapshot()) == ("NO_PREVIOUS_EVIDENCE",)


def test_merge_gate_results_is_deterministic():
    gates = merge_gate_results({"zeta": True, "alpha": False})
    assert [gate.name for gate in gates] == ["alpha", "zeta"]
    assert [gate.passed for gate in gates] == [False, True]