"""Generic cross-source temporal join contract for research inputs.

The join aligns independently sourced events on a common decision cutoff and
eligible market session. It is structural infrastructure only and has no
access to performance outcomes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any


FORBIDDEN = {
    "return", "returns", "pnl", "profit_factor", "drawdown", "holdout",
    "performance", "rank", "selection", "winner",
}


def _canon(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _ts(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"CLOCK_INVALID_{field.upper()}")
    try:
        out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"CLOCK_INVALID_{field.upper()}") from exc
    if out.tzinfo is None:
        raise ValueError(f"CLOCK_TIMEZONE_REQUIRED_{field.upper()}")
    return out


def build_join(events: list[dict[str, Any]], *, decision_cutoff: str, eligible_session: str) -> dict[str, Any]:
    cutoff = _ts(decision_cutoff, "decision_cutoff")
    if not events:
        raise ValueError("CLOCK_NO_EVENTS")
    seen: set[tuple[str, str]] = set()
    normalized: list[dict[str, Any]] = []
    for raw in events:
        if not isinstance(raw, dict):
            raise ValueError("CLOCK_EVENT_NOT_OBJECT")
        forbidden = FORBIDDEN.intersection(raw)
        if forbidden:
            raise ValueError("CLOCK_FORBIDDEN_OUTCOME_FIELD:" + ",".join(sorted(forbidden)))
        required = ("source_id", "entity_id", "event_id", "observed_at", "available_at", "eligible_session", "value_fingerprint")
        missing = [x for x in required if raw.get(x) in (None, "")]
        if missing:
            raise ValueError("CLOCK_MISSING_FIELDS:" + ",".join(missing))
        obs = _ts(raw["observed_at"], "observed_at")
        avail = _ts(raw["available_at"], "available_at")
        if avail < obs:
            raise ValueError("CLOCK_AVAILABLE_BEFORE_OBSERVED")
        if avail > cutoff:
            raise ValueError("CLOCK_FUTURE_INFORMATION")
        if str(raw["eligible_session"]) != eligible_session:
            raise ValueError("CLOCK_SESSION_MISMATCH")
        key = (str(raw["source_id"]), str(raw["event_id"]))
        if key in seen:
            raise ValueError("CLOCK_DUPLICATE_EVENT")
        seen.add(key)
        normalized.append({
            "source_id": str(raw["source_id"]),
            "entity_id": str(raw["entity_id"]),
            "event_id": str(raw["event_id"]),
            "observed_at": obs.isoformat(),
            "available_at": avail.isoformat(),
            "eligible_session": eligible_session,
            "value_fingerprint": str(raw["value_fingerprint"]),
        })

    entities = {x["entity_id"] for x in normalized}
    if len(entities) != 1:
        raise ValueError("CLOCK_ENTITY_MISMATCH")

    normalized.sort(key=lambda x: (x["available_at"], x["source_id"], x["event_id"]))
    out = {
        "schema_version": 1,
        "decision_cutoff": cutoff.isoformat(),
        "eligible_session": eligible_session,
        "event_count": len(normalized),
        "events": normalized,
        "temporal_contract": "AVAILABLE_AT_LE_CUTOFF_AND_SESSION_EQUAL",
        "future_information_rejected": True,
        "performance_fields_consulted": False,
        "holdout_used": False,
        "performance_authorized": False,
    }
    out["join_fingerprint"] = fingerprint(out)
    return out


def synthetic_contract() -> dict[str, bool]:
    events = [
        {
            "source_id": "SEC", "entity_id": "E1", "event_id": "SEC-1",
            "observed_at": "2026-10-01T12:00:00+00:00",
            "available_at": "2026-10-01T12:05:00+00:00",
            "eligible_session": "2026-10-02", "value_fingerprint": "a",
        },
        {
            "source_id": "CFTC", "entity_id": "E1", "event_id": "CFTC-1",
            "observed_at": "2026-10-01T11:00:00+00:00",
            "available_at": "2026-10-01T14:00:00+00:00",
            "eligible_session": "2026-10-02", "value_fingerprint": "b",
        },
    ]
    out = build_join(events, decision_cutoff="2026-10-01T15:00:00+00:00", eligible_session="2026-10-02")
    return {
        "sorted_by_availability": out["events"][0]["source_id"] == "SEC",
        "session_locked": out["eligible_session"] == "2026-10-02",
        "fingerprint_present": len(out["join_fingerprint"]) == 64,
        "performance_quarantined": out["performance_fields_consulted"] is False,
    }
