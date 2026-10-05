from __future__ import annotations

import pytest

from agent_runtime.paper_intent import PaperIntent, PaperIntentError
from agent_runtime.shadow_replay import validate_replay


def _intent(time: str, fp: str) -> PaperIntent:
    return PaperIntent(
        candidate_id="FROZEN-01",
        symbol="SPY",
        decision_time_utc=time,
        input_fingerprint="input-" + fp,
        decision_fingerprint="decision-" + fp,
        target_exposure=0.25,
    )


def test_replay_is_deterministic_for_ordered_unique_intents():
    receipt = validate_replay(
        [
            _intent("2026-10-05T12:00:00Z", "a"),
            _intent("2026-10-05T12:05:00Z", "b"),
        ]
    )
    assert receipt.count == 2
    assert receipt.first_decision_time_utc.endswith("Z")
    assert len(receipt.intent_chain_fingerprint) == 64


def test_replay_rejects_duplicate_intents():
    item = _intent("2026-10-05T12:00:00Z", "a")
    with pytest.raises(PaperIntentError):
        validate_replay([item, item])


def test_replay_rejects_time_reversal():
    with pytest.raises(PaperIntentError):
        validate_replay(
            [
                _intent("2026-10-05T12:05:00Z", "a"),
                _intent("2026-10-05T12:00:00Z", "b"),
            ]
        )
