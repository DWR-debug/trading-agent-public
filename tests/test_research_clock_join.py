import pytest

from automation.research_clock_join import build_join, synthetic_contract


def test_clock_join_synthetic_contract():
    assert all(synthetic_contract().values())


def _event(source="SEC", event_id="1", available="2026-10-01T12:05:00+00:00"):
    return {
        "source_id": source,
        "entity_id": "E1",
        "event_id": event_id,
        "observed_at": "2026-10-01T12:00:00+00:00",
        "available_at": available,
        "eligible_session": "2026-10-02",
        "value_fingerprint": "x",
    }


def test_clock_join_rejects_future_information():
    with pytest.raises(ValueError, match="CLOCK_FUTURE_INFORMATION"):
        build_join([_event(available="2026-10-01T16:00:00+00:00")], decision_cutoff="2026-10-01T15:00:00+00:00", eligible_session="2026-10-02")


def test_clock_join_rejects_session_mismatch():
    e = _event()
    e["eligible_session"] = "2026-10-03"
    with pytest.raises(ValueError, match="CLOCK_SESSION_MISMATCH"):
        build_join([e], decision_cutoff="2026-10-01T15:00:00+00:00", eligible_session="2026-10-02")


def test_clock_join_rejects_duplicate_event():
    with pytest.raises(ValueError, match="CLOCK_DUPLICATE_EVENT"):
        build_join([_event(), _event()], decision_cutoff="2026-10-01T15:00:00+00:00", eligible_session="2026-10-02")
