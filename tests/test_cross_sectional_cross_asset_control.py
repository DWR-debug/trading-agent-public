from automation.cross_sectional_cross_asset_control import (
    ASSETS,
    LOOKBACK,
    REBALANCE_DAYS,
    SKIP,
    STRATEGIES,
    _stats,
)


def test_same_cross_asset_universe():
    assert ASSETS == (
        "SPY",
        "EFA",
        "TLT",
        "GLD",
        "DBC",
        "UUP",
        "QQQ",
        "IWM",
    )


def test_primary_rule_is_fixed_12_1_top2():
    assert LOOKBACK == 252
    assert SKIP == 21
    assert REBALANCE_DAYS == 21
    assert STRATEGIES[0] == "cs_momentum_252_long_only_top2"


def test_stats_profit_factor():
    result = _stats([0.10, -0.05, 0.05], 0, 6)
    assert abs(result["profit_factor"] - 3.0) < 1e-12
