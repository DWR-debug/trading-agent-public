"""Deterministic research model for profit-dependent capital withdrawals.

The model is deliberately separated from broker/execution code. It replays a
portfolio return stream, treats each period's P&L as a research realization
proxy, and feeds positive/negative results into CapitalAccount. Later losses
therefore reduce the distributable balance before any further payout.

No live orders, broker integration, or production allocation decisions occur
here.
"""

from __future__ import annotations

from dataclasses import dataclass

from portfolio.capital_account import CapitalAccount


class IncomePolicyError(ValueError):
    """Raised when an income-policy contract is invalid."""


@dataclass(frozen=True)
class CapitalIncomePolicy:
    protected_capital_eur: float = 500.0
    reserve_eur: float = 0.0
    payout_fraction: float = 0.50
    capitalization_fraction: float = 0.25
    payout_interval_periods: int = 21
    maximum_payout_eur: float | None = None

    def __post_init__(self) -> None:
        if self.protected_capital_eur <= 0.0:
            raise IncomePolicyError("Protected capital must be > 0.")
        if self.reserve_eur < 0.0:
            raise IncomePolicyError("Reserve must not be negative.")
        if self.reserve_eur >= self.protected_capital_eur:
            raise IncomePolicyError(
                "Reserve must be smaller than protected capital."
            )
        if not 0.0 <= self.payout_fraction <= 1.0:
            raise IncomePolicyError(
                "Payout fraction must be between 0 and 1."
            )
        if not 0.0 <= self.capitalization_fraction <= 1.0:
            raise IncomePolicyError(
                "Capitalization fraction must be between 0 and 1."
            )
        if (
            self.payout_fraction + self.capitalization_fraction
            > 1.0 + 1e-12
        ):
            raise IncomePolicyError(
                "Payout and capitalization fractions must sum to <= 1."
            )
        if self.payout_interval_periods < 1:
            raise IncomePolicyError(
                "Payout interval must be at least 1 period."
            )
        if (
            self.maximum_payout_eur is not None
            and self.maximum_payout_eur <= 0.0
        ):
            raise IncomePolicyError(
                "Maximum payout must be > 0 when provided."
            )


@dataclass(frozen=True)
class CapitalIncomeObservation:
    period_index: int
    period_return: float
    equity_before_period_eur: float
    realized_pnl_eur: float
    distributable_before_actions_eur: float
    capitalized_eur: float
    payout_eur: float
    equity_after_actions_eur: float
    protected_capital_after_eur: float


@dataclass(frozen=True)
class CapitalIncomeResult:
    final_equity_eur: float
    total_payout_eur: float
    total_capitalized_eur: float
    payout_count: int
    capitalization_count: int
    ending_protected_capital_eur: float
    minimum_equity_eur: float
    maximum_drawdown_percent: float
    observations: tuple[CapitalIncomeObservation, ...]


@dataclass(frozen=True)
class SequenceSensitivity:
    chronological: CapitalIncomeResult
    reversed: CapitalIncomeResult

    @property
    def payout_difference_eur(self) -> float:
        return (
            self.chronological.total_payout_eur
            - self.reversed.total_payout_eur
        )

    @property
    def final_equity_difference_eur(self) -> float:
        return (
            self.chronological.final_equity_eur
            - self.reversed.final_equity_eur
        )


def _validate_returns(returns: tuple[float, ...]) -> None:
    for value in returns:
        if not isinstance(value, (int, float)):
            raise IncomePolicyError("Returns must be numeric.")
        if value <= -1.0:
            raise IncomePolicyError("Returns must be greater than -100%.")


def simulate_capital_withdrawals(
    returns: tuple[float, ...],
    policy: CapitalIncomePolicy | None = None,
) -> CapitalIncomeResult:
    """Replay a fixed return path with net-realized-profit accounting.

    Each period return is used as an explicit research realization proxy:
    period P&L is calculated from equity entering the period. This is not a
    broker-level claim about individual trade settlement.

    At a payout interval:
    1. only net realized, non-capital profit is considered;
    2. the reserve remains locked above protected capital;
    3. a fixed fraction may be capitalized into the protected base;
    4. a separate fixed fraction may be withdrawn;
    5. any remaining surplus stays in working equity.

    Negative periods reduce net realized P&L and therefore can eliminate a
    previously available withdrawal balance.
    """
    policy = policy or CapitalIncomePolicy()
    returns = tuple(returns)
    _validate_returns(returns)

    account = CapitalAccount(policy.protected_capital_eur)
    minimum_equity = account.equity_eur
    peak_equity = account.equity_eur
    maximum_drawdown = 0.0
    observations: list[CapitalIncomeObservation] = []

    for period_index, period_return in enumerate(returns, start=1):
        equity_before = account.equity_eur
        realized_pnl = equity_before * period_return
        account.update_equity(equity_before + realized_pnl)
        account.record_realized_pnl(realized_pnl)

        minimum_equity = min(minimum_equity, account.equity_eur)
        peak_equity = max(peak_equity, account.equity_eur)
        if peak_equity > 0.0:
            maximum_drawdown = max(
                maximum_drawdown,
                1.0 - account.equity_eur / peak_equity,
            )

        distributable = account.distributable_profit_eur
        capitalized = 0.0
        payout = 0.0

        if period_index % policy.payout_interval_periods == 0:
            available = max(
                0.0,
                distributable - policy.reserve_eur,
            )
            capitalized = available * policy.capitalization_fraction
            payout = available * policy.payout_fraction

            if (
                policy.maximum_payout_eur is not None
                and payout > policy.maximum_payout_eur
            ):
                payout = policy.maximum_payout_eur

            if capitalized > 0.0:
                account.capitalize_profit(capitalized)

            if payout > 0.0:
                account.record_profit_withdrawal(payout)

        observations.append(
            CapitalIncomeObservation(
                period_index=period_index,
                period_return=period_return,
                equity_before_period_eur=equity_before,
                realized_pnl_eur=realized_pnl,
                distributable_before_actions_eur=distributable,
                capitalized_eur=capitalized,
                payout_eur=payout,
                equity_after_actions_eur=account.equity_eur,
                protected_capital_after_eur=account.contributed_capital_eur,
            )
        )

    return CapitalIncomeResult(
        final_equity_eur=account.equity_eur,
        total_payout_eur=account.withdrawn_profit_eur,
        total_capitalized_eur=account.contributed_capital_eur
        - policy.protected_capital_eur,
        payout_count=sum(
            observation.payout_eur > 0.0
            for observation in observations
        ),
        capitalization_count=sum(
            observation.capitalized_eur > 0.0
            for observation in observations
        ),
        ending_protected_capital_eur=account.contributed_capital_eur,
        minimum_equity_eur=minimum_equity,
        maximum_drawdown_percent=maximum_drawdown * 100.0,
        observations=tuple(observations),
    )


def sequence_sensitivity(
    returns: tuple[float, ...],
    policy: CapitalIncomePolicy | None = None,
) -> SequenceSensitivity:
    """Compare chronological and reversed ordering as sequence-risk diagnostic."""
    returns = tuple(returns)
    return SequenceSensitivity(
        chronological=simulate_capital_withdrawals(returns, policy),
        reversed=simulate_capital_withdrawals(tuple(reversed(returns)), policy),
    )
