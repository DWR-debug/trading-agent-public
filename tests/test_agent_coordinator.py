import pytest

from portfolio.agent_coordinator import EvidenceGatedAgentCoordinator
from portfolio.market_state import MarketStateObservation, UnknownMarketStateObserver
from portfolio.strategy_allocator import StrategyAssessment


def valid_state() -> MarketStateObservation:
    return MarketStateObservation(
        state_id="TRENDING",
        confidence=0.8,
        validated=True,
        features={"trend_strength": 0.7},
        rationale="validated test state",
    )


def valid_assessment() -> StrategyAssessment:
    return StrategyAssessment(
        strategy_id="validated_strategy",
        evidence_eligible=True,
        suitability_score=1.0,
        signal_confidence=1.0,
    )


def test_unknown_observer_is_fail_closed():
    observation = UnknownMarketStateObserver().observe({"volatility": 0.9})
    assert observation.state_id == "UNKNOWN"
    assert observation.validated is False
    assert observation.confidence == pytest.approx(0.0)


def test_unvalidated_state_forces_cash_even_with_valid_strategy():
    observation = UnknownMarketStateObserver().observe()
    decision = EvidenceGatedAgentCoordinator().decide(
        observation,
        (valid_assessment(),),
    )
    assert decision.action == "HOLD_CASH"
    assert decision.allocation.strategy_exposure == {}
    assert decision.allocation.cash_exposure == pytest.approx(1.0)


def test_validated_state_allows_evidence_gated_allocation():
    decision = EvidenceGatedAgentCoordinator().decide(
        valid_state(),
        (valid_assessment(),),
    )
    assert decision.action == "ALLOCATE_STRATEGIES"
    assert decision.allocation.strategy_exposure["validated_strategy"] == pytest.approx(1.0)


def test_state_requires_valid_identifier_and_confidence_range():
    with pytest.raises(ValueError):
        MarketStateObservation("", 0.5, True, {}, "invalid")
    with pytest.raises(ValueError):
        MarketStateObservation("X", 1.5, True, {}, "invalid")