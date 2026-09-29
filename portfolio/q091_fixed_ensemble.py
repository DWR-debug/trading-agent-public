"""Q091 fixed portfolio-architecture transforms for the frozen Q069 bank.

No optimization, ranking, learning, or execution is performed here.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from automation.q069_candidate_bank import CANDIDATES, candidate_targets_at


class Q091PortfolioError(ValueError):
    pass


ENSEMBLE_ID = "E1_EQUAL_WEIGHT_Q069_5SLEEVE"
RESIDUAL_ID = "E2_CROSS_SECTIONAL_RESIDUALIZED_Q069_5SLEEVE"


def _validate_symbols(symbols: Sequence[str]) -> tuple[str, ...]:
    out = tuple(symbols)
    if len(out) < 2 or len(set(out)) != len(out):
        raise Q091PortfolioError("Q091 requires at least two unique symbols.")
    if any(not isinstance(s, str) or not s.strip() for s in out):
        raise Q091PortfolioError("Q091 symbols must be non-empty strings.")
    return out


def _validate_weights(weights: Mapping[str, float], symbols: Sequence[str]) -> None:
    missing = set(symbols) - set(weights)
    extra = set(weights) - set(symbols)
    if missing or extra:
        raise Q091PortfolioError(
            f"Weight symbols mismatch: missing={sorted(missing)}, extra={sorted(extra)}"
        )
    for symbol in symbols:
        if not math.isfinite(float(weights[symbol])):
            raise Q091PortfolioError(f"Non-finite weight for {symbol}")


def demean_weights(weights: Mapping[str, float], symbols: Sequence[str]) -> dict[str, float]:
    """Remove the cross-sectional mean with no fitted parameter."""
    symbols = _validate_symbols(symbols)
    _validate_weights(weights, symbols)
    average = sum(float(weights[s]) for s in symbols) / len(symbols)
    return {s: float(weights[s]) - average for s in symbols}


def gross_normalize(weights: Mapping[str, float], symbols: Sequence[str]) -> dict[str, float]:
    """Normalize to unit gross exposure; preserve a zero vector."""
    symbols = _validate_symbols(symbols)
    _validate_weights(weights, symbols)
    gross = sum(abs(float(weights[s])) for s in symbols)
    if gross == 0.0:
        return {s: 0.0 for s in symbols}
    return {s: float(weights[s]) / gross for s in symbols}


def equal_weight_ensemble(
    sleeve_weights: Mapping[str, Mapping[str, float]],
    symbols: Sequence[str],
) -> dict[str, float]:
    """Fixed 1/5 arithmetic combination of all five Q069 sleeves."""
    symbols = _validate_symbols(symbols)
    if set(sleeve_weights) != set(CANDIDATES):
        raise Q091PortfolioError("Q091 must include exactly all five Q069 sleeves.")
    for name in CANDIDATES:
        _validate_weights(sleeve_weights[name], symbols)
    return {
        s: sum(float(sleeve_weights[name][s]) for name in CANDIDATES) / len(CANDIDATES)
        for s in symbols
    }


def cross_sectional_residualized_ensemble(
    sleeve_weights: Mapping[str, Mapping[str, float]],
    symbols: Sequence[str],
) -> dict[str, float]:
    """Demean each sleeve, average the five sleeves, then unit-gross normalize."""
    residualized = {
        name: demean_weights(sleeve_weights[name], symbols)
        for name in CANDIDATES
    }
    return gross_normalize(equal_weight_ensemble(residualized, symbols), symbols)


def q069_sleeves_at(
    assets: Mapping[str, Sequence[object]],
    index: int,
    symbols: Sequence[str],
) -> dict[str, dict[str, float]]:
    """Build exactly the frozen Q069 sleeves at one decision index."""
    symbols = _validate_symbols(symbols)
    return {
        name: candidate_targets_at(assets, index, symbols=symbols)[name]
        for name in CANDIDATES
    }


def q091_targets_at(
    assets: Mapping[str, Sequence[object]],
    index: int,
    symbols: Sequence[str],
) -> dict[str, dict[str, float]]:
    """Return both fixed Q091 variants at one decision index."""
    sleeves = q069_sleeves_at(assets, index, symbols)
    return {
        ENSEMBLE_ID: equal_weight_ensemble(sleeves, symbols),
        RESIDUAL_ID: cross_sectional_residualized_ensemble(sleeves, symbols),
    }
