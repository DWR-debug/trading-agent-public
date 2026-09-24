from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError

import data.gdelt_events as gdelt_events
from data.gdelt_events import (
    GDELT_EVENT_FIELD_COUNT,
    parse_event_row,
    parse_event_tsv,
)


def row():
    values = [""] * GDELT_EVENT_FIELD_COUNT
    values[0], values[7], values[17] = "123", "USA", "RUS"
    values[26], values[27], values[28], values[29] = "190", "190", "19", "3"
    values[30], values[31], values[32], values[33], values[34] = "-3.5", "12", "4", "3", "-2.0"
    values[51], values[56], values[57] = "SY", "20260924123000", "https://example.com"
    return values


def test_point_in_time_parser():
    event = parse_event_row(row())
    assert event.event_id == 123
    assert event.date_added.isoformat() == "2026-09-24T12:30:00+00:00"
    assert event.event_root_code == "19"
    assert event.quad_class == 3


def test_tsv_parser():
    assert len(tuple(parse_event_tsv("\t".join(row()) + "\n"))) == 1


def test_daily_58_and_intraday_61_dateadded_formats_are_supported():
    values58 = row()
    event58 = parse_event_row(values58)
    assert event58.date_added.isoformat() == "2026-09-24T12:30:00+00:00"

    values61 = values58[:56] + ["", "", "", "20260924123000", "https://example.com/61"]
    assert len(values61) == 61
    event61 = parse_event_row(values61)
    assert event61.date_added.isoformat() == "2026-09-24T12:30:00+00:00"
    assert event61.source_url == "https://example.com/61"


def test_daily_dateonly_is_supported():
    values = row()
    values[56] = "20250101"
    event = parse_event_row(values)
    assert event.date_added.isoformat() == "2025-01-01T00:00:00+00:00"


def test_non_strict_parser_counts_skipped_rows():
    bad = "\t".join(["x"] + [""] * 9) + "\n"
    stats = {}
    assert tuple(parse_event_tsv(bad, strict=False, stats=stats)) == ()
    assert stats["rows_seen"] == 1
    assert stats["rows_skipped"] == 1


class _Response:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.payload


def test_daily_export_falls_back_to_aws_raw_tsv_and_records_source(monkeypatch, tmp_path: Path):
    day = datetime(2025, 6, 14, tzinfo=timezone.utc)
    payload = ("\t".join(row()) + "\n").encode("utf-8")
    primary = gdelt_events.daily_export_url(day)
    mirror = gdelt_events.daily_export_mirror_url(day)

    def fake_urlopen(request, timeout):
        assert timeout == 60
        if request.full_url == primary:
            raise HTTPError(primary, 404, "Not Found", hdrs=None, fp=None)
        assert request.full_url == mirror
        return _Response(payload)

    monkeypatch.setattr(gdelt_events, "urlopen", fake_urlopen)
    destination = tmp_path / "2025-06-14.zip"

    result = gdelt_events.download_daily_export(day, destination)

    assert result == destination
    assert destination.exists()
    events = tuple(gdelt_events.parse_event_zip(destination))
    assert len(events) == 1
    source = destination.with_suffix(".source.json").read_text(encoding="utf-8")
    assert '"fallback_used": true' in source
    assert mirror in source
