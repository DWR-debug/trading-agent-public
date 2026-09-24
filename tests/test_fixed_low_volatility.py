from datetime import datetime, timedelta, timezone

import pytest

from research.fixed_low_volatility import (
    daily_close_returns,
    high_vol_assets,
    low_vol_assets,
    prior_month_low_vol,
)


def test_daily_close_returns():
    values = daily_close_returns([100.0, 105.0, 102.0])
    assert values[0] == 0.0
    assert values[1] == pytest.approx(0.05)
    assert values[2] == pytest.approx(102.0 / 105.0 - 1.0)


def test_prior_month_low_vol_uses_only_completed_previous_month():
    timestamps = [
        datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=i)
        for i in range(260)
    ] + [datetime(2026, 10, 1, tzinfo=timezone.utc)]

    returns = tuple([0.001] * 260 + [0.50])

    values = prior_month_low_vol(
        timestamps,
        returns,
        lookback_sessions=252,
    )

    # The cross-month return dated October 1 must not enter September's MAX/VOL
    # history. October can use the 252 completed sessions ending in September.
    assert (2026, 10) in values
    assert values[(2026, 10)] < 0.01


def test_low_vol_assets_uses_deterministic_tie_break():
    selected = low_vol_assets(
        ("BBB", "AAA", "CCC"),
        {"AAA": 0.01, "BBB": 0.01, "CCC": 0.02},
        select_count=2,
    )
    assert selected == ("AAA", "BBB")


def test_high_vol_assets_uses_deterministic_tie_break():
    selected = high_vol_assets(
        ("BBB", "AAA", "CCC"),
        {"AAA": 0.02, "BBB": 0.02, "CCC": 0.01},
        select_count=2,
    )
    assert selected == ("AAA", "BBB")


def test_low_vol_assets_rejects_missing_value():
    with pytest.raises(ValueError):
        low_vol_assets(("AAA", "BBB"), {"AAA": 0.01}, select_count=1)
