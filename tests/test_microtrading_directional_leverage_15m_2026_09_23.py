from automation.microtrading_directional_leverage_15m_2026_09_23 import (
    LEVERAGE_LEVELS,
    SYMBOLS,
    _stats,
)


def test_universe_is_disjoint_from_previous_micro_sidecar():
    assert set(SYMBOLS).isdisjoint({"BTCUSDT", "ETHUSDT"})


def test_leverage_stays_within_research_grid():
    assert LEVERAGE_LEVELS == (1.0, 2.0, 3.0)


def test_stats_tracks_gross_and_net_results():
    rows = [
        {
            "net_return": 0.01,
            "gross_return": 0.011,
            "turnover": 1.0,
            "gross_exposure": 1.0,
            "position_changed": 1,
        },
        {
            "net_return": -0.005,
            "gross_return": -0.004,
            "turnover": 0.0,
            "gross_exposure": -1.0,
            "position_changed": 1,
        },
    ]
    result = _stats(rows, 0, 2)
    assert result["bar_count"] == 2
    assert result["gross_period_return"] != result["period_return"]
    assert result["turnover"] == 1.0
    assert result["position_change_count"] == 2
    assert result["ruined"] is False


def test_stats_handles_empty_input():
    assert _stats([], 0, 0) == {"bar_count": 0}
