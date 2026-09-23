from automation.independent_european_trend_control import (
    STRATEGIES,
    _stats,
)


def test_strategy_set_is_fixed():
    assert STRATEGIES == (
        "buy_and_hold",
        "tsm_ensemble",
        "sma_50_200_long_flat",
        "donchian_55_20",
    )


def test_stats_handles_empty_segment():
    result = _stats([], 0, 10)
    assert result["day_count"] == 0
    assert result["period_return"] == 0.0
    assert result["profit_factor"] == 0.0


def test_stats_profit_factor():
    result = _stats([0.10, -0.05, 0.05], 0, 6)
    assert abs(result["profit_factor"] - 3.0) < 1e-12
