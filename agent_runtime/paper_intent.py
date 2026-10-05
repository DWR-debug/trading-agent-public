"""Fail-closed paper intent contract for the Trading Agent runtime.

The runtime accepts a decision already produced by an explicitly selected,
externally frozen component. It never chooses candidates, tunes parameters,
evaluates returns, authorizes research, or submits broker/exchange orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Mapping


class PaperIntentError(ValueError):
    """Raised when an agent runtime packet violates the safety contract."""


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise PaperIntentError("timestamp must be a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PaperIntentError(f"invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise PaperIntentError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class FrozenDecisionPacket:
    """A precomputed target exposure with immutable provenance."""

    candidate_id: str
    symbol: str
    decision_time_utc: str
    market_observation_time_utc: str
    input_fingerprint: str
    decision_fingerprint: str
    target_exposure: float
    paper_only: bool = True
    live_trading_enabled: bool = False
    orders_enabled: bool = False
    automatic_promotion: bool = False
    metadata: Mapping[str, str] | None = None

    def validate(self) -> "FrozenDecisionPacket":
        if not self.candidate_id:
            raise PaperIntentError("candidate_id must not be empty")
        if not self.symbol:
            raise PaperIntentError("symbol must not be empty")
        if not self.input_fingerprint:
            raise PaperIntentError("input_fingerprint must not be empty")
        if not self.decision_fingerprint:
            raise PaperIntentError("decision_fingerprint must not be empty")

        decision_time = _parse_utc(self.decision_time_utc)
        observation_time = _parse_utc(self.market_observation_time_utc)
        if decision_time < observation_time:
            raise PaperIntentError(
                "decision_time_utc cannot precede market_observation_time_utc"
            )

        if not isfinite(self.target_exposure):
            raise PaperIntentError("target_exposure must be finite")
        if self.target_exposure < -1.0 or self.target_exposure > 1.0:
            raise PaperIntentError("target_exposure must be within [-1.0, 1.0]")

        if not self.paper_only:
            raise PaperIntentError("paper_only must remain true")
        if self.live_trading_enabled:
            raise PaperIntentError("live_trading_enabled must remain false")
        if self.orders_enabled:
            raise PaperIntentError("orders_enabled must remain false")
        if self.automatic_promotion:
            raise PaperIntentError("automatic_promotion must remain false")

        return self


@dataclass(frozen=True)
class PaperIntent:
    """A paper-only target-exposure intent; no broker route exists."""

    candidate_id: str
    symbol: str
    decision_time_utc: str
    input_fingerprint: str
    decision_fingerprint: str
    target_exposure: float
    execution_route: str = "paper_shadow"
    broker_order_supported: bool = False

    def validate(self) -> "PaperIntent":
        if self.execution_route != "paper_shadow":
            raise PaperIntentError("execution_route must remain paper_shadow")
        if self.broker_order_supported:
            raise PaperIntentError("broker_order_supported must remain false")
        if not (self.candidate_id and self.symbol):
            raise PaperIntentError("candidate_id and symbol are required")
        if not self.input_fingerprint or not self.decision_fingerprint:
            raise PaperIntentError("decision provenance fingerprints are required")
        if not isfinite(self.target_exposure):
            raise PaperIntentError("target_exposure must be finite")
        if not -1.0 <= self.target_exposure <= 1.0:
            raise PaperIntentError("target_exposure must be within [-1.0, 1.0]")
        _parse_utc(self.decision_time_utc)
        return self


class PaperOnlyAgentRuntime:
    """Wrap a frozen target exposure in a paper-only runtime intent."""

    def build_intent(self, packet: FrozenDecisionPacket) -> PaperIntent:
        packet.validate()
        intent = PaperIntent(
            candidate_id=packet.candidate_id,
            symbol=packet.symbol,
            decision_time_utc=packet.decision_time_utc,
            input_fingerprint=packet.input_fingerprint,
            decision_fingerprint=packet.decision_fingerprint,
            target_exposure=packet.target_exposure,
        )
        return intent.validate()
