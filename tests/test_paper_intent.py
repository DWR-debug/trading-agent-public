from __future__ import annotations

import pytest

from agent_runtime.paper_intent import (
    FrozenDecisionPacket,
    PaperIntentError,
    PaperOnlyAgentRuntime,
)


def _packet(**overrides):
    values = {
        "candidate_id": "FROZEN-CANDIDATE-01",
        "symbol": "SPY",
        "decision_time_utc": "2026-10-05T12:00:00Z",
        "market_observation_time_utc": "2026-10-05T11:59:59Z",
        "input_fingerprint": "input-fp",
        "decision_fingerprint": "decision-fp",
        "target_exposure": 0.25,
    }
    values.update(overrides)
    return FrozenDecisionPacket(**values)


def test_valid_packet_becomes_paper_shadow_intent():
    intent = PaperOnlyAgentRuntime().build_intent(_packet())

    assert intent.execution_route == "paper_shadow"
    assert intent.broker_order_supported is False
    assert intent.target_exposure == 0.25


@pytest.mark.parametrize(
    "field,value",
    [
        ("paper_only", False),
        ("live_trading_enabled", True),
        ("orders_enabled", True),
        ("automatic_promotion", True),
    ],
)
def test_safety_flags_fail_closed(field, value):
    with pytest.raises(PaperIntentError):
        PaperOnlyAgentRuntime().build_intent(_packet(**{field: value}))


def test_future_observation_cannot_be_used_for_decision():
    with pytest.raises(PaperIntentError):
        PaperOnlyAgentRuntime().build_intent(
            _packet(
                decision_time_utc="2026-10-05T11:59:59Z",
                market_observation_time_utc="2026-10-05T12:00:00Z",
            )
        )


@pytest.mark.parametrize("exposure", [-1.0001, 1.0001, float("inf")])
def test_target_exposure_bounds_are_fail_closed(exposure):
    with pytest.raises(PaperIntentError):
        PaperOnlyAgentRuntime().build_intent(_packet(target_exposure=exposure))


def test_missing_provenance_fails_closed():
    with pytest.raises(PaperIntentError):
        PaperOnlyAgentRuntime().build_intent(_packet(input_fingerprint=""))


def test_runtime_does_not_expose_a_broker_order_method():
    runtime = PaperOnlyAgentRuntime()
    assert not hasattr(runtime, "submit_order")
    assert not hasattr(runtime, "promote")
    assert not hasattr(runtime, "select_candidate")
