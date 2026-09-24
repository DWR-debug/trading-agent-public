"""Simulation-only capital accounting for the trading-agent research framework.

This module does not place orders and is intentionally independent from execution.
It defines the accounting semantics needed for a future withdrawal/payout layer.
"""

from dataclasses import dataclass


class CapitalAccountingError(ValueError):
    """Raised when a capital-accounting operation violates the contract."""


@dataclass(frozen=True)
class CapitalSnapshot:
    contributed_capital_eur: float
    equity_eur: float
    realized_profit_eur: float
    withdrawn_profit_eur: float
    distributable_profit_eur: float


class CapitalAccount:
    """Fail-closed accounting model for a permanently working capital base.

    Initial research capital is normally 500 EUR. Contributions can increase
    the protected capital base. Withdrawals can only consume distributable
    realized profit; the contributed capital base cannot be withdrawn through
    this interface.
    """

    def __init__(self, initial_capital_eur: float = 500.0) -> None:
        if initial_capital_eur <= 0:
            raise CapitalAccountingError("Initial capital must be > 0.")

        self.contributed_capital_eur = float(initial_capital_eur)
        self.equity_eur = float(initial_capital_eur)
        self.realized_profit_eur = 0.0
        self.withdrawn_profit_eur = 0.0

    def record_contribution(self, amount_eur: float) -> None:
        if amount_eur <= 0:
            raise CapitalAccountingError("Contribution must be > 0.")

        self.contributed_capital_eur += float(amount_eur)
        self.equity_eur += float(amount_eur)

    def update_equity(self, equity_eur: float) -> None:
        if equity_eur < 0:
            raise CapitalAccountingError("Equity must not be negative.")

        self.equity_eur = float(equity_eur)

    def record_realized_profit(self, amount_eur: float) -> None:
        """Classify profit without mutating broker-reported equity.

        The execution/account layer remains the source of truth for equity.
        Keeping the two updates separate prevents double-counting.
        """
        if amount_eur <= 0:
            raise CapitalAccountingError("Realized profit must be > 0.")

        self.realized_profit_eur += float(amount_eur)

    @property
    def distributable_profit_eur(self) -> float:
        realized_available = (
            self.realized_profit_eur - self.withdrawn_profit_eur
        )
        capital_surplus = self.equity_eur - self.contributed_capital_eur
        return max(0.0, min(realized_available, capital_surplus))

    def record_profit_withdrawal(self, amount_eur: float) -> None:
        if amount_eur <= 0:
            raise CapitalAccountingError("Withdrawal must be > 0.")

        if amount_eur > self.distributable_profit_eur + 1e-12:
            raise CapitalAccountingError(
                "Withdrawal exceeds currently distributable realized profit."
            )

        self.withdrawn_profit_eur += float(amount_eur)
        self.equity_eur -= float(amount_eur)

    def snapshot(self) -> CapitalSnapshot:
        return CapitalSnapshot(
            contributed_capital_eur=self.contributed_capital_eur,
            equity_eur=self.equity_eur,
            realized_profit_eur=self.realized_profit_eur,
            withdrawn_profit_eur=self.withdrawn_profit_eur,
            distributable_profit_eur=self.distributable_profit_eur,
        )
