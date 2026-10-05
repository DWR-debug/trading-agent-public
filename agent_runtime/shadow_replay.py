"""Deterministic replay validator for paper-shadow intents."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from agent_runtime.paper_intent import PaperIntent, PaperIntentError
from agent_runtime.decision_adapter import intent_fingerprint


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PaperIntentError(f"invalid decision timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise PaperIntentError("decision timestamp must include a timezone")
    return parsed


@dataclass(frozen=True)
class ReplayReceipt:
    count: int
    first_decision_time_utc: str | None
    last_decision_time_utc: str | None
    intent_chain_fingerprint: str


def validate_replay(intents: Iterable[PaperIntent]) -> ReplayReceipt:
    rows = list(intents)
    seen: set[str] = set()
    previous_time: datetime | None = None
    fingerprints: list[str] = []

    for position, intent in enumerate(rows, start=1):
        intent.validate()
        fp = intent_fingerprint(intent)
        if fp in seen:
            raise PaperIntentError(f"duplicate intent at replay position {position}: {fp}")
        seen.add(fp)

        current_time = _timestamp(intent.decision_time_utc)
        if previous_time is not None and current_time < previous_time:
            raise PaperIntentError(
                f"decision time moved backwards at replay position {position}"
            )
        previous_time = current_time
        fingerprints.append(fp)

    chain = "|".join(fingerprints).encode("utf-8")
    import hashlib
    chain_fp = hashlib.sha256(chain).hexdigest()

    return ReplayReceipt(
        count=len(rows),
        first_decision_time_utc=rows[0].decision_time_utc if rows else None,
        last_decision_time_utc=rows[-1].decision_time_utc if rows else None,
        intent_chain_fingerprint=chain_fp,
    )
