from datetime import datetime, timezone

import pytest

from data.gdelt_events import GDELTEvent
from research.event_intelligence import (
    aggregate_daily_events,
    event_importance,
    is_high_confidence_international_event,
    is_international_event,
)


def event(day, quad, goldstein, mentions, left="USA", right="RUS", articles=3):
    return GDELTEvent(
        day * 10 + quad,
        datetime(2026, 9, day, 12, tzinfo=timezone.utc),
        "190",
        "190",
        "19",
        quad,
        goldstein,
        mentions,
        2,
        articles,
        -1.0,
        left,
        right,
        "",
        "",
    )


def test_international_filter_and_confidence():
    assert is_international_event(event(1, 4, -5.0, 9))
    assert is_high_confidence_international_event(event(1, 4, -5.0, 9))
    assert not is_international_event(event(1, 4, -5.0, 9, "USA", ""))
    assert not is_high_confidence_international_event(event(1, 4, -5.0, 9, articles=2))


def test_daily_aggregation_is_international_and_conflict_aware():
    features = aggregate_daily_events(
        [
            event(1, 3, -3.0, 4),
            event(1, 4, -5.0, 9),
            event(1, 2, 2.0, 2),
            event(1, 4, -2.0, 2, "USA", "USA"),
        ],
        international_only=True,
        high_confidence_only=True,
    )
    assert len(features) == 1
    assert features[0].event_count == 2
    assert features[0].international_event_count == 2
    assert features[0].high_confidence_international_count == 2
    assert features[0].international_material_conflict_count == 1
    assert event_importance(event(1, 4, -5.0, 9)) > 0


def test_high_confidence_requires_international_only():
    with pytest.raises(ValueError):
        aggregate_daily_events([], high_confidence_only=True)
