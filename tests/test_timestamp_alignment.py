from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from automation.candidate_validation_50_50_vol_budget import _align_assets_by_latest_start


def test_latest_start_calendar_handles_leading_offset():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    early = tuple(SimpleNamespace(timestamp=start + timedelta(days=i), open=100.0, close=100.0) for i in range(6))
    late = tuple(SimpleNamespace(timestamp=start + timedelta(days=i), open=100.0, close=100.0) for i in range(1, 6))
    aligned = _align_assets_by_latest_start({"early": early, "late": late})
    assert tuple(bar.timestamp for bar in aligned["early"]) == tuple(bar.timestamp for bar in late)


def test_latest_start_calendar_rejects_unexpected_midstream_gap():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    reference = tuple(SimpleNamespace(timestamp=start + timedelta(days=i), open=100.0, close=100.0) for i in range(1, 6))
    broken = tuple(
        SimpleNamespace(timestamp=start + timedelta(days=i), open=100.0, close=100.0)
        for i in (0, 1, 2, 4, 5, 6)
    )
    try:
        _align_assets_by_latest_start({"reference": reference, "broken": broken})
    except ValueError as exc:
        assert "missing timestamps" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
