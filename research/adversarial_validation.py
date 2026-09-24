"""Deterministic adversarial diagnostics for research evidence."""
from __future__ import annotations
import math
import random
from dataclasses import dataclass

class AdversarialValidationError(ValueError):
    """Raised for invalid adversarial-test inputs."""

@dataclass(frozen=True)
class AdversarialSummary:
    name: str
    observation_count: int
    total_return: float
    max_drawdown_percent: float

def _validate(returns: tuple[float, ...]) -> None:
    if not returns or not all(math.isfinite(float(v)) for v in returns):
        raise AdversarialValidationError("returns must be non-empty and finite.")

def summarize_path(returns: tuple[float, ...]) -> AdversarialSummary:
    _validate(returns)
    equity = peak = 1.0
    max_dd = 0.0
    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
    return AdversarialSummary("baseline", len(returns), equity - 1.0, 100.0 * max_dd)

def delayed(returns: tuple[float, ...], periods: int) -> tuple[float, ...]:
    _validate(returns)
    if periods < 0:
        raise AdversarialValidationError("periods must be >= 0.")
    if periods >= len(returns):
        return tuple(0.0 for _ in returns)
    return tuple(0.0 for _ in range(periods)) + returns[:-periods] if periods else returns

def multiply_costs(returns: tuple[float, ...], *, extra_cost_per_period: float) -> tuple[float, ...]:
    _validate(returns)
    if extra_cost_per_period < 0.0:
        raise AdversarialValidationError("extra_cost_per_period must be >= 0.")
    return tuple(v - extra_cost_per_period for v in returns)

def clip_returns(returns: tuple[float, ...], *, absolute_limit: float) -> tuple[float, ...]:
    _validate(returns)
    if absolute_limit <= 0.0 or not math.isfinite(absolute_limit):
        raise AdversarialValidationError("absolute_limit must be finite and > 0.")
    return tuple(max(-absolute_limit, min(absolute_limit, v)) for v in returns)

def leave_one_out_total(returns: tuple[float, ...]) -> tuple[float, ...]:
    _validate(returns)
    return tuple(summarize_path(returns[:i] + returns[i + 1:]).total_return for i in range(len(returns)))

def sign_permutation_probability(
    returns: tuple[float, ...], *, trials: int = 1000, seed: int = 20260924
) -> float:
    _validate(returns)
    if trials < 100:
        raise AdversarialValidationError("trials must be >= 100.")
    observed = sum(returns)
    if observed <= 0.0:
        return 1.0
    rng = random.Random(seed)
    magnitudes = [abs(v) for v in returns]
    extreme = 0
    for _ in range(trials):
        trial = sum(m if rng.getrandbits(1) else -m for m in magnitudes)
        extreme += trial >= observed
    return (extreme + 1) / (trials + 1)
