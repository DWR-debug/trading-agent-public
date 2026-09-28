from __future__ import annotations

from datetime import datetime, timezone

import pytest

from automation.public_news_persistence_feasibility import (
    NewsToneRecord,
    c31_persistence_state,
    c31_persistence_state_from_daily_series,
    daily_mean_tone,
    same_sign_persistence,
    source_contract,
    visible_news,
)


def dt(day: int, hour: int = 12) -> datetime:
    return datetime(2026, 1, day, hour, tzinfo=timezone.utc)


def record(symbol: str, day: int, idx: int, tone: float) -> NewsToneRecord:
    return NewsToneRecord(
        record_id=f"{symbol}-{day}-{idx}",
        observed_at=dt(day),
        symbol=symbol,
        tone=tone,
    )


def test_future_records_are_excluded() -> None:
    base = [
        record("AAA", day, day, 1.0 if day % 2 else -1.0)
        for day in range(1, 22)
    ]
    before = c31_persistence_state(base, dt(21))
    mutated = base + [record("AAA", 22, 22, 999.0)]
    after = c31_persistence_state(mutated, dt(21))
    assert after == before


def test_as_of_boundary_excludes_t_plus_one() -> None:
    base = [
        record("AAA", day, day, 1.0 if day < 11 else -1.0)
        for day in range(1, 22)
    ]
    baseline = daily_mean_tone(base, dt(21, 23))
    extended = base + [record("AAA", 22, 22, 500.0)]
    assert daily_mean_tone(extended, dt(21, 23)) == baseline


def test_duplicate_record_id_fails_closed() -> None:
    duplicate = record("AAA", 1, 1, 1.0)
    with pytest.raises(ValueError, match="duplicate record_id"):
        visible_news((duplicate, duplicate), dt(2))


def test_same_sign_persistence() -> None:
    assert same_sign_persistence((1.0, 2.0, 3.0, -1.0)) == pytest.approx(2 / 3)


def test_zero_tone_is_not_a_comparable_pair() -> None:
    assert same_sign_persistence((1.0, 0.0, -1.0, -2.0)) == pytest.approx(1.0)


def test_short_minus_long_persistence_is_deterministic() -> None:
    daily = {
        dt(day).date(): (1.0 if day >= 17 else (-1.0 if day % 2 else 1.0))
        for day in range(1, 22)
    }
    result = c31_persistence_state_from_daily_series(daily)
    assert -1.0 <= result <= 1.0


def test_insufficient_history_fails_closed() -> None:
    records = tuple(record("AAA", day, day, 1.0) for day in range(1, 10))
    with pytest.raises(ValueError, match="insufficient observed news days"):
        c31_persistence_state(records, dt(9))


def test_source_contract_is_public_and_nonproprietary() -> None:
    contract = source_contract()
    assert contract["source_family"] == "GDELT_GKG"
    assert contract["paid_api_required"] is False
    assert contract["performance_ready"] is False


def test_t_plus_one_text_mutation_cannot_change_state() -> None:
    base = tuple(
        record("AAA", day, day, 1.0 if day % 3 else -1.0)
        for day in range(1, 22)
    )
    baseline = c31_persistence_state(base, dt(21, 23))
    mutated = base + (record("AAA", 22, 22, -10000.0),)
    assert c31_persistence_state(mutated, dt(21, 23)) == baseline
