"""Regression tests for the long-run Windows capacity policy and Copilot queue handling."""
from pathlib import Path


def test_long_q121r6_reproduction_has_priority_over_background_pc() -> None:
    permanent = Path(".github/workflows/permanent-pc-research-loop.yml").read_text(encoding="utf-8")
    long_run = Path(".github/workflows/q121r6-windows-independent-reproduction.yml").read_text(encoding="utf-8")
    assert "lane: local_reproduction" in permanent
    assert "concurrency_group: trading-agent-windows-research-capacity-v1" in permanent
    assert "lane: data_qa" in permanent
    assert "concurrency_group: trading-agent-windows-research-data-qa-v1" in permanent
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


def test_t052_allows_ai_credit_operational_plan_in_master_move_guard() -> None:
    text = Path(".github/workflows/t052-exact-master-ci-gate.yml").read_text(encoding="utf-8")
    assert "ops/ai_credit_availability_plan.json" in text
    assert "case \"$path\" in" in text


def test_q121r6_now_uses_three_windows_shards_for_third_runner() -> None:
    text = Path(".github/workflows/q121r6-windows-independent-reproduction.yml").read_text(encoding="utf-8")
    assert "max-parallel: 3" in text
    assert "shard_index: [0, 1, 2]" in text
    assert "--shard-count 3" in text
    assert "expected 3 receipts" in text
    assert "{0, 1, 2}" in text


def test_runner_c_setup_is_secrets_safe_and_has_dedicated_label() -> None:
    setup = Path("scripts/setup_third_windows_runner.ps1").read_text(encoding="utf-8")
    assert "LHT-N133732-3" in setup
    assert "trading-agent-long" in setup
    assert "registration-token" in setup
    assert "$token = $null" in setup
    doc = Path("docs/SELF_HOSTED_RESEARCH_RUNNER_C.md").read_text(encoding="utf-8")
    assert "third PowerShell window" in doc
    assert "non-authorizing" in doc.lower()
