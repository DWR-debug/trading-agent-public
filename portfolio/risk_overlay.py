"""Portfolio-level risk overlay primitives; no alpha generation or order execution."""
from __future__ import annotations
import math
from dataclasses import dataclass
from statistics import mean
from typing import Mapping, Sequence

class RiskOverlayError(ValueError):
    """Raised when portfolio risk inputs are invalid."""

@dataclass(frozen=True)
class RiskScaleDecision:
    scale: float
    realized_vol: float | None
    reason: str

def realized_volatility(returns: Sequence[float], *, annualization: float = 252.0, window: int = 63) -> float | None:
    if window < 2 or annualization <= 0.0:
        raise RiskOverlayError("window must be >= 2 and annualization must be > 0.")
    if len(returns) < window:
        return None
    sample = [float(x) for x in returns[-window:]]
    if not all(math.isfinite(x) for x in sample):
        raise RiskOverlayError("returns must be finite.")
    m = mean(sample)
    return math.sqrt(sum((x - m) ** 2 for x in sample) / len(sample) * annualization)

def lagged_volatility_scale(historical_returns: Sequence[float], *, target_vol: float = 0.10, window: int = 63) -> RiskScaleDecision:
    if target_vol <= 0.0 or not math.isfinite(target_vol):
        raise RiskOverlayError("target_vol must be finite and > 0.")
    vol = realized_volatility(historical_returns, window=window)
    if vol is None:
        return RiskScaleDecision(1.0, None, "INSUFFICIENT_HISTORY")
    if vol <= target_vol or vol == 0.0:
        return RiskScaleDecision(1.0, vol, "WITHIN_TARGET")
    return RiskScaleDecision(min(1.0, target_vol / vol), vol, "ABOVE_TARGET")

def exposure_concentration(weights: Mapping[str, float]) -> float:
    if not weights:
        return 0.0
    if any(not math.isfinite(float(v)) or v < 0.0 for v in weights.values()):
        raise RiskOverlayError("weights must be finite and non-negative.")
    total = sum(weights.values())
    if total <= 0.0:
        return 0.0
    return sum((v / total) ** 2 for v in weights.values())

def pearson_correlation(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or len(a) < 2:
        raise RiskOverlayError("Correlation needs equal series of length >= 2.")
    ma, mb = mean(a), mean(b)
    da, db = [x - ma for x in a], [x - mb for x in b]
    va, vb = sum(x * x for x in da), sum(x * x for x in db)
    if va == 0.0 or vb == 0.0:
        return 0.0
    return sum(x * y for x, y in zip(da, db)) / math.sqrt(va * vb)

def correlation_matrix(returns_by_strategy: Mapping[str, Sequence[float]]) -> dict[str, dict[str, float]]:
    names = tuple(sorted(returns_by_strategy))
    if not names:
        return {}
    if len({len(returns_by_strategy[n]) for n in names}) != 1:
        raise RiskOverlayError("All strategy return series must have equal length.")
    return {a: {b: 1.0 if a == b else pearson_correlation(returns_by_strategy[a], returns_by_strategy[b]) for b in names} for a in names}

def drawdown_profile(returns: Sequence[float]) -> dict[str, float]:
    if not returns:
        raise RiskOverlayError("returns must not be empty.")
    equity = peak = 1.0
    max_dd = 0.0
    underwater = longest = 0
    for value in returns:
        if not math.isfinite(float(value)):
            raise RiskOverlayError("returns must be finite.")
        equity *= 1.0 + value
        peak = max(peak, equity)
        if equity < peak:
            underwater += 1
            longest = max(longest, underwater)
        else:
            underwater = 0
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
    return {"max_drawdown_percent": 100.0 * max_dd, "longest_underwater_periods": float(longest), "terminal_return": equity - 1.0}

def joint_loss_rate(returns_by_strategy: Mapping[str, Sequence[float]], *, threshold: float = 0.0) -> float:
    if not returns_by_strategy:
        return 0.0
    lengths = {len(v) for v in returns_by_strategy.values()}
    if len(lengths) != 1 or not lengths or next(iter(lengths)) == 0:
        raise RiskOverlayError("Return series must share a non-empty length.")
    n = next(iter(lengths))
    names = tuple(returns_by_strategy)
    return sum(all(returns_by_strategy[name][i] < threshold for name in names) for i in range(n)) / n
