"""Candidate-neutral Trading Agent decision runtime.

This layer is deliberately narrower than a strategy engine:
- it accepts one explicitly frozen candidate;
- it consumes only explicitly closed, ordered observations;
- it delegates signal logic through an injected fixed adapter;
- it returns a deterministic decision envelope;
- it does not select candidates, tune parameters, rank trials, authorize
  performance, promote strategies, or execute live orders.

Paper execution remains a separate concern and continues to use the existing
paper broker / risk components.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any, Callable, Iterable, Mapping

from config import settings
from execution.cost_contract import (
    ResearchExecutionCostContract,
    validate_research_cost_compatibility,
)


class AgentRuntimeError(ValueError):
    """Raised when an agent runtime contract is violated."""


_ALLOWED_ACTIONS = frozenset({"BUY", "SELL", "HOLD", "EXIT"})
SignalAdapter = Callable[[tuple[Mapping[str, Any], ...]], str]


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _require_finite_positive(value: Any, field: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise AgentRuntimeError(f"{field} must be numeric.") from exc
    if not math.isfinite(numeric) or numeric <= 0:
        raise AgentRuntimeError(f"{field} must be finite and > 0.")
    return numeric


@dataclass(frozen=True)
class FrozenCandidate:
    """Minimal candidate contract accepted by the runtime."""

    candidate_id: str
    freeze_ref: str
    initial_capital_eur: float
    risk_per_trade: float
    leverage: float
    fee_bps: float = 10.0
    slippage_bps: float = 5.0

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FrozenCandidate":
        if not isinstance(payload, Mapping):
            raise AgentRuntimeError("Candidate payload must be a mapping.")
        if payload.get("frozen") is not True:
            raise AgentRuntimeError("Agent runtime requires frozen=true.")
        candidate_id = payload.get("candidate_id")
        freeze_ref = payload.get("freeze_ref")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise AgentRuntimeError("candidate_id is required.")
        if not isinstance(freeze_ref, str) or not freeze_ref.strip():
            raise AgentRuntimeError("freeze_ref is required.")

        capital = _require_finite_positive(
            payload.get("initial_capital_eur"), "initial_capital_eur"
        )
        risk_per_trade = _require_finite_positive(
            payload.get("risk_per_trade"), "risk_per_trade"
        )
        leverage = _require_finite_positive(payload.get("leverage"), "leverage")
        fee_bps = _require_finite_positive(payload.get("fee_bps", 10.0), "fee_bps")
        slippage_bps = _require_finite_positive(
            payload.get("slippage_bps", 5.0), "slippage_bps"
        )

        if risk_per_trade > settings.RISK_PER_TRADE:
            raise AgentRuntimeError(
                "Candidate risk_per_trade exceeds the global configured safety limit."
            )
        if leverage > settings.MAX_LEVERAGE:
            raise AgentRuntimeError(
                "Candidate leverage exceeds the global configured safety limit."
            )

        contract = ResearchExecutionCostContract(
            fee_bps=fee_bps, slippage_bps=slippage_bps
        )
        contract.validate()

        return cls(
            candidate_id=candidate_id.strip(),
            freeze_ref=freeze_ref.strip(),
            initial_capital_eur=capital,
            risk_per_trade=risk_per_trade,
            leverage=leverage,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )

    def contract(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "freeze_ref": self.freeze_ref,
            "initial_capital_eur": self.initial_capital_eur,
            "risk_per_trade": self.risk_per_trade,
            "leverage": self.leverage,
            "fee_bps": self.fee_bps,
            "slippage_bps": self.slippage_bps,
        }

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.contract())


@dataclass(frozen=True)
class DecisionEnvelope:
    """Immutable, paper-only decision description."""

    candidate_id: str
    candidate_fingerprint: str
    action: str
    observation_fingerprint: str
    generated_at_utc: str
    paper_only: bool
    live_execution_enabled: bool
    orders_enabled: bool
    automatic_promotion: bool
    execution_allowed: bool
    research_authorization_consumed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "candidate_id": self.candidate_id,
            "candidate_fingerprint": self.candidate_fingerprint,
            "action": self.action,
            "observation_fingerprint": self.observation_fingerprint,
            "generated_at_utc": self.generated_at_utc,
            "paper_only": self.paper_only,
            "live_execution_enabled": self.live_execution_enabled,
            "orders_enabled": self.orders_enabled,
            "automatic_promotion": self.automatic_promotion,
            "execution_allowed": self.execution_allowed,
            "research_authorization_consumed": self.research_authorization_consumed,
        }

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.as_dict())


class TradingAgentRuntime:
    """Safe decision shell around an explicitly supplied frozen candidate."""

    def __init__(
        self,
        candidate: FrozenCandidate,
        signal_adapter: SignalAdapter,
    ) -> None:
        self._assert_safety()
        if not callable(signal_adapter):
            raise AgentRuntimeError("signal_adapter must be callable.")
        validate_research_cost_compatibility(
            fee_rate=candidate.fee_bps / 10_000.0,
            slippage_rate=candidate.slippage_bps / 10_000.0,
        )
        self.candidate = candidate
        self.signal_adapter = signal_adapter

    @staticmethod
    def _assert_safety() -> None:
        if settings.PAPER_ONLY is not True:
            raise AgentRuntimeError("PAPER_ONLY must be True.")
        if settings.LIVE_TRADING_ENABLED is not False:
            raise AgentRuntimeError("LIVE_TRADING_ENABLED must be False.")
        if settings.ORDERS_ENABLED is not False:
            raise AgentRuntimeError("ORDERS_ENABLED must be False.")
        if settings.AUTOMATIC_PROMOTION is not False:
            raise AgentRuntimeError("AUTOMATIC_PROMOTION must be False.")

    @staticmethod
    def _normalize_observations(
        observations: Iterable[Mapping[str, Any]],
    ) -> tuple[Mapping[str, Any], ...]:
        rows = tuple(observations)
        if not rows:
            raise AgentRuntimeError("At least one market observation is required.")

        previous = None
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise AgentRuntimeError(
                    f"Observation {index} must be a mapping."
                )
            if row.get("closed") is not True:
                raise AgentRuntimeError(
                    f"Observation {index} is not explicitly marked closed."
                )
            timestamp = row.get("timestamp")
            if not isinstance(timestamp, str) or not timestamp.strip():
                raise AgentRuntimeError(
                    f"Observation {index} requires an explicit timestamp."
                )
            try:
                current_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError as exc:
                raise AgentRuntimeError(
                    f"Observation {index} has an invalid timestamp."
                ) from exc
            if current_dt.tzinfo is None:
                raise AgentRuntimeError(
                    f"Observation {index} timestamp must be timezone-aware."
                )
            current_dt = current_dt.astimezone(timezone.utc)
            if previous is not None and current_dt <= previous:
                raise AgentRuntimeError(
                    "Observations must be strictly increasing by timestamp."
                )
            previous = current_dt

        return rows

    def decide(
        self,
        observations: Iterable[Mapping[str, Any]],
    ) -> DecisionEnvelope:
        self._assert_safety()
        normalized = self._normalize_observations(observations)

        try:
            raw_action = self.signal_adapter(normalized)
        except Exception as exc:
            raise AgentRuntimeError("Signal adapter failed closed.") from exc

        if not isinstance(raw_action, str):
            raise AgentRuntimeError("Signal adapter must return a string action.")
        action = raw_action.strip().upper()
        if action not in _ALLOWED_ACTIONS:
            raise AgentRuntimeError(
                f"Unsupported signal action {action!r}; expected one of "
                f"{sorted(_ALLOWED_ACTIONS)}."
            )

        observation_payload = [dict(row) for row in normalized]
        observation_fingerprint = _fingerprint(observation_payload)

        return DecisionEnvelope(
            candidate_id=self.candidate.candidate_id,
            candidate_fingerprint=self.candidate.fingerprint,
            action=action,
            observation_fingerprint=observation_fingerprint,
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
            paper_only=True,
            live_execution_enabled=False,
            orders_enabled=False,
            automatic_promotion=False,
            execution_allowed=False,
            research_authorization_consumed=False,
        )
