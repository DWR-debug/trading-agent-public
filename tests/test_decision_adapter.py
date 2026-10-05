from __future__ import annotations

import pytest

from agent_runtime.decision_adapter import (
    adapt_record,
    intent_fingerprint,
    packet_from_record,
)
from agent_runtime.paper_intent import PaperIntentError


def _record(**overrides):
    row = {
        "candidate_id": "FROZEN-01",
        "symbol": "SPY",
        "decision_time_utc": "2026-10-05T12:00:00Z",
        "market_observation_time_utc": "2026-10-05T11:59:00Z",
        "input_fingerprint": "input-fp",
        "decision_fingerprint": "decision-fp",
        "target_exposure": 0.50,
    }
    row.update(overrides)
    return row


def test_adapter_accepts_only_frozen_decision_contract():
    intent = adapt_record(_record())
    assert intent.execution_route == "paper_shadow"
    assert intent.target_exposure == 0.50
    assert len(intent_fingerprint(intent)) == 64


@pytest.mark.parametrize(
    "forbidden",
    [
        "holdout_return",
        "pnl",
        "candidate_rank",
        "parameter_search",
        "promotion_decision",
    ],
)
def test_outcome_and_search_fields_are_rejected(forbidden):
    with pytest.raises(PaperIntentError):
        adapt_record(_record(**{forbidden: 1}))


def test_unknown_field_is_rejected():
    with pytest.raises(PaperIntentError):
        adapt_record(_record(extra_field="not-permitted"))


def test_missing_required_field_is_rejected():
    row = _record()
    del row["decision_fingerprint"]
    with pytest.raises(PaperIntentError):
        packet_from_record(row)


def test_safety_flags_are_inherited_and_fail_closed():
    with pytest.raises(PaperIntentError):
        adapt_record(_record(orders_enabled=True))
