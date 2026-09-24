import pytest

from portfolio.strategy_allocator import (
    EvidenceGatedStrategyAllocator,
    StrategyAllocationError,
    StrategyAssessment,
)


def assessment(strategy_id: str, eligible: bool = True, score: float = 1.0, max_exposure: float = 1.0):
    return StrategyAssessment(
        strategy_id=strategy_id,
        evidence_eligible=eligible,
        suitability_score=score,
        signal_confidence=1.0,
        max_exposure=max_exposure,
    )


def test_no_assessments_means_cash():
    decision = EvidenceGatedStrategyAllocator().allocate(())
    assert decision.strategy_exposure == {}
    assert decision.cash_exposure == pytest.approx(1.0)


def test_unvalidated_strategy_is_never_allocated():
    decision = EvidenceGatedStrategyAllocator().allocate(
        (assessment("unvalidated", eligible=False),)
    )
    assert decision.strategy_exposure == {}
    assert decision.cash_exposure == pytest.approx(1.0)


def test_validated_strategy_can_receive_exposure():
    decision = EvidenceGatedStrategyAllocator().allocate(
        (assessment("trend"),)
    )
    assert decision.strategy_exposure["trend"] == pytest.approx(1.0)
    assert decision.cash_exposure == pytest.approx(0.0)


def test_multiple_eligible_strategies_are_combined_by_relative_score():
    decision = EvidenceGatedStrategyAllocator().allocate(
        (
            assessment("trend", score=1.0),
            assessment("mean_reversion", score=0.5),
        )
    )
    assert decision.strategy_exposure["trend"] == pytest.approx(2.0 / 3.0)
    assert decision.strategy_exposure["mean_reversion"] == pytest.approx(1.0 / 3.0)
    assert decision.total_exposure == pytest.approx(1.0)


def test_total_exposure_cap_never_exceeded():
    decision = EvidenceGatedStrategyAllocator(total_exposure_cap=0.6).allocate(
        (
            assessment("a"),
            assessment("b"),
        )
    )
    assert decision.total_exposure <= 0.6 + 1e-12
    assert decision.cash_exposure == pytest.approx(0.4)


def test_per_strategy_exposure_cap_is_respected():
    decision = EvidenceGatedStrategyAllocator().allocate(
        (assessment("trend", max_exposure=0.25),)
    )
    assert decision.strategy_exposure["trend"] == pytest.approx(0.25)
    assert decision.cash_exposure == pytest.approx(0.75)


def test_zero_suitability_falls_back_to_cash():
    decision = EvidenceGatedStrategyAllocator().allocate(
        (assessment("trend", score=0.0),)
    )
    assert decision.strategy_exposure == {}
    assert decision.cash_exposure == pytest.approx(1.0)


def test_duplicate_strategy_ids_are_rejected():
    with pytest.raises(StrategyAllocationError):
        EvidenceGatedStrategyAllocator().allocate(
            (assessment("trend"), assessment("trend"))
        )


def test_max_exposure_cannot_exceed_requested_exposure():
    with pytest.raises(StrategyAllocationError):
        StrategyAssessment(
            strategy_id="invalid",
            evidence_eligible=True,
            suitability_score=1.0,
            signal_confidence=1.0,
            requested_exposure=0.25,
            max_exposure=0.5,
        )