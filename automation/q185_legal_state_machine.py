"""Deterministic Q185 legal-state machine.

The state builder is intentionally conservative and pre-formal. It accepts
already-classified docket event classes and uses only information public by the
requested cutoff. Later events cannot rewrite an earlier state prefix.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping

STATE_ORDER = (
    "NO_KNOWN_CASE",
    "CASE_FILED",
    "ACTIVE_LITIGATION",
    "MATERIAL_PROCEDURAL_TRANSITION",
    "RESOLVED",
)

EVENT_TO_STATE = {
    "CASE_FILED": "CASE_FILED",
    "ACTIVE_DOCKET_ENTRY": "ACTIVE_LITIGATION",
    "MATERIAL_PROCEDURAL_ORDER": "MATERIAL_PROCEDURAL_TRANSITION",
    "TERMINATION": "RESOLVED",
}

@dataclass(frozen=True)
class PublicState:
    case_id: str
    public_date: date
    state: str
    event_id: str

def states_as_of(
    entries: Iterable[Mapping[str, object]],
    cutoff: date,
) -> list[PublicState]:
    eligible = []
    for row in entries:
        public_date = row["public_date"]
        if not isinstance(public_date, date):
            raise TypeError("public_date must be a datetime.date")
        if public_date > cutoff:
            continue
        event_class = str(row["event_class"])
        if event_class not in EVENT_TO_STATE:
            continue
        eligible.append((str(row["case_id"]), public_date, str(row["event_id"]), EVENT_TO_STATE[event_class]))

    eligible.sort(key=lambda x: (x[0], x[1], x[2]))
    current_case: dict[str, str] = {}
    output: list[PublicState] = []

    for case_id, public_date, event_id, event_state in eligible:
        previous = current_case.get(case_id, "NO_KNOWN_CASE")
        if event_state == "CASE_FILED":
            new_state = "CASE_FILED" if previous == "NO_KNOWN_CASE" else previous
        elif event_state == "ACTIVE_LITIGATION":
            new_state = "ACTIVE_LITIGATION" if previous not in {"RESOLVED"} else previous
        elif event_state == "MATERIAL_PROCEDURAL_TRANSITION":
            new_state = "MATERIAL_PROCEDURAL_TRANSITION" if previous not in {"RESOLVED"} else previous
        else:
            new_state = "RESOLVED"
        current_case[case_id] = new_state
        output.append(PublicState(case_id, public_date, new_state, event_id))

    return output

def earliest_public_state(
    entries: Iterable[Mapping[str, object]],
    cutoff: date,
) -> dict[str, PublicState]:
    states = states_as_of(entries, cutoff)
    first: dict[str, PublicState] = {}
    for item in states:
        first.setdefault(item.case_id, item)
    return first
