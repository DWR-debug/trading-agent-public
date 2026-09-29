"""Q094 fixed monthly-rebalance overlay for the frozen Q091 portfolio rules.

No optimization or ranking is performed. Both Q091 parent variants are
evaluated under exactly the same calendar-month rebalance schedule.
"""
from __future__ import annotations

from datetime import datetime
from typing import Mapping, Sequence

from portfolio.q091_fixed_ensemble import (
    ENSEMBLE_ID,
    RESIDUAL_ID,
    q091_targets_at,
)

MONTHLY_E1_ID = "M1_MONTHLY_REBALANCED_Q091_E1"
MONTHLY_E2_ID = "M2_MONTHLY_REBALANCED_Q091_E2"
VARIANTS = (MONTHLY_E1_ID, MONTHLY_E2_ID)


def _validate_symbols(symbols: Sequence[str]) -> tuple[str, ...]:
    out = tuple(symbols)
    if len(out) < 2 or len(set(out)) != len(out):
        raise ValueError("Q094 requires at least two unique symbols")
    return out


def is_first_trading_session_of_month(
    assets: Mapping[str, Sequence[object]],
    index: int,
    symbols: Sequence[str],
) -> bool:
    symbols = _validate_symbols(symbols)
    if index < 0:
        raise ValueError("index must be non-negative")
    ts = assets[symbols[0]][index].timestamp
    if index == 0:
        return True
    previous = assets[symbols[0]][index - 1].timestamp
    return (ts.year, ts.month) != (previous.year, previous.month)


def monthly_targets_at(
    assets: Mapping[str, Sequence[object]],
    index: int,
    symbols: Sequence[str],
) -> dict[str, dict[str, float]]:
    """Return both Q094 variants' target weights at one decision index.

    If the current index is not a first trading session of a calendar month,
    the latest prior monthly decision target is carried forward unchanged.
    """
    symbols = _validate_symbols(symbols)
    if index < 0 or index >= len(assets[symbols[0]]):
        raise IndexError(index)

    rebalance_index = index
    while rebalance_index > 0 and not is_first_trading_session_of_month(
        assets, rebalance_index, symbols
    ):
        rebalance_index -= 1

    q091 = q091_targets_at(assets, rebalance_index, symbols)
    return {
        MONTHLY_E1_ID: dict(q091[ENSEMBLE_ID]),
        MONTHLY_E2_ID: dict(q091[RESIDUAL_ID]),
    }


def build_monthly_targets(
    assets: Mapping[str, Sequence[object]],
    symbols: Sequence[str],
) -> dict[str, tuple[dict[str, float], ...]]:
    symbols = _validate_symbols(symbols)
    count = len(assets[symbols[0]])
    result = {variant: [] for variant in VARIANTS}
    current: dict[str, dict[str, float]] | None = None
    for index in range(count):
        if current is None or is_first_trading_session_of_month(assets, index, symbols):
            current = monthly_targets_at(assets, index, symbols)
        assert current is not None
        for variant in VARIANTS:
            result[variant].append(dict(current[variant]))
    return {variant: tuple(rows) for variant, rows in result.items()}


def monthly_rebalance_indices(
    assets: Mapping[str, Sequence[object]],
    symbols: Sequence[str],
) -> tuple[int, ...]:
    symbols = _validate_symbols(symbols)
    count = len(assets[symbols[0]])
    return tuple(
        i for i in range(count)
        if is_first_trading_session_of_month(assets, i, symbols)
    )
