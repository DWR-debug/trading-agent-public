"""Neutral point-in-time political/geopolitical event features."""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime

from data.gdelt_events import GDELTEvent


@dataclass(frozen=True)
class EventFeatures:
    event_date: date
    event_count: int
    international_event_count: int
    high_confidence_international_count: int
    material_conflict_count: int
    international_material_conflict_count: int
    verbal_conflict_count: int
    material_cooperation_count: int
    negative_goldstein_sum: float
    mention_weighted_conflict: float
    source_count: int
    mean_tone: float


def is_international_event(event: GDELTEvent) -> bool:
    left = event.actor1_country_code.strip()
    right = event.actor2_country_code.strip()
    return bool(left and right and left != right)


def is_high_confidence_international_event(event: GDELTEvent) -> bool:
    return is_international_event(event) and event.num_articles >= 3


def event_importance(event: GDELTEvent) -> float:
    return max(1.0, abs(event.goldstein_scale)) * math.log1p(
        max(0, event.num_mentions)
    )


def aggregate_daily_events(
    events: list[GDELTEvent],
    *,
    international_only: bool = False,
    high_confidence_only: bool = False,
) -> tuple[EventFeatures, ...]:
    if high_confidence_only and not international_only:
        raise ValueError("high_confidence_only requires international_only=True.")
    grouped: dict[date, list[GDELTEvent]] = defaultdict(list)
    for event in events:
        if international_only and not is_international_event(event):
            continue
        if high_confidence_only and not is_high_confidence_international_event(event):
            continue
        grouped[event.date_added.date()].append(event)

    result = []
    for day in sorted(grouped):
        values = grouped[day]
        international = [event for event in values if is_international_event(event)]
        high_confidence = [
            event for event in values if is_high_confidence_international_event(event)
        ]
        result.append(
            EventFeatures(
                event_date=day,
                event_count=len(values),
                international_event_count=len(international),
                high_confidence_international_count=len(high_confidence),
                material_conflict_count=sum(e.quad_class == 4 for e in values),
                international_material_conflict_count=sum(
                    e.quad_class == 4 and is_international_event(e)
                    for e in values
                ),
                verbal_conflict_count=sum(e.quad_class == 3 for e in values),
                material_cooperation_count=sum(e.quad_class == 2 for e in values),
                negative_goldstein_sum=sum(
                    -e.goldstein_scale for e in values if e.goldstein_scale < 0
                ),
                mention_weighted_conflict=sum(
                    event_importance(e) for e in values if e.quad_class in {3, 4}
                ),
                source_count=sum(max(0, e.num_sources) for e in values),
                mean_tone=sum(e.avg_tone for e in values) / len(values),
            )
        )
    return tuple(result)


def conflict_flag(features: EventFeatures) -> bool:
    return (
        features.international_material_conflict_count > 0
        or features.verbal_conflict_count > 0
    )


def point_in_time_timestamp(event: GDELTEvent) -> datetime:
    return event.date_added
