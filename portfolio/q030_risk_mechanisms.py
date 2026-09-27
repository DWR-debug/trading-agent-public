"""Q030 risk/stability mechanism primitives.

Performance-free, point-in-time-safe building blocks for Q034 validation.
No signal generation, order execution, or asset selection.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean
from typing import Mapping, Sequence


RISK_A_WINDOW = 63
RISK_A_TARGET_VOL = 0.10
RISK_A_MIN_SCALE = 0.25
RISK_A_MAX_SCALE = 1.0

RISK_B_STATE_1_DD = 0.05
RISK_B_STATE_1_SCALE = 0.50
RISK_B_STATE_2_DD = 0.08
RISK_B_STATE_2_SCALE = 0.25
RISK_B_RECOVERY_DD = 0.03
RISK_B_RECOVERY_SESSIONS = 5

RISK_C_WINDOW = 63
RISK_C_TRIGGER = 0.60
RISK_C_SCALE = 0.50

RISK_D_ATR_WINDOW = 20
RISK_D_ATR_MULTIPLE = 3.0


class MechanismInputError(ValueError):
    pass


def sleeve_volatility_scale(
    completed_returns: Sequence[float],
    *,
    target_vol: float = RISK_A_TARGET_VOL,
    window: int = RISK_A_WINDOW,
    minimum_scale: float = RISK_A_MIN_SCALE,
    maximum_scale: float = RISK_A_MAX_SCALE,
) -> float:
    if window < 2 or target_vol <= 0.0:
        raise MechanismInputError("invalid volatility parameters")
    if minimum_scale <= 0.0 or maximum_scale < minimum_scale:
        raise MechanismInputError("invalid exposure scale bounds")
    if len(completed_returns) < window:
        return maximum_scale
    sample = [float(x) for x in completed_returns[-window:]]
    if not all(math.isfinite(x) for x in sample):
        raise MechanismInputError("returns must be finite")
    mu = mean(sample)
    variance = sum((x - mu) ** 2 for x in sample) / len(sample)
    realized = math.sqrt(variance * 252.0)
    if realized <= 0.0:
        return maximum_scale
    raw = target_vol / realized
    return min(max(raw, minimum_scale), maximum_scale)


def drawdown_throttle_scale(
    completed_returns: Sequence[float],
    *,
    state_1_dd: float = RISK_B_STATE_1_DD,
    state_1_scale: float = RISK_B_STATE_1_SCALE,
    state_2_dd: float = RISK_B_STATE_2_DD,
    state_2_scale: float = RISK_B_STATE_2_SCALE,
    recovery_dd: float = RISK_B_RECOVERY_DD,
    recovery_sessions: int = RISK_B_RECOVERY_SESSIONS,
) -> float:
    if not (0.0 < state_1_dd < state_2_dd):
        raise MechanismInputError("drawdown thresholds must be ordered and positive")
    if not (0.0 < recovery_dd < state_1_dd):
        raise MechanismInputError("recovery drawdown must be below first state")
    if recovery_sessions < 1:
        raise MechanismInputError("recovery_sessions must be positive")
    if not (0.0 < state_2_scale <= state_1_scale <= 1.0):
        raise MechanismInputError("invalid drawdown scale ordering")

    equity = 1.0
    peak = 1.0
    state = 0
    recovery_count = 0

    for raw_return in completed_returns:
        value = float(raw_return)
        if not math.isfinite(value) or value <= -1.0:
            raise MechanismInputError("returns must be finite and greater than -100%")
        equity *= 1.0 + value
        peak = max(peak, equity)
        drawdown = 1.0 - equity / peak if peak > 0.0 else 1.0

        if state > 0:
            if drawdown <= recovery_dd:
                recovery_count += 1
            else:
                recovery_count = 0
            if recovery_count >= recovery_sessions:
                state = 0
                recovery_count = 0

        if state == 0 and drawdown >= state_2_dd:
            state = 2
            recovery_count = 0
        elif state == 0 and drawdown >= state_1_dd:
            state = 1
            recovery_count = 0
        elif state == 1 and drawdown >= state_2_dd:
            state = 2
            recovery_count = 0

    return (1.0, state_1_scale, state_2_scale)[state]


def _pearson(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or len(a) < 2:
        raise MechanismInputError("correlation needs equal series with >=2 values")
    ma, mb = mean(a), mean(b)
    da = [x - ma for x in a]
    db = [x - mb for x in b]
    va = sum(x * x for x in da)
    vb = sum(x * x for x in db)
    if va == 0.0 or vb == 0.0:
        return 0.0
    return sum(x * y for x, y in zip(da, db)) / math.sqrt(va * vb)


def common_mode_exposure_scale(
    returns_by_asset: Mapping[str, Sequence[float]],
    active_weights: Mapping[str, float],
    *,
    window: int = RISK_C_WINDOW,
    trigger: float = RISK_C_TRIGGER,
    triggered_scale: float = RISK_C_SCALE,
) -> float:
    active = tuple(sorted(symbol for symbol, weight in active_weights.items() if float(weight) > 0.0))
    if len(active) < 2:
        return 1.0
    if any(symbol not in returns_by_asset for symbol in active):
        raise MechanismInputError("active asset return series missing")
    if len({len(returns_by_asset[s]) for s in active}) != 1:
        raise MechanismInputError("active series must share length")
    if len(next(iter((returns_by_asset[s] for s in active)), ())) < window:
        return 1.0
    samples = {s: [float(x) for x in returns_by_asset[s][-window:]] for s in active}
    if any(not math.isfinite(x) for vals in samples.values() for x in vals):
        raise MechanismInputError("returns must be finite")
    correlations = [
        _pearson(samples[a], samples[b])
        for i, a in enumerate(active)
        for b in active[i + 1:]
    ]
    mean_corr = mean(correlations)
    return triggered_scale if mean_corr >= trigger else 1.0


@dataclass(frozen=True)
class Bar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float


def atr_value(bars: Sequence[Bar], index: int, *, window: int = RISK_D_ATR_WINDOW) -> float | None:
    if window < 1 or index < window:
        return None
    ranges: list[float] = []
    for cursor in range(index - window + 1, index + 1):
        previous_close = bars[cursor - 1].close
        current = bars[cursor]
        if current.high < current.low or current.close <= 0.0:
            raise MechanismInputError("invalid OHLC bar")
        ranges.append(max(
            current.high - current.low,
            abs(current.high - previous_close),
            abs(current.low - previous_close),
        ))
    return sum(ranges) / window


def position_lifecycle_exit_trigger(
    bars: Sequence[Bar],
    decision_index: int,
    *,
    highest_close_since_entry: float,
    window: int = RISK_D_ATR_WINDOW,
    multiple: float = RISK_D_ATR_MULTIPLE,
) -> bool:
    if decision_index < 0 or decision_index >= len(bars):
        raise MechanismInputError("decision index out of range")
    if highest_close_since_entry <= 0.0 or multiple <= 0.0:
        raise MechanismInputError("invalid lifecycle inputs")
    atr = atr_value(bars, decision_index, window=window)
    if atr is None or atr <= 0.0:
        return False
    return bars[decision_index].close < highest_close_since_entry - multiple * atr
