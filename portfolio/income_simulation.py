"""Research-only simulation of profit-dependent portfolio withdrawals.

No broker integration and no order execution. The simulator is designed to
measure whether a strategy's equity path can support recurring withdrawals
while preserving a protected capital base.
"""

from dataclasses import dataclass


class IncomeSimulationError(ValueError):
    """Raised when an income-simulation contract is invalid."""


@dataclass(frozen=True)
class IncomePolicy:
    protected_capital_eur: float = 500.0
    payout_fraction: float = 1.0
    reserve_eur: float = 0.0
    payout_interval_periods: int = 21

    def __post_init__(self) -> None:
        if self.protected_capital_eur <= 0:
            raise IncomeSimulationError("Protected capital must be > 0.")
        if not 0.0 <= self.payout_fraction <= 1.0:
            raise IncomeSimulationError("Payout fraction must be between 0 and 1.")
        if self.reserve_eur < 0:
            raise IncomeSimulationError("Reserve must not be negative.")
        if self.reserve_eur >= self.protected_capital_eur:
            raise IncomeSimulationError("Reserve must be smaller than protected capital.")
        if self.payout_interval_periods < 1:
            raise IncomeSimulationError("Payout interval must be at least 1 period.")


@dataclass(frozen=True)
class IncomeObservation:
    period_index: int
    equity_before_payout_eur: float
    payout_eur: float
    equity_after_payout_eur: float
    high_water_mark_eur: float


@dataclass(frozen=True)
class IncomeSimulationResult:
    final_equity_eur: float
    total_payout_eur: float
    payout_count: int
    minimum_equity_eur: float
    maximum_drawdown_percent: float
    observations: tuple[IncomeObservation, ...]


def simulate_income(
    returns: tuple[float, ...],
    policy: IncomePolicy | None = None,
) -> IncomeSimulationResult:
    """Replay a fixed return series with a conservative high-water payout rule.

    Returns are decimal portfolio returns (e.g. 0.01 = +1%) and must be ordered
    chronologically. A payout can only come from a new equity high above the
    protected capital plus reserve. The pre-payout high-water mark is retained,
    so temporary gains cannot be repeatedly withdrawn.
    """
    policy = policy or IncomePolicy()

    equity = policy.protected_capital_eur
    high_water_mark = equity
    total_payout = 0.0
    observations: list[IncomeObservation] = []
    minimum_equity = equity
    peak_for_drawdown = equity
    maximum_drawdown = 0.0

    for period_index, period_return in enumerate(returns, start=1):
        if period_return <= -1.0:
            raise IncomeSimulationError("Returns must be greater than -100%.")

        equity *= 1.0 + period_return
        minimum_equity = min(minimum_equity, equity)
        peak_for_drawdown = max(peak_for_drawdown, equity)
        if peak_for_drawdown > 0.0:
            maximum_drawdown = max(
                maximum_drawdown,
                1.0 - equity / peak_for_drawdown,
            )

        payout = 0.0
        if period_index % policy.payout_interval_periods == 0:
            gain_above_hwm = max(0.0, equity - high_water_mark)
            available_above_floor = max(
                0.0,
                equity - policy.protected_capital_eur - policy.reserve_eur,
            )
            payout = min(
                gain_above_hwm * policy.payout_fraction,
                available_above_floor,
            )

            if payout > 0.0:
                equity -= payout
                total_payout += payout
                high_water_mark = max(high_water_mark, equity + payout)
            else:
                high_water_mark = max(high_water_mark, equity)

            observations.append(
                IncomeObservation(
                    period_index=period_index,
                    equity_before_payout_eur=equity + payout,
                    payout_eur=payout,
                    equity_after_payout_eur=equity,
                    high_water_mark_eur=high_water_mark,
                )
            )
        else:
            high_water_mark = max(high_water_mark, equity)

    return IncomeSimulationResult(
        final_equity_eur=equity,
        total_payout_eur=total_payout,
        payout_count=sum(obs.payout_eur > 0.0 for obs in observations),
        minimum_equity_eur=minimum_equity,
        maximum_drawdown_percent=maximum_drawdown * 100.0,
        observations=tuple(observations),
    )
