"""Fixed monthly low-realized-volatility cross-sectional research policy.

The rule is pre-registered: at the start of each calendar month, rank assets by
the standard deviation of the prior 252 completed daily close-to-close returns
and hold the four lowest-volatility assets for the current month.
"""
from __future__ import annotations

from datetime import datetime
from math import isfinite, sqrt
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


def prior_month_low_vol(
    timestamps: list[datetime],
    daily_returns: tuple[float, ...],
    *,
    lookback_sessions: int = LOOKBACK_SESSIONS,
) -> dict[tuple[int, int], float]:
    if len(timestamps) != len(daily_returns):
        raise ValueError("Timestamps and daily returns must have equal length.")
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

    result: dict[tuple[int, int], float] = {}
    for month_index in range(1, len(month_keys)):
        current_month = month_keys[month_index]
        end_index = last_previous_index.get(current_month)
        if end_index is None or end_index < lookback_sessions:
            continue

        window = daily_returns[end_index - lookback_sessions + 1 : end_index + 1]
        if len(window) != lookback_sessions:
            continue

        for value in window:
            if not isfinite(value):
                raise ValueError("Volatility input must be finite.")

        result[current_month] = stdev(window, xbar=sum(window) / len(window))
    return result


def low_vol_assets(
    symbols: tuple[str, ...],
    vol_values: dict[str, float],
    *,
    select_count: int = SELECT_COUNT,
) -> tuple[str, ...]:
    if len(symbols) < 2:
        raise ValueError("At least two symbols are required.")
    if select_count < 1 or select_count > len(symbols):
        raise ValueError("select_count must be within the universe size.")

    missing = set(symbols) - set(vol_values)
    if missing:
        raise ValueError(f"Missing volatility values for: {sorted(missing)}")

    return tuple(
        symbol
        for symbol, _value in sorted(
            ((symbol, vol_values[symbol]) for symbol in symbols),
            key=lambda item: (item[1], item[0]),
        )[:select_count]
    )


def high_vol_assets(
    symbols: tuple[str, ...],
    vol_values: dict[str, float],
    *,
    select_count: int = SELECT_COUNT,
) -> tuple[str, ...]:
    if set(vol_values) != set(symbols):
        raise ValueError("Volatility values must cover exactly the requested symbols.")

    return tuple(
        symbol
        for symbol, _value in sorted(
            ((symbol, vol_values[symbol]) for symbol in symbols),
            key=lambda item: (-item[1], item[0]),
        )[:select_count]
    )
