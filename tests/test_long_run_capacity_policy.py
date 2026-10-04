"""Regression tests for the long-run Windows capacity policy and Copilot queue handling."""
from pathlib import Path


def test_long_q121r6_reproduction_has_priority_over_background_pc() -> None:
    permanent = Path(".github/workflows/permanent-pc-research-loop.yml").read_text(encoding="utf-8")
    long_run = Path(".github/workflows/q121r6-windows-independent-reproduction.yml").read_text(encoding="utf-8")
    assert "trading-agent-windows-research-capacity-v1" in permanent
    assert "cancel-in-progress: false" in permanent
    assert "trading-agent-windows-research-capacity-v1" in long_run
    assert "cancel-in-progress: true" in long_run


def test_long_q121r6_reproduction_is_not_performance_evidence() -> None:
    text = Path(".github/workflows/q121r6-windows-independent-reproduction.yml").read_text(encoding="utf-8")
    assert "independent_reproduction_only':True" in text
    assert "formal_evidence_allowed':False" in text
    assert '"performance": False' in text
    assert '"promotion": False' in text
    assert '"live_execution": False' in text


def test_agent_queue_treats_copilot_exhaustion_as_pause_but_keeps_other_errors_closed() -> None:
    text = Path(".github/workflows/agent-request-queue.yml").read_text(encoding="utf-8")
    assert "continue-on-error: true" in text
    assert "id: copilot_budget_reconcile" in text
    assert "COPILOT_FREE_GATE_RECONCILE=EXHAUSTED" in text
    assert "Copilot Free gate failed and the protected budget is not provably exhausted; fail closed." in text
    assert "steps.copilot_budget.outcome == 'success'" in text
