from __future__ import annotations

import json

import pytest

from agent_runtime.paper_intent import PaperIntent
from agent_runtime.shadow_coordinator import PaperShadowCoordinator, ShadowCoordinatorError
from agent_runtime.shadow_event_replay import validate_shadow_event_replay
from agent_runtime.shadow_ledger import PaperShadowIntentLedger
from risk.portfolio_controller import PortfolioRiskController, RiskError


def _intent(symbol: str, time: str, fp: str = "a") -> PaperIntent:
    return PaperIntent(
        candidate_id="Q-TEST-FROZEN",
        symbol=symbol,
        decision_time_utc=time,
        input_fingerprint="input-" + fp,
        decision_fingerprint="decision-" + fp,
        target_exposure=0.5,
    )


def test_valid_intent_is_admitted_without_order_capability():
    coordinator = PaperShadowCoordinator(PortfolioRiskController(2000.0))
    event = coordinator.admit(_intent("SPY", "2026-10-05T12:00:00Z"))
    assert event.event_type == "SHADOW_INTENT_ACCEPTED"
    assert coordinator.export()[0]["live_execution"] is False
    assert not hasattr(coordinator, "submit_order")


def test_time_regression_is_rejected_globally():
    coordinator = PaperShadowCoordinator(PortfolioRiskController(2000.0))
    coordinator.admit(_intent("SPY", "2026-10-05T12:05:00Z", "a"))
    with pytest.raises(PaperIntentError) as exc_info:
        coordinator.admit(_intent("QQQ", "2026-10-05T12:00:00Z", "b"))
    assert "moved backwards" in str(exc_info.value)


def test_kill_switch_blocks_shadow_admission():
    risk = PortfolioRiskController(2000.0)
    with pytest.raises(RiskError):
        risk.update_equity(1984.0)
    assert risk.kill_switch is True

    coordinator = PaperShadowCoordinator(risk)
    with pytest.raises(RiskError):
        coordinator.admit(_intent("SPY", "2026-10-05T12:00:00Z"))


def test_event_export_is_provenance_bearing_and_non_authorizing():
    coordinator = PaperShadowCoordinator(PortfolioRiskController(2000.0))
    event = coordinator.admit(_intent("SPY", "2026-10-05T12:00:00Z"))
    exported = coordinator.export()
    assert exported[0]["intent_fingerprint"] == event.intent_fingerprint
    assert len(exported[0]["event_fingerprint"]) == 64
    assert exported[0]["scientific_evidence"] is False
    assert exported[0]["performance_authorization"] is False
    assert exported[0]["promotion"] is False
    assert exported[0]["live_execution"] is False


def test_coordinator_writes_accepted_intents_to_canonical_ledger(tmp_path):
    ledger = PaperShadowIntentLedger()
    coordinator = PaperShadowCoordinator(PortfolioRiskController(2000.0), ledger)
    coordinator.admit(_intent("SPY", "2026-10-05T12:00:00Z", "a"))
    coordinator.admit(_intent("QQQ", "2026-10-05T12:01:00Z", "b"))

    assert len(coordinator.ledger.intents) == 2
    assert coordinator.ledger.intents[0].symbol == "SPY"
    assert coordinator.ledger.intents[1].symbol == "QQQ"

    path = tmp_path / "ledger.json"
    persisted = coordinator.persist_ledger(path)
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["chain_fingerprint"] == stored["chain_fingerprint"]
    assert stored["count"] == 2
    assert stored["live_execution"] is False


def test_shadow_event_replay_is_deterministic_and_detects_tampering():
    coordinator = PaperShadowCoordinator(PortfolioRiskController(2000.0))
    coordinator.admit(_intent("SPY", "2026-10-05T12:00:00Z", "a"))
    coordinator.admit(_intent("QQQ", "2026-10-05T12:01:00Z", "b"))

    exported = coordinator.export()
    first = validate_shadow_event_replay(exported)
    second = validate_shadow_event_replay(exported)

    assert first == second
    assert first.count == 2
    assert first.event_chain_fingerprint == coordinator.event_chain_fingerprint()

    tampered = json.loads(json.dumps(exported))
    tampered[0]["target_exposure"] = 0.75
    with pytest.raises(ShadowCoordinatorError, match="fingerprint mismatch"):
        validate_shadow_event_replay(tampered)


def test_shadow_event_replay_rejects_authorizing_flags():
    coordinator = PaperShadowCoordinator(PortfolioRiskController(2000.0))
    coordinator.admit(_intent("SPY", "2026-10-05T12:00:00Z"))
    exported = coordinator.export()
    exported[0]["promotion"] = True
    with pytest.raises(ShadowCoordinatorError):
        validate_shadow_event_replay(exported)
