"""Deterministic lagged OHLCV market-state topology for RCCSM.

Feasibility-only. No future labels, P&L, holdout outcomes, or optimization are
accepted. Every descriptor at decision index i uses data at or before i.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

STATE_FIELDS = (
    "trend_coherence",
    "breadth",
    "dispersion_percentile",
    "shock_density",
)

DEFAULT_TREND_WINDOW = 63
DEFAULT_BREADTH_WINDOW = 200
DEFAULT_DISPERSION_WINDOW = 21
DEFAULT_DISPERSION_HISTORY = 252
DEFAULT_SHOCK_WINDOW = 5
DEFAULT_SHOCK_HISTORY = 63


def _finite_float(value: Any, name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")
    return out


def _closes(assets: Mapping[str, Sequence[Any]], symbols: Sequence[str]) -> dict[str, list[float]]:
    if not symbols:
        raise ValueError("symbols must be non-empty")
    if len(symbols) != len(set(symbols)):
        raise ValueError("symbols must be unique")
    missing = [s for s in symbols if s not in assets]
    if missing:
        raise ValueError(f"missing symbols: {missing}")
    lengths = {len(assets[s]) for s in symbols}
    if len(lengths) != 1:
        raise ValueError("assets must be aligned")
    out: dict[str, list[float]] = {}
    for symbol in symbols:
        values = [_finite_float(getattr(bar, "close"), f"{symbol}.close") for bar in assets[symbol]]
        if any(value <= 0 for value in values):
            raise ValueError(f"{symbol}: close values must be positive")
        out[symbol] = values
    return out


def _return_at(closes: Sequence[float], index: int, window: int) -> float:
    if index < window:
        raise ValueError(f"index {index} lacks {window} sessions")
    return closes[index] / closes[index - window] - 1.0


def _dispersion_at(closes: Mapping[str, Sequence[float]], index: int, window: int, symbols: Sequence[str]) -> float:
    values = [_return_at(closes[s], index, window) for s in symbols]
    mean = sum(values) / len(values)
    return math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))


def _percentile_rank(value: float, history: Sequence[float]) -> float:
    if not history:
        raise ValueError("percentile history must be non-empty")
    less = sum(item < value for item in history)
    equal = sum(item == value for item in history)
    return (less + 0.5 * equal) / len(history)


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def fingerprint(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def state_at(
    assets: Mapping[str, Sequence[Any]],
    index: int,
    *,
    symbols: Sequence[str],
    trend_window: int = DEFAULT_TREND_WINDOW,
    breadth_window: int = DEFAULT_BREADTH_WINDOW,
    dispersion_window: int = DEFAULT_DISPERSION_WINDOW,
    dispersion_history: int = DEFAULT_DISPERSION_HISTORY,
    shock_window: int = DEFAULT_SHOCK_WINDOW,
    shock_history: int = DEFAULT_SHOCK_HISTORY,
) -> dict[str, Any]:
    """Compute one state observation using only bars <= index."""
    if min(trend_window, breadth_window, dispersion_window, dispersion_history, shock_window, shock_history) < 1:
        raise ValueError("window lengths must be positive")
    closes = _closes(assets, symbols)
    min_history = max(trend_window, breadth_window, dispersion_window + dispersion_history, shock_window + shock_history)
    if index < min_history:
        raise ValueError(f"index {index} lacks required state history {min_history}")

    trend_returns = [_return_at(closes[s], index, trend_window) for s in symbols]
    positive = sum(value > 0 for value in trend_returns)
    negative = sum(value < 0 for value in trend_returns)
    trend_coherence = max(positive, negative) / len(symbols)

    breadth = sum(
        closes[s][index] > sum(closes[s][index - breadth_window:index]) / breadth_window
        for s in symbols
    ) / len(symbols)

    current_dispersion = _dispersion_at(closes, index, dispersion_window, symbols)
    history = [
        _dispersion_at(closes, j, dispersion_window, symbols)
        for j in range(index - dispersion_history, index)
    ]
    dispersion_percentile = _percentile_rank(current_dispersion, history)

    shock_flags = []
    for s in symbols:
        recent_abs = [
            abs(closes[s][index - shock_window + k] / closes[s][index - shock_window + k - 1] - 1.0)
            for k in range(shock_window)
        ]
        prior_abs = [
            abs(closes[s][j] / closes[s][j - 1] - 1.0)
            for j in range(index - shock_history, index - shock_window)
        ]
        prior_mean = sum(prior_abs) / len(prior_abs)
        shock_flags.append(1.0 if sum(recent_abs) / len(recent_abs) > 2.0 * prior_mean else 0.0)
    shock_density = sum(shock_flags) / len(symbols)

    payload = {
        "schema_version": 1,
        "index": index,
        "symbols": list(symbols),
        "trend_window": trend_window,
        "breadth_window": breadth_window,
        "dispersion_window": dispersion_window,
        "dispersion_history": dispersion_history,
        "shock_window": shock_window,
        "shock_history": shock_history,
        "trend_coherence": trend_coherence,
        "breadth": breadth,
        "dispersion_percentile": dispersion_percentile,
        "shock_density": shock_density,
        "uses_future_bars": False,
        "uses_returns_as_targets": False,
        "uses_holdout": False,
        "uses_optimizer": False,
    }
    payload["provenance_fingerprint"] = fingerprint(payload)
    return payload
