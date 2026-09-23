from automation.cross_asset_trend_replication import (
    LOOKBACKS,
    MAX_ASSET_WEIGHT,
    STRATEGIES,
    _inverse_vol_weights,
    _month_end_indices,
    _stats,
)


def test_pre_registered_cross_asset_strategy_set():
    assert STRATEGIES == (
        "buy_and_hold_equal",
        "tsm_monthly_equal",
        "tsm_monthly_inverse_vol",
        "sma_50_200_inverse_vol",
        "blend_tsm_sma_inverse_vol",
    )


def test_tsm_horizons_match_one_three_twelve_month_proxy():
    assert LOOKBACKS == (21, 63, 252)


def test_inverse_vol_weights_respect_asset_cap():
    signals = {
        "A": 1.0,
        "B": 1.0,
        "C": -1.0,
        "D": 0.0,
    }
    vols = {
        "A": 0.01,
        "B": 0.02,
        "C": 0.03,
        "D": 0.02,
    }

    weights = _inverse_vol_weights(signals, vols)

    assert weights["A"] <= MAX_ASSET_WEIGHT
    assert weights["B"] <= MAX_ASSET_WEIGHT
    assert weights["C"] >= -MAX_ASSET_WEIGHT
    assert set(weights) == set(signals)
    assert sum(abs(value) for value in weights.values()) <= 1.0 + 1e-12


def test_stats_calculates_profit_factor():
    result = _stats([0.10, -0.05, 0.05], 0, 6)
    assert abs(result["profit_factor"] - 3.0) < 1e-12


def test_month_end_indices_identifies_month_boundaries():
    class Stamp:
        def __init__(self, year, month):
            self.year = year
            self.month = month

    class Bar:
        def __init__(self, year, month):
            self.timestamp = Stamp(year, month)

    bars = (
        Bar(2020, 1),
        Bar(2020, 1),
        Bar(2020, 2),
        Bar(2020, 2),
        Bar(2020, 3),
    )

    assert _month_end_indices(bars) == (1, 3, 4)
