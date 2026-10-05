"""Deterministic replay validation for accepted paper-shadow events."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

from agent_runtime.shadow_coordinator import ShadowCoordinatorError, ShadowLedgerEvent


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ShadowCoordinatorError(f"invalid shadow event timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ShadowCoordinatorError("shadow event timestamp must include a timezone")
    return parsed


@dataclass(frozen=True)
class ShadowEventReplayReceipt:
    count: int
    first_decision_time_utc: str | None
    last_decision_time_utc: str | None
    event_chain_fingerprint: str


_REQUIRED = frozenset(
    {
        "event_type",
        "candidate_id",
        "symbol",
        "decision_time_utc",
        "target_exposure",
        "intent_fingerprint",
        "portfolio_state",
        "scientific_evidence",
        "performance_authorization",
        "promotion",
        "live_execution",
        "event_fingerprint",
    }
)


def _validate_fingerprint(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ShadowCoordinatorError(
            "shadow event fingerprint must be a 64-character SHA-256 hex string"
        )
    try:
        int(value, 16)
    except ValueError as exc:
        raise ShadowCoordinatorError("shadow event fingerprint must be hexadecimal") from exc
    return value


def validate_shadow_event_replay(
    records: Iterable[Mapping[str, Any]],
) -> ShadowEventReplayReceipt:
    rows = list(records)
    seen: set[str] = set()
    previous: datetime | None = None
    fingerprints: list[str] = []

    for position, record in enumerate(rows, start=1):
        if set(record) != _REQUIRED:
            raise ShadowCoordinatorError(
                f"shadow event at replay position {position} must contain exactly the frozen event fields"
            )
        if not isinstance(record["portfolio_state"], Mapping):
            raise ShadowCoordinatorError("shadow event portfolio_state must be a mapping")
        for flag in ("scientific_evidence", "performance_authorization", "promotion", "live_execution"):
            if type(record[flag]) is not bool:
                raise ShadowCoordinatorError(f"shadow event flag {flag} must be boolean")
        event = ShadowLedgerEvent(
            event_type=record["event_type"],
            candidate_id=record["candidate_id"],
            symbol=record["symbol"],
            decision_time_utc=record["decision_time_utc"],
            target_exposure=record["target_exposure"],
            intent_fingerprint=record["intent_fingerprint"],
            portfolio_state=record["portfolio_state"],
            scientific_evidence=record["scientific_evidence"],
            performance_authorization=record["performance_authorization"],
            promotion=record["promotion"],
            live_execution=record["live_execution"],
        )
        stored = _validate_fingerprint(record["event_fingerprint"])
        computed = event.fingerprint()
        if stored != computed:
            raise ShadowCoordinatorError(
                f"shadow event fingerprint mismatch at replay position {position}"
            )
        if stored in seen:
            raise ShadowCoordinatorError(
                f"duplicate shadow event at replay position {position}: {stored}"
            )
        seen.add(stored)

        current = _timestamp(event.decision_time_utc)
        if previous is not None and current < previous:
            raise ShadowCoordinatorError(
                f"shadow event decision time moved backwards at replay position {position}"
            )
        previous = current

        if any((
            event.scientific_evidence,
            event.performance_authorization,
            event.promotion,
            event.live_execution,
        )):
            raise ShadowCoordinatorError(
                "shadow event contains an authorizing or live-execution flag"
            )

        fingerprints.append(stored)

    chain = hashlib.sha256("|".join(fingerprints).encode("utf-8")).hexdigest()
    return ShadowEventReplayReceipt(
        count=len(rows),
        first_decision_time_utc=rows[0]["decision_time_utc"] if rows else None,
        last_decision_time_utc=rows[-1]["decision_time_utc"] if rows else None,
        event_chain_fingerprint=chain,
    )
