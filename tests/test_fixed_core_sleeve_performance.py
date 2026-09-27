from pathlib import Path

from automation.fixed_core_sleeve_performance import (
    _cs_weights,
    _load_prereg,
    _rolling,
    _stats,
)
from backtesting.models import Candle


def _assets(count=3500):
    from datetime import datetime, timedelta, timezone
    origin = datetime(2011, 1, 1, tzinfo=timezone.utc)
    symbols = ("A", "B", "C", "D")
    return {
        symbol: tuple(
            Candle(
                timestamp=origin + timedelta(days=i),
                open=100.0 + i + offset,
                high=100.0 + i + offset,
                low=100.0 + i + offset,
                close=100.0 + i + offset,
                volume=1000.0,
            )
            for i in range(count)
        )
        for offset, symbol in enumerate(symbols)
    }


def test_cs_weights_are_fixed_top2_long_only():
    weights = _cs_weights(_assets())
    assert len(weights) == 3500
    assert all(sum(row.values()) <= 1.0 + 1e-12 for row in weights)
    assert all(
        value in {0.0, 0.5}
        for row in weights[280:3500]
        for value in row.values()
    )


def test_stats_and_rolling_are_deterministic():
    values = [0.01, -0.005, 0.02, -0.01] * 700
    assert _stats(values, 0, 2798) == _stats(values, 0, 2798)
    rolling = _rolling(values)
    assert len(rolling) == 5
    assert sum(item["day_count"] for item in rolling) == 2798


def test_t052_preregistration_is_safe_and_fixed():
    spec = _load_prereg(
        Path(
            "research/preregistrations/"
            "trial_052_fixed_core_sleeve_performance_2026_09_27.json"
        )
    )
    assert spec["trial_id"] == "T-2026-09-27-052"
    assert spec["data_contract"]["research_periods"] == 2798
    assert spec["data_contract"]["holdout_periods"] == 700
    assert spec["governance"]["parameter_search"] is False
    assert spec["governance"]["asset_selection_by_performance"] is False
    assert spec["governance"]["holdout_used_for_selection"] is False
    assert spec["safety"]["orders_enabled"] is False


def test_stats_empty_is_explicitly_empty():
    result = _stats([], 0, 1)
    assert result["day_count"] == 0
    assert result["period_return"] == 0.0
