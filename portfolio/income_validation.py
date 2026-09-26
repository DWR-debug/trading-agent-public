"""Deterministic accounting evaluator for future validated return series.

This module is deliberately downstream of research evidence. It accepts one
fixed chronological return series and evaluates whether that *given* series
could support conservative profit-dependent withdrawals.

It does not select strategies, tune parameters from outcomes, access holdouts,
or interact with brokers/orders.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


class IncomeValidationError(ValueError):
    """Raised when an income-validation contract is invalid."""


@dataclass(frozen=True)
class IncomeValidationPolicy:
    """Fixed accounting assumptions for an income-viability replay."""

    protected_capital_eur: float = 500.0
    reserve_eur: float = 0.0
    payout_fraction: float = 0.50
    payout_interval_periods: int = 21
    fee_fraction_per_period: float = 0.0
    slippage_fraction_per_period: float = 0.0
    lower_quantile: float = 0.10
    sequence_window_periods: int | None = 252

    def __post_init__(self) -> None:
        numeric = (
            self.protected_capital_eur,
            self.reserve_eur,
            self.payout_fraction,
            self.fee_fraction_per_period,
            self.slippage_fraction_per_period,
            self.lower_quantile,
        )
        if any(not math.isfinite(float(value)) for value in numeric):
            raise IncomeValidationError("Policy values must be finite.")
        if self.protected_capital_eur <= 0.0:
            raise IncomeValidationError("Protected capital must be > 0.")
        if self.reserve_eur < 0.0:
            raise IncomeValidationError("Reserve must not be negative.")
        if self.payout_fraction < 0.0 or self.payout_fraction > 1.0:
            raise IncomeValidationError("Payout fraction must be between 0 and 1.")
        if self.payout_interval_periods < 1:
            raise IncomeValidationError("Payout interval must be at least 1 period.")
        if self.fee_fraction_per_period < 0.0:
            raise IncomeValidationError("Fee fraction must not be negative.")
        if self.slippage_fraction_per_period < 0.0:
            raise IncomeValidationError("Slippage fraction must not be negative.")
        if (
            self.fee_fraction_per_period + self.slippage_fraction_per_period
            >= 1.0
        ):
            raise IncomeValidationError("Fee plus slippage must be < 100% per period.")
        if self.lower_quantile < 0.0 or self.lower_quantile > 1.0:
            raise IncomeValidationError("lower_quantile must be between 0 and 1.")
        if (
            self.sequence_window_periods is not None
            and self.sequence_window_periods < 1
        ):
            raise IncomeValidationError("Sequence window must be >= 1 period.")

    @property
    def capital_floor_eur(self) -> float:
        return self.protected_capital_eur + self.reserve_eur

    @property
    def total_cost_fraction_per_period(self) -> float:
        return self.fee_fraction_per_period + self.slippage_fraction_per_period


@dataclass(frozen=True)
class PayoutObservation:
    """One scheduled payout checkpoint, including zero-payout checkpoints."""

    period_index: int
    equity_before_payout_eur: float
    high_water_mark_before_eur: float
    distributable_above_hwm_eur: float
    payout_eur: float
    equity_after_payout_eur: float


@dataclass(frozen=True)
class SequenceScenario:
    """Fixed-length historical start-point replay used only for sequence risk."""

    start_period_index: int
    window_periods: int
    total_payout_eur: float
    final_equity_eur: float
    minimum_equity_eur: float
    maximum_drawdown_percent: float
    zero_payout_fraction: float
    floor_violation_count: int


@dataclass(frozen=True)
class IncomeValidationResult:
    """Deterministic viability metrics for one fixed return series."""

    initial_capital_eur: float
    final_equity_eur: float
    total_payout_eur: float
    payout_count: int
    scheduled_payout_period_count: int
    zero_payout_periods: int
    zero_payout_fraction: float
    median_scheduled_payout_eur: float
    lower_quantile_scheduled_payout_eur: float
    longest_no_payout_periods: int
    minimum_equity_eur: float
    minimum_post_payout_equity_eur: float
    capital_floor_eur: float
    floor_violation_count: int
    minimum_floor_headroom_eur: float
    maximum_drawdown_percent_after_withdrawals: float
    total_cost_eur: float
    sequence_scenarios: tuple[SequenceScenario, ...]

    @property
    def sequence_start_count(self) -> int:
        return len(self.sequence_scenarios)

    @property
    def sequence_worst_total_payout_eur(self) -> float | None:
        if not self.sequence_scenarios:
            return None
        return min(item.total_payout_eur for item in self.sequence_scenarios)

    @property
    def sequence_lower_quantile_total_payout_eur(self) -> float | None:
        if not self.sequence_scenarios:
            return None
        return _quantile(
            [item.total_payout_eur for item in self.sequence_scenarios],
            0.10,
        )

    @property
    def sequence_worst_drawdown_percent(self) -> float | None:
        if not self.sequence_scenarios:
            return None
        return max(
            item.maximum_drawdown_percent
            for item in self.sequence_scenarios
        )


def _validate_returns(returns: Sequence[float]) -> tuple[float, ...]:
    normalized = tuple(float(value) for value in returns)
    for value in normalized:
        if not math.isfinite(value):
            raise IncomeValidationError("Returns must be finite.")
        if value <= -1.0:
            raise IncomeValidationError("Returns must be greater than -100%.")
    return normalized


def _quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _longest_zero_streak(observations: Sequence[PayoutObservation]) -> int:
    longest = 0
    current = 0
    for observation in observations:
        if observation.payout_eur <= 1e-12:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _replay(
    returns: tuple[float, ...],
    policy: IncomeValidationPolicy,
) -> IncomeValidationResult:
    equity = policy.protected_capital_eur
    high_water_mark = equity
    minimum_equity = equity
    minimum_post_payout_equity = equity
    peak_equity = equity
    maximum_drawdown = 0.0
    total_payout = 0.0
    total_cost = 0.0
    floor_violations = 0
    minimum_floor_headroom = equity - policy.capital_floor_eur
    observations: list[PayoutObservation] = []

    for period_index, gross_return in enumerate(returns, start=1):
        equity_before = equity
        gross_equity = equity_before * (1.0 + gross_return)
        cost_eur = gross_equity * policy.total_cost_fraction_per_period
        total_cost += cost_eur
        equity = gross_equity - cost_eur

        minimum_equity = min(minimum_equity, equity)
        peak_equity = max(peak_equity, equity)
        if peak_equity > 0.0:
            maximum_drawdown = max(
                maximum_drawdown,
                1.0 - equity / peak_equity,
            )

        floor_headroom = equity - policy.capital_floor_eur
        minimum_floor_headroom = min(minimum_floor_headroom, floor_headroom)
        if equity < policy.capital_floor_eur - 1e-12:
            floor_violations += 1

        payout = 0.0
        if period_index % policy.payout_interval_periods == 0:
            high_water_mark_before = high_water_mark
            distributable = max(0.0, equity - high_water_mark)
            payout = distributable * policy.payout_fraction
            payout = min(
                payout,
                max(0.0, equity - policy.capital_floor_eur),
            )
            if payout > 0.0:
                equity -= payout
                total_payout += payout

            minimum_post_payout_equity = min(
                minimum_post_payout_equity,
                equity,
            )
            high_water_mark = max(high_water_mark, equity + payout)
            observations.append(
                PayoutObservation(
                    period_index=period_index,
                    equity_before_payout_eur=equity + payout,
                    high_water_mark_before_eur=high_water_mark_before,
                    distributable_above_hwm_eur=distributable,
                    payout_eur=payout,
                    equity_after_payout_eur=equity,
                )
            )
        else:
            high_water_mark = max(high_water_mark, equity)
            minimum_post_payout_equity = min(
                minimum_post_payout_equity,
                equity,
            )

    scheduled_count = len(observations)
    payout_count = sum(item.payout_eur > 1e-12 for item in observations)
    zero_payout_periods = scheduled_count - payout_count
    payout_values = [item.payout_eur for item in observations]

    return IncomeValidationResult(
        initial_capital_eur=policy.protected_capital_eur,
        final_equity_eur=equity,
        total_payout_eur=total_payout,
        payout_count=payout_count,
        scheduled_payout_period_count=scheduled_count,
        zero_payout_periods=zero_payout_periods,
        zero_payout_fraction=(
            zero_payout_periods / scheduled_count if scheduled_count else 0.0
        ),
        median_scheduled_payout_eur=_quantile(payout_values, 0.50),
        lower_quantile_scheduled_payout_eur=_quantile(
            payout_values,
            policy.lower_quantile,
        ),
        longest_no_payout_periods=_longest_zero_streak(observations),
        minimum_equity_eur=minimum_equity,
        minimum_post_payout_equity_eur=minimum_post_payout_equity,
        capital_floor_eur=policy.capital_floor_eur,
        floor_violation_count=floor_violations,
        minimum_floor_headroom_eur=minimum_floor_headroom,
        maximum_drawdown_percent_after_withdrawals=maximum_drawdown * 100.0,
        total_cost_eur=total_cost,
        sequence_scenarios=(),
    )


def evaluate_sequence_risk(
    returns: Sequence[float],
    policy: IncomeValidationPolicy | None = None,
) -> tuple[SequenceScenario, ...]:
    """Replay equal-length historical start points without ranking strategies."""
    policy = policy or IncomeValidationPolicy()
    values = _validate_returns(returns)
    window = policy.sequence_window_periods
    if window is None or len(values) < window:
        return ()

    scenarios: list[SequenceScenario] = []
    for start in range(0, len(values) - window + 1):
        result = _replay(values[start : start + window], policy)
        scenarios.append(
            SequenceScenario(
                start_period_index=start + 1,
                window_periods=window,
                total_payout_eur=result.total_payout_eur,
                final_equity_eur=result.final_equity_eur,
                minimum_equity_eur=result.minimum_equity_eur,
                maximum_drawdown_percent=(
                    result.maximum_drawdown_percent_after_withdrawals
                ),
                zero_payout_fraction=result.zero_payout_fraction,
                floor_violation_count=result.floor_violation_count,
            )
        )
    return tuple(scenarios)


def evaluate_income_viability(
    returns: Sequence[float],
    policy: IncomeValidationPolicy | None = None,
) -> IncomeValidationResult:
    """Evaluate one fixed chronological return series under fixed accounting rules.

    The evaluator never chooses among return series or policies. It only computes
    deterministic accounting and sequence-risk metrics for the supplied inputs.
    """
    policy = policy or IncomeValidationPolicy()
    values = _validate_returns(returns)
    result = _replay(values, policy)
    scenarios = evaluate_sequence_risk(values, policy)
    return IncomeValidationResult(
        **{
            **result.__dict__,
            "sequence_scenarios": scenarios,
        }
    )
