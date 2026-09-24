from automation.portfolio_risk_control_min_variance import (
    COVARIANCE_WINDOW,
    min_variance_weight,
)


def test_min_variance_is_half_for_identical_sleeves():
    values = [0.01, -0.01, 0.02, -0.02] * (COVARIANCE_WINDOW // 4 + 1)
    values = values[:COVARIANCE_WINDOW]
    assert min_variance_weight(values, values) == 0.5


def test_min_variance_prefers_lower_variance_when_covariance_is_fixed():
    trend = [0.005, -0.005] * (COVARIANCE_WINDOW // 2 + 1)
    cross = [0.02, -0.02] * (COVARIANCE_WINDOW // 2 + 1)
    trend = trend[:COVARIANCE_WINDOW]
    cross = cross[:COVARIANCE_WINDOW]
    weight = min_variance_weight(trend, cross)
    assert 0.70 < weight < 0.90


def test_min_variance_is_clamped_long_only():
    trend = [0.02, -0.02] * (COVARIANCE_WINDOW // 2 + 1)
    cross = [0.001, -0.001] * (COVARIANCE_WINDOW // 2 + 1)
    trend = trend[:COVARIANCE_WINDOW]
    cross = cross[:COVARIANCE_WINDOW]
    weight = min_variance_weight(trend, cross)
    assert 0.0 <= weight <= 1.0
