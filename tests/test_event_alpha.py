import pytest
from datetime import date

from research.event_alpha import (
    EventAlphaError,
    EventRelativeValuePolicy,
    gross_exposure,
    net_exposure,
    qualifying_event,
    target_weights,
)
from research.event_intelligence import EventFeatures


def features(*, conflict: int, high_confidence: int) -> EventFeatures:
    return EventFeatures(
        event_date=date(2025, 5, 1),
        event_count=high_confidence,
        international_event_count=high_confidence,
        high_confidence_international_count=high_confidence,
        material_conflict_count=conflict,
        international_material_conflict_count=conflict,
        verbal_conflict_count=0,
        material_cooperation_count=0,
        negative_goldstein_sum=1.0,
        mention_weighted_conflict=2.0,
        source_count=3,
        mean_tone=-1.0,
    )


def test_default_policy_is_market_neutral_and_one_x_gross():
    policy = EventRelativeValuePolicy()
    assert gross_exposure(policy.weights) == pytest.approx(1.0)
    assert net_exposure(policy.weights) == pytest.approx(0.0)
    assert policy.symbols == ("IWB", "GDX", "BIL")


def test_qualifying_event_requires_both_fixed_conditions():
    assert qualifying_event(features(conflict=1, high_confidence=1))
    assert not qualifying_event(features(conflict=0, high_confidence=1))
    assert not qualifying_event(features(conflict=1, high_confidence=0))


def test_target_weights_are_fixed_when_active():
    policy = EventRelativeValuePolicy()
    assert target_weights(features(conflict=1, high_confidence=2), policy) == {
        "IWB": -0.5,
        "GDX": 0.25,
        "BIL": 0.25,
    }
    assert target_weights(features(conflict=0, high_confidence=2), policy) == {}


def test_policy_rejects_non_neutral_or_over_exposed_weights():
    with pytest.raises(EventAlphaError):
        EventRelativeValuePolicy(risk_weight=-0.4)
    with pytest.raises(EventAlphaError):
        EventRelativeValuePolicy(defensive_weight_a=0.5)


def test_policy_rejects_duplicate_assets():
    with pytest.raises(EventAlphaError):
        EventRelativeValuePolicy(defensive_asset_a="IWB")
