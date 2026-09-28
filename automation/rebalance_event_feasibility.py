"""Performance-free PIT primitives for scheduled index-rebalance demand states."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
import math


@dataclass(frozen=True)
class RebalanceEvent:
    event_id: str
    symbol: str
    action: int
    published_at: datetime
    effective_at: datetime


def _validate(event: RebalanceEvent) -> None:
    if not event.event_id:
        raise ValueError("event_id must be non-empty")
    if not event.symbol:
        raise ValueError("symbol must be non-empty")
    if event.action not in (-1, 1):
        raise ValueError("action must be -1 (delete) or +1 (add)")
    if event.published_at.tzinfo is None or event.effective_at.tzinfo is None:
        raise ValueError("event timestamps must be timezone-aware")
    if event.effective_at <= event.published_at:
        raise ValueError("effective_at must be after published_at")


def visible_future_rebalance_events(
    events: Sequence[RebalanceEvent],
    as_of: datetime,
) -> tuple[RebalanceEvent, ...]:
    """Return future effective events whose publication was already visible at as_of."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    seen: set[str] = set()
    visible: list[RebalanceEvent] = []
    for event in events:
        _validate(event)
        if event.event_id in seen:
            raise ValueError(f"duplicate event_id: {event.event_id}")
        seen.add(event.event_id)
        if event.published_at <= as_of < event.effective_at:
            visible.append(event)
    return tuple(
        sorted(
            visible,
            key=lambda x: (x.effective_at, x.symbol, x.published_at, x.event_id),
        )
    )


def next_known_rebalance_state(
    events: Sequence[RebalanceEvent],
    as_of: datetime,
) -> dict[str, int]:
    """Return the action of the next known effective event for each symbol.

    If several public revisions share the same effective date, the latest
    already-published revision supersedes earlier revisions. Two revisions at
    identical publication timestamps fail closed when they disagree.
    """
    visible = visible_future_rebalance_events(events, as_of)
    by_symbol: dict[str, list[RebalanceEvent]] = {}
    for event in visible:
        by_symbol.setdefault(event.symbol, []).append(event)

    state: dict[str, int] = {}
    for symbol, candidates in by_symbol.items():
        first_effective = min(event.effective_at for event in candidates)
        same_date = [
            event for event in candidates if event.effective_at == first_effective
        ]
        latest_published = max(event.published_at for event in same_date)
        revisions = [
            event for event in same_date if event.published_at == latest_published
        ]
        actions = {event.action for event in revisions}
        if len(actions) > 1:
            raise ValueError(
                f"conflicting same-time rebalance revisions for {symbol}"
            )
        state[symbol] = revisions[0].action

    return dict(sorted(state.items()))


def rebalance_event_schema() -> dict[str, object]:
    """Freeze the event contract without authorizing any performance use."""
    return {
        "source_family": "PUBLIC_INDEX_REBALANCE_SCHEDULE",
        "required_fields": (
            "event_id",
            "symbol",
            "action",
            "published_at",
            "effective_at",
        ),
        "action_encoding": {"ADD": 1, "DELETE": -1},
        "time_boundary": "published_at",
        "state_rule": "next known effective event; latest public revision at that effective time wins",
        "event_window_search": False,
        "performance_ready": False,
    }
