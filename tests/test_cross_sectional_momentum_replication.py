from automation.cross_sectional_momentum_replication import (
    ASSETS,
    LOOKBACK,
    REBALANCE_DAYS,
    SKIP,
    STRATEGIES,
    _stats,
)


def test_replication_uses_independent_liquid_universe():
    assert ASSETS == ("NVDA", "AMD", "TSLA", "COIN", "PLTR")


def test_primary_rule_is_exact_12_1_top2():
    assert LOOKBACK == 252
    assert SKIP == 21
    assert REBALANCE_DAYS == 21
    assert STRATEGIES == (
        "cs_momentum_252_long_only_top2",
        "equal_weight_buy_and_hold",
    )


def test_stats_profit_factor():
    result = _stats([0.10, -0.05, 0.05], 0, 6)
    assert abs(result["profit_factor"] - 3.0) < 1e-12


def test_stats_empty_safe():
    result = _stats([], 0, 10)
    assert result["day_count"] == 0
    assert result["period_return"] == 0.0
