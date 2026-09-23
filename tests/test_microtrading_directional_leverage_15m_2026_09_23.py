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


from datetime import datetime, timezone

from automation.microtrading_directional_leverage_15m_2026_09_23 import _align_assets


def test_alignment_uses_common_timestamps_when_one_asset_lacks_a_bar():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows_a = [
        {"timestamp": t0, "net_return": 0.0, "gross_return": 0.0, "turnover": 0.0, "gross_exposure": 1.0, "position_changed": 0},
        {"timestamp": t0.replace(hour=0, minute=15), "net_return": 0.01, "gross_return": 0.01, "turnover": 0.0, "gross_exposure": 1.0, "position_changed": 0},
    ]
    rows_b = [rows_a[0]]
    aligned = _align_assets({"SOLUSDT": rows_a, "BNBUSDT": rows_a, "XRPUSDT": rows_a, "ADAUSDT": rows_b})
    assert len(aligned) == 1
