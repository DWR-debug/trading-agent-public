from automation.microtrading_holding_horizon_15m_2026_09_23 import (
    HOLDING_HORIZONS,
    LEVERAGE_LEVELS,
    SYMBOLS,
    _stats,
)


def test_universe_is_disjoint_from_prior_micro_controls():
    prior = {"BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"}
    assert set(SYMBOLS).isdisjoint(prior)


def test_holding_horizons_are_fixed():
    assert HOLDING_HORIZONS == (1, 4, 16)


def test_leverage_levels_match_project_limit():
    assert LEVERAGE_LEVELS == (1.0, 2.0, 3.0)


def test_stats_tracks_turnover_and_ruin():
    rows = [
        {
            "net_return": 0.01,
            "gross_return": 0.011,
            "turnover": 2.0,
            "gross_exposure": 1.0,
            "block_opened": 1,
        },
        {
            "net_return": -0.005,
            "gross_return": -0.004,
            "turnover": 0.0,
            "gross_exposure": 1.0,
            "block_opened": 0,
        },
        {
            "net_return": 0.002,
            "gross_return": 0.002,
            "turnover": 2.0,
            "gross_exposure": 1.0,
            "block_opened": 1,
        },
    ]
    result = _stats(rows, 0, 3)
    assert result["bar_count"] == 3
    assert result["block_open_count"] == 2
    assert result["turnover"] == 4.0
    assert result["ruined"] is False


def test_stats_empty_is_safe():
    assert _stats([], 0, 0) == {"bar_count": 0}
