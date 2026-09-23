from automation.microtrading_holding_horizon_replication_15m_2026_09_23 import (
    HOLDING_HORIZONS,
    LEVERAGE_LEVELS,
    SYMBOLS,
    _stats,
)


def test_replication_universe_is_disjoint_from_all_prior_micro_controls():
    prior = {
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
        "DOGEUSDT", "LTCUSDT", "LINKUSDT", "AVAXUSDT",
    }
    assert set(SYMBOLS).isdisjoint(prior)
    assert set(SYMBOLS) == {"DOTUSDT", "ATOMUSDT", "UNIUSDT", "NEARUSDT"}


def test_replication_protocol_is_unchanged():
    assert HOLDING_HORIZONS == (1, 4, 16)
    assert LEVERAGE_LEVELS == (1.0, 2.0, 3.0)


def test_stats_tracks_turnover():
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
    ]
    result = _stats(rows, 0, 2)
    assert result["turnover"] == 2.0
    assert result["block_open_count"] == 1
    assert result["ruined"] is False
