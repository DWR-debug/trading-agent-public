from automation.failure_diagnosis_2026_09_23 import _correlation, _stats


def test_stats_reproduces_basic_return_and_profit_factor():
    result = _stats([0.10, -0.05, 0.02])
    assert result["period_return"] == 1.1 * 0.95 * 1.02 - 1.0
    assert abs(result["profit_factor"] - (0.12 / 0.05)) < 1e-12


def test_correlation_is_zero_for_constant_series():
    assert _correlation([1.0, 1.0], [2.0, 3.0]) == 0.0


def test_correlation_is_one_for_identical_nonconstant_series():
    assert abs(_correlation([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) - 1.0) < 1e-12
