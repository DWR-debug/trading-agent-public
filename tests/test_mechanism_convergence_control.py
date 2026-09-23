from automation.mechanism_convergence_control import (
    STRATEGIES,
    _correlation,
    _stats,
)


def test_convergence_strategy_set_is_fixed():
    assert STRATEGIES == (
        "trend_sma_50_200",
        "cs_momentum_12_1",
        "equal_50_50_convergence",
    )


def test_stats_handles_empty_and_positive_series():
    empty = _stats([])
    positive = _stats([0.01, 0.02, -0.01])

    assert empty["day_count"] == 0
    assert positive["day_count"] == 3
    assert positive["profit_factor"] > 0


def test_correlation_of_identical_series_is_one():
    value = _correlation([0.1, 0.2, -0.1], [0.1, 0.2, -0.1])
    assert abs(value - 1.0) < 1e-12


def test_correlation_of_insufficient_series_is_zero():
    assert _correlation([0.1], [0.1]) == 0.0
