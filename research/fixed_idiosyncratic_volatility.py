"""Fixed monthly market-residual-volatility cross-sectional research policy.

The rule is pre-registered: at the start of each calendar month, rank assets by
the standard deviation of the prior 252 completed daily close-to-close residual
returns after leave-one-out equal-weight market regression, and hold the four
lowest-residual-volatility assets for the current month.
"""
from __future__ import annotations

from datetime import datetime
from math import isfinite
from statistics import stdev


LOOKBACK_SESSIONS = 252
SELECT_COUNT = 4


def _month_key(timestamp: datetime) -> tuple[int, int]:
    return timestamp.year, timestamp.month


def daily_close_returns(closes: list[float]) -> tuple[float, ...]:
    if not closes:
        raise ValueError("At least one close is required.")
    values = [0.0]
    for previous, current in zip(closes, closes[1:]):
        if previous <= 0.0 or current <= 0.0:
            raise ValueError("Close prices must be positive.")
        value = current / previous - 1.0
        if not isfinite(value):
            raise ValueError("Daily return must be finite.")
        values.append(value)
    return tuple(values)


def _ols_residual_std(y: list[float], x: list[float]) -> float:
    if len(y) != len(x) or len(y) < 2:
        raise ValueError("OLS inputs must have equal length >= 2.")
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    centered_x = [value - x_mean for value in x]
    centered_y = [value - y_mean for value in y]
    denominator = sum(value * value for value in centered_x)
    if denominator <= 0.0:
        raise ValueError("Market factor variance must be positive.")
    beta = sum(a * b for a, b in zip(centered_x, centered_y)) / denominator
    alpha = y_mean - beta * x_mean
    residuals = [yy - alpha - beta * xx for yy, xx in zip(y, x)]
    if any(not isfinite(value) for value in residuals):
        raise ValueError("Residuals must be finite.")
    return stdev(residuals)


def prior_month_residual_volatility(
    timestamps: list[datetime],
    daily_returns_by_symbol: dict[str, tuple[float, ...]],
    *,
    lookback_sessions: int = LOOKBACK_SESSIONS,
) -> dict[str, dict[tuple[int, int], float]]:
    symbols = tuple(daily_returns_by_symbol)
    if len(symbols) < 3:
        raise ValueError("At least three symbols are required.")
    if any(len(values) != len(timestamps) for values in daily_returns_by_symbol.values()):
        raise ValueError("All return series must match timestamps.")
    if lookback_sessions < 2:
        raise ValueError("lookback_sessions must be at least 2.")

    month_keys: list[tuple[int, int]] = []
    last_previous_index: dict[tuple[int, int], int] = {}
    for index, timestamp in enumerate(timestamps):
        month = _month_key(timestamp)
        if not month_keys or month_keys[-1] != month:
            month_keys.append(month)
        if index > 0:
            last_previous_index.setdefault(month, index - 1)

    result = {symbol: {} for symbol in symbols}
    for month_index in range(1, len(month_keys)):
        current_month = month_keys[month_index]
        end_index = last_previous_index.get(current_month)
        if end_index is None or end_index < lookback_sessions:
            continue

        start_index = end_index - lookback_sessions + 1
        window_slices = {
            symbol: list(daily_returns_by_symbol[symbol][start_index:end_index + 1])
            for symbol in symbols
        }
        if any(len(values) != lookback_sessions for values in window_slices.values()):
            continue

        for symbol in symbols:
            other_symbols = [item for item in symbols if item != symbol]
            market = [
                sum(window_slices[item][offset] for item in other_symbols) / len(other_symbols)
                for offset in range(lookback_sessions)
            ]
            result[symbol][current_month] = _ols_residual_std(
                window_slices[symbol],
                market,
            )

    return result


def residual_vol_assets(
    symbols: tuple[str, ...],
    vol_values: dict[str, float],
    *,
    select_count: int = SELECT_COUNT,
) -> tuple[str, ...]:
    if len(symbols) < 2:
        raise ValueError("At least two symbols are required.")
    if select_count < 1 or select_count > len(symbols):
        raise ValueError("select_count must be within the universe size.")
    if set(vol_values) != set(symbols):
        raise ValueError("Residual-volatility values must cover exactly the symbols.")
    return tuple(
        symbol
        for symbol, _value in sorted(
            ((symbol, vol_values[symbol]) for symbol in symbols),
            key=lambda item: (item[1], item[0]),
        )[:select_count]
    )


def high_residual_vol_assets(
    symbols: tuple[str, ...],
    vol_values: dict[str, float],
    *,
    select_count: int = SELECT_COUNT,
) -> tuple[str, ...]:
    if set(vol_values) != set(symbols):
        raise ValueError("Residual-volatility values must cover exactly the symbols.")
    return tuple(
        symbol
        for symbol, _value in sorted(
            ((symbol, vol_values[symbol]) for symbol in symbols),
            key=lambda item: (-item[1], item[0]),
        )[:select_count]
    )
