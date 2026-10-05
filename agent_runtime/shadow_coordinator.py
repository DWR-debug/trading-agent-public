"""Paper-only coordinator between frozen agent intent and a shadow ledger.

The coordinator validates safety/risk state and emits a provenance-bearing shadow
event. It never calls a broker, creates an order, changes candidate selection,
tunes parameters, or evaluates performance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any, Mapping

from agent_runtime.decision_adapter import intent_fingerprint
from agent_runtime.paper_intent import PaperIntent, PaperIntentError
from agent_runtime.shadow_ledger import PaperShadowIntentLedger
from risk.portfolio_controller import PortfolioRiskController


class ShadowCoordinatorError(ValueError):
    """Raised when a shadow intent cannot be safely admitted to the ledger."""


@dataclass(frozen=True)
class ShadowLedgerEvent:
    event_type: str
    candidate_id: str
    symbol: str
    decision_time_utc: str
    target_exposure: float
    intent_fingerprint: str
    portfolio_state: Mapping[str, Any]
    scientific_evidence: bool = False
    performance_authorization: bool = False
    promotion: bool = False
    live_execution: bool = False

    def fingerprint(self) -> str:
        payload = {
            "event_type": self.event_type,
            "candidate_id": self.candidate_id,
            "symbol": self.symbol,
            "decision_time_utc": self.decision_time_utc,
            "target_exposure": self.target_exposure,
            "intent_fingerprint": self.intent_fingerprint,
            "portfolio_state": dict(self.portfolio_state),
            "scientific_evidence": self.scientific_evidence,
            "performance_authorization": self.performance_authorization,
            "promotion": self.promotion,
            "live_execution": self.live_execution,
        }
        return hashlib.sha256(
            json.dumps(
                payload, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
        ).hexdigest()


class PaperShadowCoordinator:
    """Admit valid intents to a canonical append-only paper-shadow ledger."""

    def __init__(
        self,
        risk_controller: PortfolioRiskController,
        ledger: PaperShadowIntentLedger | None = None,
    ) -> None:
        self._risk = risk_controller
        self._ledger = ledger if ledger is not None else PaperShadowIntentLedger()
        self._events: list[ShadowLedgerEvent] = []

    @property
    def events(self) -> tuple[ShadowLedgerEvent, ...]:
        return tuple(self._events)

    @property
    def ledger(self) -> PaperShadowIntentLedger:
        return self._ledger

    def admit(self, intent: PaperIntent) -> ShadowLedgerEvent:
        try:
            intent.validate()
        except PaperIntentError:
            raise

        self._risk.check_trade_allowed()

        if not isfinite(intent.target_exposure):
            raise ShadowCoordinatorError("target exposure must be finite")
        if abs(intent.target_exposure) > 1.0:
            raise ShadowCoordinatorError("target exposure exceeds shadow bound")

        state = dict(self._risk.status())
        event = ShadowLedgerEvent(
            event_type="SHADOW_INTENT_ACCEPTED",
            candidate_id=intent.candidate_id,
            symbol=intent.symbol,
            decision_time_utc=intent.decision_time_utc,
            target_exposure=intent.target_exposure,
            intent_fingerprint=intent_fingerprint(intent),
            portfolio_state=state,
        )
        event.fingerprint()
        self._ledger.append(intent)
        self._events.append(event)
        return event

    def persist_ledger(self, path: str | Path) -> dict[str, object]:
        """Persist the canonical PaperIntent ledger without outcomes."""
        return self._ledger.persist(path)

    def event_chain_fingerprint(self) -> str:
        chain = "|".join(event.fingerprint() for event in self._events).encode("utf-8")
        return hashlib.sha256(chain).hexdigest()

    def export(self) -> list[dict[str, Any]]:
        return [
            {
                "event_type": item.event_type,
                "candidate_id": item.candidate_id,
                "symbol": item.symbol,
                "decision_time_utc": item.decision_time_utc,
                "target_exposure": item.target_exposure,
                "intent_fingerprint": item.intent_fingerprint,
                "portfolio_state": dict(item.portfolio_state),
                "scientific_evidence": item.scientific_evidence,
                "performance_authorization": item.performance_authorization,
                "promotion": item.promotion,
                "live_execution": item.live_execution,
                "event_fingerprint": item.fingerprint(),
            }
            for item in self._events
        ]
