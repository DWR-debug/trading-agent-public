"""Q067 fixed alpha-level exposure transformations.

This module contains only deterministic signal/portfolio transformations for the
Q067 design. It does not perform data acquisition, performance evaluation,
holdout selection, ranking or promotion.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from math import sqrt

Q067_SYMBOLS = (
    "ANSS",
    "ROP",
    "NVR",
    "ZION",
    "SLB",
    "EIX",
    "K",
    "CCL",
)
Q067_SLEEVES = (
    "A1_TSM_CONSENSUS",
    "A2_CS_MOMENTUM_TOP2",
    "A3_RESIDUAL_MOMENTUM_TOP2",
    "A5_LOW_BETA_TOP2",
    "A1B_52W_HIGH_TOP2",
    "A6_OVERNIGHT_TUGWAR_TOP2",
)

TARGET_CANDLES = 3500
RETURN_COUNT = TARGET_CANDLES - 2

E1_CORRELATION_LOOKBACK = 63
E1_ACTIVATION_THRESHOLD = 0.70
E1_ACTIVATION_CONSECUTIVE = 3
E1_RECOVERY_THRESHOLD = 0.50
E1_RECOVERY_CONSECUTIVE = 5
E1_EXPOSURE_MULTIPLIER = 0.50

E2_MIN_ABS_WEIGHT_CHANGE = 0.05


def fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _returns(closes: Sequence[float]) -> list[float]:
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]


def _beta(values: Sequence[float], market: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean_values = sum(values) / len(values)
    mean_market = sum(market) / len(market)
    variance = sum((x - mean_market) ** 2 for x in market)
    if variance <= 0.0:
        return 0.0
    return sum((x - mean_values) * (m - mean_market) for x, m in zip(values, market)) / variance


def _top2_weights(scores: Mapping[str, float], symbols: Sequence[str], reverse: bool = True) -> dict[str, float]:
    ordered = sorted(symbols, key=lambda symbol: ((-scores[symbol]) if reverse else scores[symbol], symbol))[:2]
    return {symbol: (0.5 if symbol in ordered else 0.0) for symbol in symbols}


def _prepare(assets: Mapping[str, Sequence[object]], symbols: Sequence[str]):
    missing = [symbol for symbol in symbols if symbol not in assets]
    if missing:
        raise ValueError(f"missing symbols: {missing}")
    lengths = {len(assets[symbol]) for symbol in symbols}
    if len(lengths) != 1:
        raise ValueError("alpha inputs must be aligned")
    closes = {symbol: [bar.close for bar in assets[symbol]] for symbol in symbols}
    returns = {symbol: _returns(closes[symbol]) for symbol in symbols}
    return closes, returns


def alpha_sleeve_targets_at(
    assets: Mapping[str, Sequence[object]],
    index: int,
    *,
    symbols: Sequence[str] = Q067_SYMBOLS,
    prepared=None,
) -> dict[str, dict[str, float]]:
    closes, returns = prepared if prepared is not None else _prepare(assets, symbols)

    scores_a1: dict[str, int] = {}
    for symbol in symbols:
        if index < 252:
            scores_a1[symbol] = 0
        else:
            scores_a1[symbol] = sum(
                1 if closes[symbol][index] / closes[symbol][lookback] > 1.0 else -1
                for lookback in (21, 63, 252)
            )
    active = [symbol for symbol in symbols if scores_a1[symbol] > 0]
    weight = 1.0 / len(active) if active else 0.0
    a1 = {symbol: (weight if symbol in active else 0.0) for symbol in symbols}

    anchor = index - 21
    if anchor < 252:
        a2 = {symbol: 0.0 for symbol in symbols}
    else:
        a2 = _top2_weights(
            {
                symbol: closes[symbol][anchor] / closes[symbol][anchor - 252] - 1.0
                for symbol in symbols
            },
            symbols,
        )

    if anchor < 273:
        a3 = {symbol: 0.0 for symbol in symbols}
        a5 = {symbol: 0.0 for symbol in symbols}
    else:
        start = anchor - 273
        end = anchor - 21
        market = [sum(returns[symbol][i] for symbol in symbols) / len(symbols) for i in range(start, end)]
        betas = {symbol: _beta(returns[symbol][start:end], market) for symbol in symbols}
        residual_scores = {
            symbol: sum(
                own - betas[symbol] * market_return
                for own, market_return in zip(returns[symbol][start:end], market)
            )
            for symbol in symbols
        }
        a3 = _top2_weights(residual_scores, symbols)
        a5 = _top2_weights(betas, symbols, reverse=False)

    if anchor < 252:
        a1b = {symbol: 0.0 for symbol in symbols}
    else:
        anchor_scores = {}
        for symbol in symbols:
            high = max(closes[symbol][anchor - 251 : anchor + 1])
            anchor_scores[symbol] = closes[symbol][anchor] / high if high else 0.0
        a1b = _top2_weights(anchor_scores, symbols)

    if index < 21:
        a6 = {symbol: 0.0 for symbol in symbols}
    else:
        tug_scores = {}
        for symbol in symbols:
            bars = assets[symbol]
            count = 0
            for j in range(index - 20, index + 1):
                overnight = bars[j].open / bars[j - 1].close - 1.0
                daytime = bars[j].close / bars[j].open - 1.0
                if overnight > 0.0 and daytime < 0.0:
                    count += 1
            tug_scores[symbol] = float(count)
        a6 = _top2_weights(tug_scores, symbols)

    return {
        "A1_TSM_CONSENSUS": a1,
        "A2_CS_MOMENTUM_TOP2": a2,
        "A3_RESIDUAL_MOMENTUM_TOP2": a3,
        "A5_LOW_BETA_TOP2": a5,
        "A1B_52W_HIGH_TOP2": a1b,
        "A6_OVERNIGHT_TUGWAR_TOP2": a6,
    }


def build_alpha_sleeves(
    assets: Mapping[str, Sequence[object]],
    *,
    symbols: Sequence[str] = Q067_SYMBOLS,
) -> dict[str, tuple[dict[str, float], ...]]:
    prepared = _prepare(assets, symbols)
    outputs = {name: [] for name in Q067_SLEEVES}
    for index in range(TARGET_CANDLES):
        current = alpha_sleeve_targets_at(assets, index, symbols=symbols, prepared=prepared)
        for name in Q067_SLEEVES:
            outputs[name].append(current[name])
    return {name: tuple(rows) for name, rows in outputs.items()}


def equal_weight_ensemble(
    sleeves: Mapping[str, Sequence[Mapping[str, float]]],
    *,
    symbols: Sequence[str] = Q067_SYMBOLS,
) -> tuple[dict[str, float], ...]:
    missing = [name for name in Q067_SLEEVES if name not in sleeves]
    if missing:
        raise ValueError(f"missing alpha sleeves: {missing}")
    length = len(next(iter(sleeves.values())))
    if any(len(sleeves[name]) != length for name in Q067_SLEEVES):
        raise ValueError("sleeve paths must have equal length")
    return tuple(
        {
            symbol: sum(float(sleeves[name][i].get(symbol, 0.0)) for name in Q067_SLEEVES) / len(Q067_SLEEVES)
            for symbol in symbols
        }
        for i in range(length)
    )


def sleeve_period_returns(
    assets: Mapping[str, Sequence[object]],
    sleeves: Mapping[str, Sequence[Mapping[str, float]]],
    *,
    symbols: Sequence[str] = Q067_SYMBOLS,
) -> dict[str, list[float]]:
    result: dict[str, list[float]] = {name: [] for name in Q067_SLEEVES}
    for i in range(RETURN_COUNT):
        for name in Q067_SLEEVES:
            result[name].append(
                sum(
                    float(sleeves[name][i].get(symbol, 0.0))
                    * (assets[symbol][i + 2].open / assets[symbol][i + 1].open - 1.0)
                    for symbol in symbols
                )
            )
    return result


def sleeve_return_history_at(
    assets: Mapping[str, Sequence[object]],
    decision_index: int,
    *,
    symbols: Sequence[str] = Q067_SYMBOLS,
    lookback: int = E1_CORRELATION_LOOKBACK,
) -> dict[str, list[float]]:
    if decision_index < lookback + 1:
        raise ValueError("decision index lacks the required completed history")
    prepared = _prepare(assets, symbols)
    result = {name: [] for name in Q067_SLEEVES}
    for i in range(decision_index - lookback - 1, decision_index - 1):
        current = alpha_sleeve_targets_at(assets, i, symbols=symbols, prepared=prepared)
        for name in Q067_SLEEVES:
            result[name].append(
                sum(
                    current[name].get(symbol, 0.0)
                    * (assets[symbol][i + 2].open / assets[symbol][i + 1].open - 1.0)
                    for symbol in symbols
                )
            )
    return result


def _pearson(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("correlation inputs must have equal non-zero length")
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum((a - mean_left) * (b - mean_right) for a, b in zip(left, right))
    denominator = sqrt(sum((a - mean_left) ** 2 for a in left)) * sqrt(sum((b - mean_right) ** 2 for b in right))
    return 0.0 if denominator <= 0.0 else numerator / denominator


def mean_pairwise_correlation(
    history: Mapping[str, Sequence[float]],
    *,
    sleeve_names: Sequence[str] = Q067_SLEEVES,
) -> float:
    if any(name not in history for name in sleeve_names):
        raise ValueError("all configured sleeves are required")
    if any(len(history[name]) != E1_CORRELATION_LOOKBACK for name in sleeve_names):
        raise ValueError("correlation history length mismatch")
    values = []
    for left_index, left_name in enumerate(sleeve_names):
        for right_name in sleeve_names[left_index + 1 :]:
            values.append(_pearson(history[left_name], history[right_name]))
    return sum(values) / len(values)


def common_mode_multipliers(
    sleeve_returns: Mapping[str, Sequence[float]],
    *,
    decision_count: int = TARGET_CANDLES,
) -> tuple[float, ...]:
    if any(len(sleeve_returns[name]) < decision_count - 2 for name in Q067_SLEEVES):
        raise ValueError("sleeve return histories are too short")

    active = False
    high_streak = 0
    low_streak = 0
    multipliers: list[float] = []

    for decision_index in range(decision_count):
        if decision_index < E1_CORRELATION_LOOKBACK + 1:
            multipliers.append(1.0)
            continue

        history = {
            name: list(
                sleeve_returns[name][
                    decision_index - E1_CORRELATION_LOOKBACK - 1 : decision_index - 1
                ]
            )
            for name in Q067_SLEEVES
        }
        mean_corr = mean_pairwise_correlation(history)

        high_streak = high_streak + 1 if mean_corr >= E1_ACTIVATION_THRESHOLD else 0
        low_streak = low_streak + 1 if mean_corr <= E1_RECOVERY_THRESHOLD else 0

        if not active and high_streak >= E1_ACTIVATION_CONSECUTIVE:
            active = True
        if active and low_streak >= E1_RECOVERY_CONSECUTIVE:
            active = False

        multipliers.append(E1_EXPOSURE_MULTIPLIER if active else 1.0)

    return tuple(multipliers)


def apply_common_mode_throttle(
    aggregate_weights: Sequence[Mapping[str, float]],
    sleeve_returns: Mapping[str, Sequence[float]],
    *,
    symbols: Sequence[str] = Q067_SYMBOLS,
) -> tuple[dict[str, float], ...]:
    multipliers = common_mode_multipliers(sleeve_returns, decision_count=len(aggregate_weights))
    return tuple(
        {
            symbol: float(aggregate_weights[i].get(symbol, 0.0)) * multipliers[i]
            for symbol in symbols
        }
        for i in range(len(aggregate_weights))
    )


def apply_turnover_hysteresis(
    aggregate_weights: Sequence[Mapping[str, float]],
    *,
    symbols: Sequence[str] = Q067_SYMBOLS,
) -> tuple[dict[str, float], ...]:
    previous = {symbol: 0.0 for symbol in symbols}
    out: list[dict[str, float]] = []

    for target_map in aggregate_weights:
        current: dict[str, float] = {}
        for symbol in symbols:
            target = float(target_map.get(symbol, 0.0))
            prior = previous[symbol]
            if (prior == 0.0 and target != 0.0) or (prior != 0.0 and target == 0.0):
                current[symbol] = target
            elif abs(target - prior) >= E2_MIN_ABS_WEIGHT_CHANGE:
                current[symbol] = target
            else:
                current[symbol] = prior
        out.append(current)
        previous = current

    return tuple(out)
