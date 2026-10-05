"""Research-to-agent adapter for frozen, paper-only decisions.

This module is an integration boundary, not a research engine. It accepts one
already-frozen decision record and converts it into the existing paper-only
runtime contract. It rejects outcome-derived or search-derived fields and never
selects candidates, tunes parameters, evaluates performance, or submits orders.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agent_runtime.paper_intent import (
    FrozenDecisionPacket,
    PaperIntent,
    PaperIntentError,
    PaperOnlyAgentRuntime,
)

_REQUIRED_FIELDS = frozenset(
    {
        "candidate_id",
        "symbol",
        "decision_time_utc",
        "market_observation_time_utc",
        "input_fingerprint",
        "decision_fingerprint",
        "target_exposure",
    }
)

_OPTIONAL_FIELDS = frozenset(
    {
        "metadata",
        "paper_only",
        "live_trading_enabled",
        "orders_enabled",
        "automatic_promotion",
    }
)

_FORBIDDEN_FIELDS = frozenset(
    {
        "return",
        "returns",
        "pnl",
        "drawdown",
        "profit_factor",
        "holdout_return",
        "holdout_selection",
        "candidate_selection",
        "candidate_rank",
        "family_ranking",
        "parameter_search",
        "threshold_search",
        "horizon_search",
        "asset_search",
        "variant_search",
        "promotion_decision",
        "performance_authorization",
    }
)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def intent_fingerprint(intent: PaperIntent) -> str:
    payload = {
        "candidate_id": intent.candidate_id,
        "symbol": intent.symbol,
        "decision_time_utc": intent.decision_time_utc,
        "input_fingerprint": intent.input_fingerprint,
        "decision_fingerprint": intent.decision_fingerprint,
        "target_exposure": intent.target_exposure,
        "execution_route": intent.execution_route,
        "broker_order_supported": intent.broker_order_supported,
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def packet_from_record(record: dict[str, Any]) -> FrozenDecisionPacket:
    if not isinstance(record, dict):
        raise PaperIntentError("decision record must be a JSON object")

    forbidden = sorted(_FORBIDDEN_FIELDS.intersection(record))
    if forbidden:
        raise PaperIntentError(
            "decision record contains outcome/search fields: " + ",".join(forbidden)
        )

    allowed = _REQUIRED_FIELDS | _OPTIONAL_FIELDS
    unknown = sorted(set(record) - allowed)
    if unknown:
        raise PaperIntentError(
            "decision record contains unknown fields: " + ",".join(unknown)
        )

    missing = sorted(_REQUIRED_FIELDS - set(record))
    if missing:
        raise PaperIntentError(
            "decision record is missing required fields: " + ",".join(missing)
        )

    packet = FrozenDecisionPacket(
        candidate_id=record["candidate_id"],
        symbol=record["symbol"],
        decision_time_utc=record["decision_time_utc"],
        market_observation_time_utc=record["market_observation_time_utc"],
        input_fingerprint=record["input_fingerprint"],
        decision_fingerprint=record["decision_fingerprint"],
        target_exposure=record["target_exposure"],
        paper_only=record.get("paper_only", True),
        live_trading_enabled=record.get("live_trading_enabled", False),
        orders_enabled=record.get("orders_enabled", False),
        automatic_promotion=record.get("automatic_promotion", False),
        metadata=record.get("metadata"),
    )
    return packet.validate()


def adapt_record(record: dict[str, Any]) -> PaperIntent:
    packet = packet_from_record(record)
    return PaperOnlyAgentRuntime().build_intent(packet)


def load_record(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PaperIntentError(f"cannot read frozen decision record: {exc}") from exc
    return payload


def write_intent(path: str | Path, intent: PaperIntent) -> dict[str, Any]:
    intent.validate()
    envelope = {
        "schema_version": 1,
        "record_type": "paper_shadow_intent",
        "candidate_id": intent.candidate_id,
        "symbol": intent.symbol,
        "decision_time_utc": intent.decision_time_utc,
        "input_fingerprint": intent.input_fingerprint,
        "decision_fingerprint": intent.decision_fingerprint,
        "target_exposure": intent.target_exposure,
        "execution_route": intent.execution_route,
        "broker_order_supported": intent.broker_order_supported,
        "scientific_evidence": False,
        "performance_authorization": False,
        "promotion": False,
        "live_execution": False,
        "receipt_fingerprint": intent_fingerprint(intent),
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return envelope
