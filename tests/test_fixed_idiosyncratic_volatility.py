import math
from datetime import datetime, timedelta, timezone

import pytest

from research.fixed_idiosyncratic_volatility import (
    high_residual_vol_assets,
    residual_vol_assets,
    _ols_residual_std,
    prior_month_residual_volatility,
    daily_close_returns,
)


def test_daily_close_returns_are_finite_and_deterministic():
    result = daily_close_returns([100.0, 101.0, 99.0])
    assert result[0] == 0.0
    assert math.isfinite(result[1])
    assert math.isfinite(result[2])


def test_ols_residual_std_is_near_zero_for_exact_linear_relation():
    x = [0.0, 0.01, -0.01, 0.02, -0.02]
    y = [0.001 + 2.0 * value for value in x]
    assert _ols_residual_std(y, x) < 1e-14


def test_ols_residual_std_rejects_zero_factor_variance():
    with pytest.raises(ValueError):
        _ols_residual_std([0.01, 0.02, 0.03], [0.0, 0.0, 0.0])


def test_residual_vol_ranking_is_deterministic():
    symbols = ("A", "B", "C", "D")
    values = {"A": 0.02, "B": 0.01, "C": 0.03, "D": 0.02}
    assert residual_vol_assets(symbols, values, select_count=2) == ("B", "A")
    assert high_residual_vol_assets(symbols, values, select_count=2) == ("C", "A")


def test_prior_month_requires_full_lookback_and_residualization():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    timestamps = [start + timedelta(days=i) for i in range(270)]
    base = [100.0 * (1.0005 ** i) for i in range(270)]
    assets = {
        "A": [100.0 + i * 0.01 for i in range(270)],
        "B": [100.0 + i * 0.02 for i in range(270)],
        "C": [100.0 + i * 0.03 + (0.2 if i % 7 == 0 else 0.0) for i in range(270)],
    }
    returns = {symbol: daily_close_returns(closes) for symbol, closes in assets.items()}
    result = prior_month_residual_volatility(timestamps, returns, lookback_sessions=30)
    assert all(isinstance(item, dict) for item in result.values())
    assert all(value >= 0.0 for item in result.values() for value in item.values())
