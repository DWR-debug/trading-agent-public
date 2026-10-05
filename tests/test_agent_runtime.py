from __future__ import annotations

from dataclasses import replace

import pytest

from agent.runtime import AgentRuntimeError, FrozenCandidate, TradingAgentRuntime
from config import settings


def candidate_payload() -> dict:
    return {
        "schema_version": 1,
        "frozen": True,
        "candidate_id": "TEST-CANDIDATE-V1",
        "freeze_ref": "test-freeze-v1",
        "initial_capital_eur": 2000.0,
        "risk_per_trade": 0.01,
        "leverage": 1.0,
        "fee_bps": 10.0,
        "slippage_bps": 5.0,
    }


def observations() -> list[dict]:
    return [
        {
            "timestamp": "2026-10-01T09:00:00+00:00",
            "closed": True,
            "close": 100.0,
        },
        {
            "timestamp": "2026-10-01T10:00:00+00:00",
            "closed": True,
            "close": 101.0,
        },
    ]


def test_frozen_candidate_contract_is_deterministic() -> None:
    candidate = FrozenCandidate.from_mapping(candidate_payload())
    assert candidate.fingerprint == FrozenCandidate.from_mapping(
        candidate_payload()
    ).fingerprint


def test_runtime_rejects_unfrozen_candidate() -> None:
    payload = candidate_payload()
    payload["frozen"] = False
    with pytest.raises(AgentRuntimeError, match="frozen=true"):
        FrozenCandidate.from_mapping(payload)


def test_runtime_rejects_excessive_leverage() -> None:
    payload = candidate_payload()
    payload["leverage"] = settings.MAX_LEVERAGE + 1
    with pytest.raises(AgentRuntimeError, match="leverage"):
        FrozenCandidate.from_mapping(payload)


def test_runtime_requires_closed_ordered_observations() -> None:
    candidate = FrozenCandidate.from_mapping(candidate_payload())
    runtime = TradingAgentRuntime(candidate, lambda rows: "HOLD")

    bad = observations()
    bad[1]["closed"] = False
    with pytest.raises(AgentRuntimeError, match="not explicitly marked closed"):
        runtime.decide(bad)


def test_runtime_requires_strict_timestamp_order() -> None:
    candidate = FrozenCandidate.from_mapping(candidate_payload())
    runtime = TradingAgentRuntime(candidate, lambda rows: "HOLD")

    bad = observations()
    bad[1]["timestamp"] = bad[0]["timestamp"]
    with pytest.raises(AgentRuntimeError, match="strictly increasing"):
        runtime.decide(bad)


def test_runtime_returns_paper_only_non_executable_envelope() -> None:
    candidate = FrozenCandidate.from_mapping(candidate_payload())
    runtime = TradingAgentRuntime(candidate, lambda rows: "BUY")
    decision = runtime.decide(observations())

    assert decision.action == "BUY"
    assert decision.paper_only is True
    assert decision.live_execution_enabled is False
    assert decision.orders_enabled is False
    assert decision.automatic_promotion is False
    assert decision.execution_allowed is False
    assert decision.research_authorization_consumed is False
    assert decision.candidate_id == candidate.candidate_id
    assert decision.candidate_fingerprint == candidate.fingerprint


def test_runtime_rejects_invalid_signal() -> None:
    candidate = FrozenCandidate.from_mapping(candidate_payload())
    runtime = TradingAgentRuntime(candidate, lambda rows: "MAYBE")
    with pytest.raises(AgentRuntimeError, match="Unsupported signal action"):
        runtime.decide(observations())


def test_runtime_never_exposes_live_execution_method() -> None:
    candidate = FrozenCandidate.from_mapping(candidate_payload())
    runtime = TradingAgentRuntime(candidate, lambda rows: "HOLD")
    assert not hasattr(runtime, "execute_live")


def test_cost_contract_is_frozen() -> None:
    candidate = FrozenCandidate.from_mapping(candidate_payload())
    assert candidate.fee_bps == 10.0
    assert candidate.slippage_bps == 5.0


def test_candidate_identity_changes_when_contract_changes() -> None:
    candidate = FrozenCandidate.from_mapping(candidate_payload())
    changed = replace(candidate, freeze_ref="test-freeze-v2")
    assert candidate.fingerprint != changed.fingerprint


def test_runtime_rejects_wrong_candidate_schema() -> None:
    payload = candidate_payload()
    payload["schema_version"] = 2
    with pytest.raises(AgentRuntimeError, match="schema_version=1"):
        FrozenCandidate.from_mapping(payload)


def test_decision_fingerprint_is_replay_deterministic() -> None:
    candidate = FrozenCandidate.from_mapping(candidate_payload())
    runtime = TradingAgentRuntime(candidate, lambda rows: "BUY")
    first = runtime.decide(observations())
    second = runtime.decide(observations())
    assert first.fingerprint == second.fingerprint
    assert first.observation_fingerprint == second.observation_fingerprint
    assert first.candidate_fingerprint == second.candidate_fingerprint
