from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Observation:
    security: str
    observation_time: str
    publication_time: str
    value: float
    source_id: str
    revision: int = 0


def _visible(records: list[Observation], decision_time: str) -> list[Observation]:
    visible = [r for r in records if r.publication_time <= decision_time]
    seen: dict[tuple[str, str], Observation] = {}
    for row in visible:
        key = (row.security, row.observation_time)
        prior = seen.get(key)
        if prior is not None:
            if row.publication_time == prior.publication_time and row.revision == prior.revision and row.value != prior.value:
                raise ValueError('CONFLICTING_SAME_PUBLICATION_REVISION')
            if (row.publication_time, row.revision, row.source_id) < (prior.publication_time, prior.revision, prior.source_id):
                continue
        seen[key] = row
    return list(seen.values())


def last_visible_state(records: list[Observation], security: str, decision_time: str) -> Observation | None:
    visible = [r for r in _visible(records, decision_time) if r.security == security]
    if not visible:
        return None
    return max(visible, key=lambda r: (r.observation_time, r.publication_time, r.revision, r.source_id))


def ftd_state(records: list[Observation], security: str, decision_time: str) -> float:
    row = last_visible_state(records, security, decision_time)
    return 0.0 if row is None else row.value


def short_interest_state(records: list[Observation], security: str, decision_time: str) -> float:
    row = last_visible_state(records, security, decision_time)
    return 0.0 if row is None else row.value


def beneficial_ownership_state(records: list[Observation], security: str, decision_time: str) -> float:
    row = last_visible_state(records, security, decision_time)
    return 0.0 if row is None else row.value


def form144_state(records: list[Observation], security: str, decision_time: str) -> float:
    row = last_visible_state(records, security, decision_time)
    return 0.0 if row is None else row.value
