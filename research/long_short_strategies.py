"""Long/short research signal and exposure helpers.

These helpers are deliberately separate from the production StrategyEngine.
They produce signed research exposures but do not execute trades.
"""

from __future__ import annotations

import math


def sma_50_200_long_short_signal(closes: tuple[float, ...] | list[float]) -> tuple[int, ...]:
    """Return +1 for bullish 50/200 SMA and -1 for bearish 50/200 SMA."""
    if len(closes) < 200:
        return tuple(0 for _ in closes)
    result = [0] * len(closes)
    for index in range(199, len(closes)):
        fast = sum(closes[index - 49:index + 1]) / 50.0
        slow = sum(closes[index - 199:index + 1]) / 200.0
        result[index] = 1 if fast > slow else -1 if fast < slow else 0
    return tuple(result)


def tsm_ensemble_long_short_signal(
    closes: tuple[float, ...] | list[float],
    lookbacks: tuple[int, ...] = (63, 126, 252),
) -> tuple[int, ...]:
    """Majority vote across fixed TSM horizons, symmetrically long/short."""
    if not lookbacks or any(value < 1 for value in lookbacks):
        raise ValueError("lookbacks must contain positive values.")
    minimum = max(lookbacks)
    result = [0] * len(closes)
    for index in range(minimum, len(closes)):
        votes = 0
        for lookback in lookbacks:
            change = closes[index] / closes[index - lookback] - 1.0
            votes += 1 if change > 0 else -1 if change < 0 else 0
        result[index] = 1 if votes > 0 else -1 if votes < 0 else 0
    return tuple(result)


def annualized_volatility(
    closes: tuple[float, ...] | list[float],
    index: int,
    window: int = 63,
) -> float | None:
    """Point-in-time annualized close-to-close volatility estimate."""
    if window < 2 or index < window:
        return None
    returns = []
    for cursor in range(index - window + 1, index + 1):
        previous = closes[cursor - 1]
        current = closes[cursor]
        if previous <= 0 or current <= 0:
            return None
        returns.append(current / previous - 1.0)
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / len(returns)
    return math.sqrt(variance) * math.sqrt(252.0)


def build_signed_exposure(
    closes: tuple[float, ...] | list[float],
    signal: tuple[int, ...] | list[int],
    *,
    target_annualized_vol: float = 0.10,
    volatility_window: int = 63,
    gross_exposure_cap: float = 1.0,
    rebalance_periods: int = 21,
) -> tuple[float, ...]:
    """Convert a signed signal to conservative, volatility-scaled exposure."""
    if len(closes) != len(signal):
        raise ValueError("closes and signal must have equal length.")
    if target_annualized_vol < 0 or gross_exposure_cap < 0 or rebalance_periods < 1:
        raise ValueError("Invalid exposure configuration.")

    output = [0.0] * len(closes)
    current = 0.0
    previous_signal = 0
    for index, target_signal in enumerate(signal):
        if target_signal == 0:
            current = 0.0
        elif target_signal != previous_signal or index % rebalance_periods == 0:
            vol = annualized_volatility(closes, index, volatility_window)
            if vol is None or vol <= 0:
                current = 0.0
            else:
                current = target_signal * min(
                    gross_exposure_cap,
                    target_annualized_vol / vol,
                )
        output[index] = current
        previous_signal = target_signal
    return tuple(output)
