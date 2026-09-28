"""Q069 ex-ante orthogonal OHLCV candidate bank.

Design-only candidate mechanisms. No performance evaluation, candidate-family
ranking, holdout selection, promotion, or live execution is performed here.
"""
from __future__ import annotations
from math import sqrt
from collections.abc import Mapping, Sequence

CANDIDATES = (
    "C7_LOW_MAX_21",
    "C8_LOW_IDIO_VOL_273",
    "C9_LONG_TERM_REVERSAL_756",
    "C10_TREND_EFFICIENCY_63",
    "C11_VOLUME_CONFIRMED_TREND_126",
)

MIN_HISTORY_INDEX = {"C7_LOW_MAX_21": 21, "C8_LOW_IDIO_VOL_273": 273, "C9_LONG_TERM_REVERSAL_756": 756, "C10_TREND_EFFICIENCY_63": 63, "C11_VOLUME_CONFIRMED_TREND_126": 146}

GOVERNANCE = {
    "performance_evaluation": False, "selection_used": False,
    "holdout_used_for_selection": False, "parameter_search": False,
    "threshold_search": False, "asset_search": False, "horizon_search": False,
    "variant_search": False, "family_ranking": False,
    "promotion_decision": False, "automatic_promotion": False,
}
SAFETY = {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False}

def _validate_assets(assets: Mapping[str, Sequence[object]], symbols: Sequence[str]) -> None:
    if not symbols: raise ValueError("symbols must be non-empty")
    missing = [s for s in symbols if s not in assets]
    if missing: raise ValueError(f"missing symbols: {missing}")
    if len({len(assets[s]) for s in symbols}) != 1: raise ValueError("candidate inputs must be aligned")

def _returns(closes: Sequence[float]) -> list[float]:
    return [float(closes[i]) / float(closes[i - 1]) - 1.0 for i in range(1, len(closes))]

def _zero(symbols: Sequence[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}

def _top2(scores: Mapping[str, float], symbols: Sequence[str], reverse: bool) -> dict[str, float]:
    ordered = sorted(symbols, key=(lambda s: (-scores[s], s) if reverse else (scores[s], s)))[:2]
    weight = 1.0 / len(ordered)
    return {s: (weight if s in ordered else 0.0) for s in symbols}

def candidate_scores_at(assets, index: int, *, symbols: Sequence[str]) -> dict[str, dict[str, float]]:
    """Return fixed raw scores using only information available at decision index."""
    _validate_assets(assets, symbols)
    closes = {s: [float(b.close) for b in assets[s]] for s in symbols}
    rets = {s: _returns(closes[s]) for s in symbols}

    c7 = _zero(symbols) if index < 21 else {s: max(rets[s][index - 21:index]) for s in symbols}

    if index < 273:
        c8 = _zero(symbols)
    else:
        start, end = index - 273, index
        market = [sum(rets[s][i] for s in symbols) / len(symbols) for i in range(start, end)]
        market_mean = sum(market) / len(market)
        market_var = sum((x - market_mean) ** 2 for x in market)
        c8 = {}
        for s in symbols:
            own = [rets[s][i] for i in range(start, end)]
            own_mean = sum(own) / len(own)
            beta = sum((a - own_mean) * (m - market_mean) for a, m in zip(own, market)) / market_var if market_var > 0 else 0.0
            residual = [a - beta * m for a, m in zip(own, market)]
            c8[s] = sqrt(sum(x * x for x in residual) / len(residual))

    c9 = _zero(symbols) if index < 756 else {s: closes[s][index] / closes[s][index - 756] - 1.0 for s in symbols}

    if index < 63:
        c10 = _zero(symbols)
    else:
        c10 = {}
        for s in symbols:
            path = rets[s][index - 63:index]
            denominator = sum(abs(x) for x in path)
            net = closes[s][index] / closes[s][index - 63] - 1.0
            c10[s] = abs(net) / denominator if denominator > 0 else 0.0

    if index < 146:
        c11 = _zero(symbols)
    else:
        c11 = {}
        for s in symbols:
            recent = sum(float(assets[s][j].volume) for j in range(index - 20, index + 1)) / 21.0
            prior = sum(float(assets[s][j].volume) for j in range(index - 146, index - 20)) / 126.0
            volume_ratio = recent / prior if prior > 0 else 0.0
            momentum = closes[s][index] / closes[s][index - 126] - 1.0
            c11[s] = momentum * volume_ratio

    return {"C7_LOW_MAX_21": c7, "C8_LOW_IDIO_VOL_273": c8, "C9_LONG_TERM_REVERSAL_756": c9, "C10_TREND_EFFICIENCY_63": c10, "C11_VOLUME_CONFIRMED_TREND_126": c11}

def candidate_targets_at(assets, index: int, *, symbols: Sequence[str]) -> dict[str, dict[str, float]]:
    scores = candidate_scores_at(assets, index, symbols=symbols)
    output = {}
    for name in CANDIDATES:
        if index < MIN_HISTORY_INDEX[name]:
            output[name] = _zero(symbols)
        else:
            output[name] = _top2(
                scores[name],
                symbols,
                name in {"C10_TREND_EFFICIENCY_63", "C11_VOLUME_CONFIRMED_TREND_126"},
            )
    return output

def build_candidate_bank(assets, *, symbols: Sequence[str]):
    _validate_assets(assets, symbols)
    out = {name: [] for name in CANDIDATES}
    for i in range(len(assets[symbols[0]])):
        targets = candidate_targets_at(assets, i, symbols=symbols)
        for name in CANDIDATES: out[name].append(targets[name])
    return {name: tuple(rows) for name, rows in out.items()}