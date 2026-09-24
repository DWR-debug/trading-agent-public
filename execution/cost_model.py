"""Explicit transaction-cost and short-borrow model.

This module is opt-in infrastructure. Existing broker/backtest defaults are not
changed by importing it.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


class ExecutionCostModelError(ValueError):
    """Raised for invalid execution-cost model parameters."""


@dataclass(frozen=True)
class ExecutionCostModel:
    """Deterministic one-way execution cost model."""

    fee_bps: float = 10.0
    slippage_bps: float = 5.0
    spread_bps: float = 0.0
    short_borrow_annual_bps: float = 0.0
    trading_days_per_year: int = 252

    def __post_init__(self) -> None:
        for name, value in (
            ("fee_bps", self.fee_bps),
            ("slippage_bps", self.slippage_bps),
            ("spread_bps", self.spread_bps),
            ("short_borrow_annual_bps", self.short_borrow_annual_bps),
        ):
            if not isfinite(value) or value < 0.0:
                raise ExecutionCostModelError(
                    f"{name} must be finite and non-negative."
                )
        if self.trading_days_per_year < 1:
            raise ExecutionCostModelError("trading_days_per_year must be >= 1.")

    @property
    def one_way_cost_rate(self) -> float:
        return (
            self.fee_bps + self.slippage_bps + 0.5 * self.spread_bps
        ) / 10_000.0

    @property
    def one_way_impact_rate(self) -> float:
        return (
            self.slippage_bps + 0.5 * self.spread_bps
        ) / 10_000.0

    def execution_price(self, market_price: float, side: str) -> float:
        if not isfinite(market_price) or market_price <= 0.0:
            raise ExecutionCostModelError("market_price must be finite and > 0.")
        normalized_side = side.upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise ExecutionCostModelError("side must be BUY or SELL.")
        impact = self.one_way_impact_rate
        return (
            market_price * (1.0 + impact)
            if normalized_side == "BUY"
            else market_price * (1.0 - impact)
        )

    def one_way_transaction_cost(self, notional: float) -> float:
        if notional < 0.0 or not isfinite(notional):
            raise ExecutionCostModelError("notional must be finite and non-negative.")
        return notional * self.one_way_cost_rate

    def round_trip_transaction_cost(self, notional: float) -> float:
        return 2.0 * self.one_way_transaction_cost(notional)

    def short_borrow_cost(self, notional: float, days: int = 1) -> float:
        if notional < 0.0 or not isfinite(notional):
            raise ExecutionCostModelError("notional must be finite and non-negative.")
        if days < 0:
            raise ExecutionCostModelError("days must be non-negative.")
        annual_rate = self.short_borrow_annual_bps / 10_000.0
        return notional * annual_rate * days / self.trading_days_per_year
