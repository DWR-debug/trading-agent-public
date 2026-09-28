from __future__ import annotations

from datetime import datetime, timezone

import pytest

from automation.rebalance_event_feasibility import (
    RebalanceEvent,
    next_known_rebalance_state,
    rebalance_event_schema,
    visible_future_rebalance_events,
)


def dt(day: int, hour: int = 12) -> datetime:
    return datetime(2026, 6, day, hour, tzinfo=timezone.utc)


def event(event_id: str, symbol: str, action: int, published: int, effective: int) -> RebalanceEvent:
    return RebalanceEvent(event_id, symbol, action, dt(published), dt(effective))


def test_only_publicly_known_future_events_are_visible() -> None:
    events = (
        event("E1", "AAA", 1, 2, 10),
        event("E2", "BBB", -1, 11, 20),
    )
    visible = visible_future_rebalance_events(events, dt(5))
    assert [item.event_id for item in visible] == ["E1"]


def test_future_publication_mutation_is_inert() -> None:
    events = (event("E1", "AAA", 1, 10, 20),)
    baseline = next_known_rebalance_state(events, dt(5))
    mutated = (event("E1", "AAA", -1, 10, 20),)
    assert next_known_rebalance_state(mutated, dt(5)) == baseline


def test_latest_public_revision_supersedes_preliminary_revision() -> None:
    events = (
        event("PRE", "AAA", 1, 2, 20),
        event("FINAL", "AAA", -1, 15, 20),
    )
    assert next_known_rebalance_state(events, dt(16)) == {"AAA": -1}


def test_same_publication_timestamp_conflict_fails_closed() -> None:
    events = (
        event("E1", "AAA", 1, 10, 20),
        event("E2", "AAA", -1, 10, 20),
    )
    with pytest.raises(ValueError, match="conflicting"):
        next_known_rebalance_state(events, dt(11))


def test_duplicate_event_id_fails_closed() -> None:
    e = event("E1", "AAA", 1, 10, 20)
    with pytest.raises(ValueError, match="duplicate event_id"):
        visible_future_rebalance_events((e, e), dt(11))


def test_effective_date_must_follow_publication() -> None:
    with pytest.raises(ValueError, match="effective_at"):
        event("E1", "AAA", 1, 20, 10)


def test_action_domain_is_fixed() -> None:
    with pytest.raises(ValueError, match="action"):
        event("E1", "AAA", 0, 10, 20)


def test_schema_forbids_event_window_search() -> None:
    schema = rebalance_event_schema()
    assert schema["event_window_search"] is False
    assert schema["performance_ready"] is False
