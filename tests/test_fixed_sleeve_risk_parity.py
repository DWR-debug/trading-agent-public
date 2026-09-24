import pytest

from research.fixed_sleeve_risk_parity import lagged_inverse_vol_weights


def test_fixed_fallback_before_lookback_exists():
    returns = tuple([0.01] * 64)
    weights = lagged_inverse_vol_weights(returns, returns)
    assert weights[0] == {"trend": 0.5, "cross_sectional": 0.5}
    assert weights[63] == {"trend": 0.5, "cross_sectional": 0.5}


def test_allocator_is_lagged_and_ignores_current_return():
    trend = tuple([0.01] * 63 + [0.20])
    cross = tuple([0.01] * 64)
    weights = lagged_inverse_vol_weights(trend, cross)
    assert weights[63] == {"trend": 0.5, "cross_sectional": 0.5}


def test_more_volatile_sleeve_receives_less_weight():
    trend = tuple([0.01, -0.01] * 40)
    cross = tuple([0.001] * len(trend))
    weights = lagged_inverse_vol_weights(trend, cross)
    assert weights[-1]["cross_sectional"] > 0.9
    assert weights[-1]["trend"] < 0.1
    assert sum(weights[-1].values()) == pytest.approx(1.0)


def test_zero_volatility_falls_back_to_fixed_fifty_fifty():
    trend = tuple([0.01] * 70)
    cross = tuple([0.01, -0.01] * 35)
    weights = lagged_inverse_vol_weights(trend, cross)
    assert weights[-1] == {"trend": 0.5, "cross_sectional": 0.5}


def test_mismatched_series_are_rejected():
    with pytest.raises(ValueError):
        lagged_inverse_vol_weights((0.01,), (0.01, 0.02))
