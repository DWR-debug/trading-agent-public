"""Fixed monthly MAX-effect research policy.

The rule is pre-registered: for each month, rank assets by the maximum
close-to-close daily return observed in the immediately preceding calendar
month and hold the four lowest-MAX assets during the current month.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import isfinite


SELECT_COUNT = 4


def _month_key(timestamp: datetime) -> tuple[int, int]:
    return timestamp.year, timestamp.month


def daily_close_returns(closes: list[float]) -> tuple[float, ...]:
    if not closes:
        raise ValueError("At least one close is required.")
    result = [0.0]
    for previous, current in zip(closes, closes[1:]):
        if previous <= 0.0 or current <= 0.0:
            raise ValueError("Close prices must be positive.")
        value = current / previous - 1.0
        if not isfinite(value):
            raise ValueError("Daily return must be finite.")
        result.append(value)
    return tuple(result)


def previous_month_max(
    timestamps: list[datetime],
    daily_returns: tuple[float, ...],
) -> dict[tuple[int, int], float]:
    if len(timestamps) != len(daily_returns):
        raise ValueError("Timestamps and daily returns must have equal length.")
    by_month: dict[tuple[int, int], list[float]] = defaultdict(list)
    for timestamp, value in zip(timestamps, daily_returns):
        by_month[_month_key(timestamp)].append(value)

    ordered_months = sorted(by_month)
    result: dict[tuple[int, int], float] = {}
    for index in range(1, len(ordered_months)):
        previous = ordered_months[index - 1]
        current = ordered_months[index]
        result[current] = max(by_month[previous])
    return result


def low_max_assets(
    symbols: tuple[str, ...],
    max_values: dict[str, float],
    *,
    select_count: int = SELECT_COUNT,
) -> tuple[str, ...]:
    if len(symbols) < 2:
        raise ValueError("At least two symbols are required.")
    if select_count < 1 or select_count > len(symbols):
        raise ValueError("select_count must be within the universe size.")
    missing = set(symbols) - set(max_values)
    if missing:
        raise ValueError(f"Missing MAX values for: {sorted(missing)}")
    return tuple(
        symbol
        for symbol, _value in sorted(
            ((symbol, max_values[symbol]) for symbol in symbols),
            key=lambda item: (item[1], item[0]),
        )[:select_count]
    )


def build_monthly_weight_path(
    timestamps: list[datetime],
    returns_by_symbol: dict[str, tuple[float, ...]],
    *,
    select_count: int = SELECT_COUNT,
) -> tuple[tuple[float, ...], dict[tuple[int, int], tuple[str, ...]]]:
    symbols = tuple(sorted(returns_by_symbol))
    if not symbols:
        raise ValueError("At least one symbol is required.")
    for symbol in symbols:
        if len(returns_by_symbol[symbol]) != len(timestamps):
            raise ValueError(f"{symbol}: return length mismatch.")

    max_by_symbol_month: dict[tuple[int, int], dict[str, float]] = {}
    for symbol in symbols:
        series = returns_by_symbol[symbol]
        month_values = previous_month_max(timestamps, series)
        for month, value in month_values.items():
            max_by_symbol_month.setdefault(month, {})[symbol] = value

    weights: list[float] = []
    target_sets: dict[tuple[int, int], tuple[str, ...]] = {}
    previous_weights = {symbol: 0.0 for symbol in symbols}

    for index, timestamp in enumerate(timestamps):
        month = _month_key(timestamp)
        max_values = max_by_symbol_month.get(month)
        if max_values and len(max_values) == len(symbols):
            selected = low_max_assets(symbols, max_values, select_count=select_count)
            target = {symbol: (1.0 / select_count if symbol in selected else 0.0) for symbol in symbols}
            target_sets[month] = selected
        else:
            target = {symbol: 0.0 for symbol in symbols}

        turnover = sum(abs(target[symbol] - previous_weights[symbol]) for symbol in symbols)
        portfolio_weight = sum(target.values())
        weights.append((portfolio_weight, turnover))
        previous_weights = target

    return tuple(weights), target_sets
