"""Champion/challenger evidence contract; no autonomous production promotion."""
from __future__ import annotations
import math
from dataclasses import dataclass
from statistics import mean
from typing import Mapping, Sequence

class ChampionChallengerError(ValueError):
    """Raised for malformed evidence snapshots."""

@dataclass(frozen=True)
class EvidenceSnapshot:
    strategy_id: str
    research_drawdown_percent: float
    rolling_profit_factor: float | str
    holdout_return: float
    holdout_profit_factor: float | str
    stress_2x_holdout_return: float
    return_series: tuple[float, ...] = ()
    def __post_init__(self) -> None:
        if not self.strategy_id.strip():
            raise ChampionChallengerError("strategy_id must not be empty.")
        for name, value in (
            ("research_drawdown_percent", self.research_drawdown_percent),
            ("holdout_return", self.holdout_return),
            ("stress_2x_holdout_return", self.stress_2x_holdout_return),
        ):
            if not math.isfinite(float(value)):
                raise ChampionChallengerError(f"{name} must be finite.")
        for name, value in (
            ("rolling_profit_factor", self.rolling_profit_factor),
            ("holdout_profit_factor", self.holdout_profit_factor),
        ):
            if value != "inf" and not math.isfinite(float(value)):
                raise ChampionChallengerError(f"{name} must be finite or inf.")

@dataclass(frozen=True)
class ChallengerAssessment:
    status: str
    checks: Mapping[str, bool]
    reason: str

def pearson_correlation(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or len(a) < 2:
        raise ChampionChallengerError("Correlation needs equal series of length >= 2.")
    ma, mb = mean(a), mean(b)
    da, db = [x - ma for x in a], [x - mb for x in b]
    va, vb = sum(x * x for x in da), sum(x * x for x in db)
    if va == 0.0 or vb == 0.0:
        return 0.0
    return sum(x * y for x, y in zip(da, db)) / math.sqrt(va * vb)

def evaluate_challenger(champion: EvidenceSnapshot, challenger: EvidenceSnapshot, *, minimum_profit_factor: float = 1.0, maximum_challenger_drawdown_percent: float | None = None) -> ChallengerAssessment:
    if champion.strategy_id == challenger.strategy_id:
        raise ChampionChallengerError("Champion and challenger must differ.")
    if minimum_profit_factor <= 0.0:
        raise ChampionChallengerError("minimum_profit_factor must be > 0.")
    max_dd = champion.research_drawdown_percent if maximum_challenger_drawdown_percent is None else maximum_challenger_drawdown_percent
    def pf(value: float | str) -> float:
        return float("inf") if value == "inf" else float(value)
    checks = {
        "holdout_return_positive": challenger.holdout_return > 0.0,
        "holdout_profit_factor": pf(challenger.holdout_profit_factor) >= minimum_profit_factor,
        "rolling_profit_factor": pf(challenger.rolling_profit_factor) >= minimum_profit_factor,
        "stress_2x_nonnegative": challenger.stress_2x_holdout_return >= 0.0,
        "research_drawdown_within_limit": challenger.research_drawdown_percent <= max_dd,
    }
    passed = all(checks.values())
    return ChallengerAssessment(
        "EVIDENCE_ELIGIBLE" if passed else "NOT_ELIGIBLE",
        checks,
        "All predefined challenger evidence checks passed." if passed else "At least one predefined challenger evidence check failed.",
    )
