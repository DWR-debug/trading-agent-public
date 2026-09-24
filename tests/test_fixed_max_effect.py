from datetime import datetime, timezone

import pytest

from research.fixed_max_effect import (
    daily_close_returns,
    low_max_assets,
    previous_month_max,
)


def test_daily_close_returns():
    values = daily_close_returns([100.0, 105.0, 102.0])
    assert values[0] == 0.0
    assert values[1] == pytest.approx(0.05)
    assert values[2] == pytest.approx(102.0 / 105.0 - 1.0)


def test_previous_month_max_is_lagged_by_calendar_month():
    timestamps = [
        datetime(2026, 1, 30, tzinfo=timezone.utc),
        datetime(2026, 2, 2, tzinfo=timezone.utc),
        datetime(2026, 2, 3, tzinfo=timezone.utc),
        datetime(2026, 2, 4, tzinfo=timezone.utc),
        datetime(2026, 3, 2, tzinfo=timezone.utc),
    ]
    returns = (0.0, 0.02, 0.02, -0.01, 0.03)
    values = previous_month_max(timestamps, returns)
    assert values[(2026, 2)] == pytest.approx(0.0)
    assert values[(2026, 3)] == pytest.approx(0.02)


def test_low_max_assets_uses_deterministic_tie_break():
    symbols = ("BBB", "AAA", "CCC")
    selected = low_max_assets(
        symbols,
        {"AAA": 0.01, "BBB": 0.01, "CCC": 0.02},
        select_count=2,
    )
    assert selected == ("AAA", "BBB")


def test_low_max_assets_rejects_missing_value():
    with pytest.raises(ValueError):
        low_max_assets(("AAA", "BBB"), {"AAA": 0.01}, select_count=1)
