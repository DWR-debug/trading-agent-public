"""Deterministic H06-P2 global ranking signal construction.

Research-only signal kernel. No forward returns, P&L, holdout observations,
parameter search, or authorization decisions are performed here.

H06-P2 intentionally applies the sector-residual transformation before a
GLOBAL cross-sectional top-5/bottom-5 selection. Selecting within each sector
would make residualization algebraically identical to raw momentum.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

SYMBOLS: tuple[str, ...] = (
    "TXN", "ADI", "AMAT",
    "MDT", "SYK", "BDX",
    "ETN", "ITW", "GD",
    "CL", "KMB", "GIS",
    "AEP", "XEL", "DTE",
)

SECTOR_MAP: dict[str, tuple[str, ...]] = {
    "technology": ("TXN", "ADI", "AMAT"),
    "healthcare": ("MDT", "SYK", "BDX"),
    "industrials": ("ETN", "ITW", "GD"),
    "consumer_staples": ("CL", "KMB", "GIS"),
    "utilities": ("AEP", "XEL", "DTE"),
}

LOOKBACK = 252
SKIP = 21
TOP_K = 5
WEIGHT = 0.10


def _validate_symbols(scores: Mapping[str, float]) -> None:
    if set(scores) != set(SYMBOLS):
        raise ValueError("H06P2_SYMBOL_SET_MISMATCH")


def raw_momentum_scores(closes: Mapping[str, Sequence[float]], index: int) -> dict[str, float]:
    _validate_symbols(closes)
    if index < LOOKBACK:
        raise ValueError("H06P2_INSUFFICIENT_LOOKBACK")
    out: dict[str, float] = {}
    for symbol in SYMBOLS:
        series = closes[symbol]
        if len(series) <= index:
            raise ValueError("H06P2_SERIES_TOO_SHORT")
        base = float(series[index - LOOKBACK])
        skip_close = float(series[index - SKIP])
        if base <= 0.0 or skip_close <= 0.0:
            raise ValueError("H06P2_NONPOSITIVE_CLOSE")
        out[symbol] = skip_close / base - 1.0
    return out


def residualize_by_sector(raw: Mapping[str, float]) -> dict[str, float]:
    _validate_symbols(raw)
    out = dict(raw)
    for members in SECTOR_MAP.values():
        mean = sum(float(raw[s]) for s in members) / len(members)
        for symbol in members:
            out[symbol] = float(raw[symbol]) - mean
    return out


def rank_global(
    scores: Mapping[str, float],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    _validate_symbols(scores)
    ordered = sorted(SYMBOLS, key=lambda symbol: (-float(scores[symbol]), symbol))
    longs = tuple(ordered[:TOP_K])
    shorts = tuple(ordered[-TOP_K:][::-1])
    if set(longs) & set(shorts):
        raise ValueError("H06P2_LONG_SHORT_OVERLAP")
    return longs, shorts


def target_weights(
    scores: Mapping[str, float],
) -> dict[str, float]:
    longs, shorts = rank_global(scores)
    return {
        symbol: (
            WEIGHT if symbol in longs
            else -WEIGHT if symbol in shorts
            else 0.0
        )
        for symbol in SYMBOLS
    }


def build_arms(
    closes: Mapping[str, Sequence[float]],
    index: int,
) -> dict[str, dict[str, object]]:
    raw = raw_momentum_scores(closes, index)
    residual = residualize_by_sector(raw)
    raw_longs, raw_shorts = rank_global(raw)
    residual_longs, residual_shorts = rank_global(residual)
    return {
        "H06-P2-RAW-GLOBAL-T5/B5": {
            "longs": raw_longs,
            "shorts": raw_shorts,
            "weights": target_weights(raw),
            "signal_type": "raw_global",
        },
        "H06-P2-RESIDUAL-GLOBAL-T5/B5": {
            "longs": residual_longs,
            "shorts": residual_shorts,
            "weights": target_weights(residual),
            "signal_type": "sector_residual_global",
        },
    }


def gross_exposure(weights: Mapping[str, float]) -> float:
    return sum(abs(float(value)) for value in weights.values())


def net_exposure(weights: Mapping[str, float]) -> float:
    return sum(float(value) for value in weights.values())
