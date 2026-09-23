from automation.third_validation_failure_diagnosis_2026_09_23 import (
    _correlation,
    _stats,
)


def test_stats_compounds_returns_and_drawdown():
    result = _stats([0.10, -0.05])
    assert abs(result["period_return"] - (1.10 * 0.95 - 1.0)) < 1e-15
    assert result["day_count"] == 2
    assert result["max_drawdown_percent"] > 0.0


def test_correlation_identical_series():
    assert abs(_correlation([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) - 1.0) < 1e-12
