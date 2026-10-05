"""Candidate-neutral local paper execution adapter.

This module wires a frozen candidate to the existing local paper broker and
portfolio risk controller. It has no network, broker-account, research-evidence,
selection, ranking, tuning, promotion, or live-execution capability.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from config import settings
from execution.cost_contract import ResearchExecutionCostContract
from execution.execution_guard import execute_order
from execution.paper_broker import PaperBroker
from risk.portfolio_controller import PortfolioRiskController
from risk.risk_engine import calculate_position

from agent.runtime import AgentRuntimeError, FrozenCandidate


@dataclass(frozen=True)
class TradeIntent:
    symbol: str
    side: str
    entry_price: float
    stop_price: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side.upper(),
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
        }


class PaperExecutionAdapter:
    """Execute one validated trade intent entirely inside the local paper stack."""

    def __init__(self, candidate: FrozenCandidate) -> None:
        self._assert_global_safety()
        self.candidate = candidate

        contract = ResearchExecutionCostContract(
            fee_bps=candidate.fee_bps,
            slippage_bps=candidate.slippage_bps,
        )
        contract.validate()

        self.broker = PaperBroker(
            initial_capital=candidate.initial_capital_eur,
            cost_contract=contract,
        )
        self.portfolio_risk = PortfolioRiskController(
            initial_capital=candidate.initial_capital_eur
        )

    @staticmethod
    def _assert_global_safety() -> None:
        if settings.PAPER_ONLY is not True:
            raise AgentRuntimeError("PAPER_ONLY must be True.")
        if settings.LIVE_TRADING_ENABLED is not False:
            raise AgentRuntimeError("LIVE_TRADING_ENABLED must be False.")
        if settings.ORDERS_ENABLED is not False:
            raise AgentRuntimeError("ORDERS_ENABLED must be False.")
        if settings.AUTOMATIC_PROMOTION is not False:
            raise AgentRuntimeError("AUTOMATIC_PROMOTION must be False.")

    def open(self, intent: TradeIntent) -> dict[str, Any]:
        self._assert_global_safety()
        if not isinstance(intent, TradeIntent):
            raise AgentRuntimeError("intent must be a TradeIntent.")

        payload = intent.as_dict()
        side = payload["side"]
        if side not in {"BUY", "SELL"}:
            raise AgentRuntimeError("TradeIntent side must be BUY or SELL.")

        if not isinstance(payload["symbol"], str) or not payload["symbol"].strip():
            raise AgentRuntimeError("TradeIntent symbol is required.")

        try:
            risk = calculate_position(
                capital_eur=self.broker.cash,
                entry_price=float(payload["entry_price"]),
                stop_price=float(payload["stop_price"]),
                leverage=self.candidate.leverage,
            )
        except Exception as exc:
            raise AgentRuntimeError("Paper risk sizing failed closed.") from exc

        if risk["risk_eur"] > (
            self.broker.initial_capital * self.candidate.risk_per_trade
        ):
            raise AgentRuntimeError("Candidate risk exceeds its frozen contract.")

        self.portfolio_risk.check_trade_allowed()
        self.portfolio_risk.record_position_opened()
        try:
            guard = execute_order(
                {
                    **payload,
                    "quantity": risk["quantity"],
                    "leverage": self.candidate.leverage,
                }
            )
            if guard.get("status") != "PAPER_ONLY":
                raise AgentRuntimeError("Execution guard did not confirm paper-only mode.")

            result = self.broker.execute_order(
                symbol=payload["symbol"],
                side=side,
                quantity=risk["quantity"],
                price=float(payload["entry_price"]),
                leverage=self.candidate.leverage,
                stop_price=float(payload["stop_price"]),
            )
        except Exception as exc:
            self.portfolio_risk.record_position_closed()
            if isinstance(exc, AgentRuntimeError):
                raise
            raise AgentRuntimeError("Paper execution failed closed.") from exc

        return {
            "schema_version": 1,
            "candidate_id": self.candidate.candidate_id,
            "candidate_fingerprint": self.candidate.fingerprint,
            "intent": payload,
            "risk": risk,
            "security": guard,
            "execution": result,
            "portfolio_risk": self.portfolio_risk.status(),
        }

    def mark_to_market(self, market_prices: Mapping[str, float]) -> dict[str, Any]:
        self._assert_global_safety()
        if not isinstance(market_prices, Mapping):
            raise AgentRuntimeError("market_prices must be a mapping.")
        try:
            normalized = {
                str(symbol): float(price) for symbol, price in market_prices.items()
            }
            result = self.broker.account_status(normalized)
            self.portfolio_risk.update_equity(result["equity"])
        except Exception as exc:
            raise AgentRuntimeError("Paper mark-to-market failed closed.") from exc

        return {
            "account": result,
            "portfolio_risk": self.portfolio_risk.status(),
        }

    def close(self, symbol: str, price: float) -> dict[str, Any]:
        self._assert_global_safety()
        try:
            result = self.broker.close_position(symbol=symbol, price=float(price))
            self.portfolio_risk.record_position_closed()
            equity = self.broker.equity()
            self.portfolio_risk.update_equity(equity)
        except Exception as exc:
            raise AgentRuntimeError("Paper position close failed closed.") from exc

        return {
            "execution": result,
            "portfolio_risk": self.portfolio_risk.status(),
            "account": self.broker.account_status(),
        }
