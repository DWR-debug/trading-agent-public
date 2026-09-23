from datetime import timezone

from data.time_utils import parse_timestamp


def test_naive_timestamp_is_interpreted_as_utc():
    timestamp = parse_timestamp("2026-01-01T00:00:00")
    assert timestamp.tzinfo == timezone.utc


def test_offset_timestamp_is_normalized_to_utc():
    timestamp = parse_timestamp("2026-01-01T01:00:00+01:00")
    assert timestamp.tzinfo == timezone.utc
    assert timestamp.hour == 0
