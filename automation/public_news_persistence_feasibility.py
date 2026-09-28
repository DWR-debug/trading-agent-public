"""Performance-free public-news persistence primitives for C31.

The implementation is source-neutral: upstream ingestion supplies immutable
GDELT-derived records with a conservative observed_at timestamp. No portfolio
formation, return evaluation, ranking, tuning or promotion occurs here.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class NewsToneRecord:
    record_id: str
    observed_at: datetime
    symbol: str
    tone: float


def _validate_record(record: NewsToneRecord) -> None:
    if not record.record_id:
        raise ValueError("record_id must be non-empty")
    if not record.symbol:
        raise ValueError("symbol must be non-empty")
    if record.observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    if not math.isfinite(float(record.tone)):
        raise ValueError("tone must be finite")


def visible_news(
    records: Sequence[NewsToneRecord],
    as_of: datetime,
) -> tuple[NewsToneRecord, ...]:
    """Return records observed by the conservative as-of boundary.

    A duplicate record_id is a hard failure. This prevents ingestion collisions
    from silently changing the historical state.
    """
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    seen: set[str] = set()
    visible: list[NewsToneRecord] = []
    for record in records:
        _validate_record(record)
        if record.record_id in seen:
            raise ValueError(f"duplicate record_id: {record.record_id}")
        seen.add(record.record_id)
        if record.observed_at <= as_of:
            visible.append(record)
    return tuple(sorted(visible, key=lambda x: (x.observed_at, x.record_id)))


def daily_mean_tone(
    records: Sequence[NewsToneRecord],
    as_of: datetime,
) -> dict[date, float]:
    """Aggregate visible article tone by UTC observation date."""
    grouped: dict[date, list[float]] = defaultdict(list)
    for record in visible_news(records, as_of):
        grouped[record.observed_at.astimezone().date()].append(float(record.tone))
    return {
        day: sum(values) / len(values)
        for day, values in sorted(grouped.items())
    }


def same_sign_persistence(tone_series: Sequence[float]) -> float:
    """Fraction of comparable adjacent non-zero tone pairs retaining sign.

    A result of 1 means complete persistence, 0 means no comparable pair
    persisted. Neutral observations are excluded from the denominator.
    """
    if len(tone_series) < 2:
        raise ValueError("at least two daily tone observations are required")
    comparable = 0
    same = 0
    for left, right in zip(tone_series, tone_series[1:]):
        left_sign = 1 if left > 0 else -1 if left < 0 else 0
        right_sign = 1 if right > 0 else -1 if right < 0 else 0
        if left_sign == 0 or right_sign == 0:
            continue
        comparable += 1
        if left_sign == right_sign:
            same += 1
    return same / comparable if comparable else 0.0


def c31_persistence_state(
    records: Sequence[NewsToneRecord],
    as_of: datetime,
    *,
    short_observation_days: int = 5,
    long_observation_days: int = 21,
) -> float:
    """Fixed C31 state: short-run minus long-run sign persistence.

    Windows are measured in successive observed news days, not traded bars.
    The short/long lengths are part of this feasibility freeze and must not be
    searched after the design is registered.
    """
    if short_observation_days < 2:
        raise ValueError("short_observation_days must be at least 2")
    if long_observation_days <= short_observation_days:
        raise ValueError("long_observation_days must exceed short_observation_days")
    daily = daily_mean_tone(records, as_of)
    ordered = list(daily.values())
    if len(ordered) < long_observation_days:
        raise ValueError("insufficient observed news days for fixed persistence state")
    long_window = ordered[-long_observation_days:]
    short_window = long_window[-short_observation_days:]
    return same_sign_persistence(short_window) - same_sign_persistence(long_window)


def c31_persistence_state_from_daily_series(
    daily_tone: Mapping[date, float],
    *,
    short_observation_days: int = 5,
    long_observation_days: int = 21,
) -> float:
    """Pure state calculation for an already frozen daily tone panel."""
    ordered_days = sorted(daily_tone)
    values = [float(daily_tone[day]) for day in ordered_days]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("daily tone values must be finite")
    if len(values) < long_observation_days:
        raise ValueError("insufficient daily tone history")
    long_window = values[-long_observation_days:]
    short_window = long_window[-short_observation_days:]
    return same_sign_persistence(short_window) - same_sign_persistence(long_window)


def source_contract() -> dict[str, object]:
    """Freeze the external-source assumptions without binding to a vendor API."""
    return {
        "source_family": "GDELT_GKG",
        "record_identity": "stable_record_id",
        "time_boundary": "observed_at",
        "tone_field": "document_level_tone",
        "historical_access": "public_raw_archive",
        "paid_api_required": False,
        "performance_ready": False,
    }
