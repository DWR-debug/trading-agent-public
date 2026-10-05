from __future__ import annotations

import json

import pytest

from agent_runtime.paper_intent import PaperIntent, PaperIntentError
from agent_runtime.shadow_ledger import PaperShadowIntentLedger


def _intent(time: str, key: str) -> PaperIntent:
    return PaperIntent(
        candidate_id="Q-FROZEN",
        symbol="SPY",
        decision_time_utc=time,
        input_fingerprint="input-" + key,
        decision_fingerprint="decision-" + key,
        target_exposure=0.25,
    )


def test_append_only_ledger_tracks_fingerprint_chain(tmp_path):
    ledger = PaperShadowIntentLedger()
    ledger.append(_intent("2026-10-05T12:00:00Z", "a"))
    receipt = ledger.append(_intent("2026-10-05T12:05:00Z", "b"))
    assert receipt.count == 2
    assert len(receipt.chain_fingerprint) == 64

    path = tmp_path / "ledger.json"
    payload = ledger.persist(path)
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["chain_fingerprint"] == payload["chain_fingerprint"]
    assert payload["scientific_evidence"] is False
    assert payload["live_execution"] is False


def test_duplicate_intent_is_rejected():
    ledger = PaperShadowIntentLedger()
    item = _intent("2026-10-05T12:00:00Z", "a")
    ledger.append(item)
    with pytest.raises(PaperIntentError):
        ledger.append(item)


def test_time_reversal_is_rejected():
    ledger = PaperShadowIntentLedger()
    ledger.append(_intent("2026-10-05T12:05:00Z", "a"))
    with pytest.raises(PaperIntentError):
        ledger.append(_intent("2026-10-05T12:00:00Z", "b"))
