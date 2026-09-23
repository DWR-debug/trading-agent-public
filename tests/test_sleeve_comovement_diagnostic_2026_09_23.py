from automation.sleeve_comovement_diagnostic_2026_09_23 import (
    _correlation,
    _interaction,
)


def test_correlation_is_symmetric():
    left = [0.01, -0.01, 0.02, -0.02]
    right = [0.02, -0.02, 0.03, -0.03]
    assert abs(_correlation(left, right) - _correlation(right, left)) < 1e-12


def test_joint_negative_rate_and_opposite_sign_rates():
    result = _interaction(
        [0.02, -0.01, -0.02, 0.01],
        [0.01, -0.02, 0.03, -0.01],
    )
    assert abs(result["both_negative_rate"] - 0.25) < 1e-12
    assert abs(result["trend_negative_cs_positive_rate"] - 0.25) < 1e-12
    assert abs(result["trend_positive_cs_negative_rate"] - 0.25) < 1e-12


def test_worst_tail_metric_is_defined():
    result = _interaction(
        [0.01, -0.02, -0.03, 0.02, -0.01] * 20,
        [0.00, -0.01, -0.02, 0.01, -0.02] * 20,
    )
    assert result["worst_5pct_count"] >= 1
