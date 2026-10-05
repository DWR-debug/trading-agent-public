from __future__ import annotations

import pytest

from agent_runtime.paper_intent import PaperIntent
from agent_runtime.shadow_coordinator import PaperShadowCoordinator, ShadowCoordinatorError
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


def test_time_regression_is_rejected_per_symbol():
    coordinator = PaperShadowCoordinator(PortfolioRiskController(2000.0))
    coordinator.admit(_intent("SPY", "2026-10-05T12:05:00Z", "a"))
    with pytest.raises(ShadowCoordinatorError):
        coordinator.admit(_intent("SPY", "2026-10-05T12:00:00Z", "b"))


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
