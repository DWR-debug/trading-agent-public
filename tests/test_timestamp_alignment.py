from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from automation.candidate_validation_50_50_vol_budget import _return_rows

def bars(start, count, offset=0):
    return tuple(SimpleNamespace(timestamp=start + timedelta(days=i), open=100.0+i, close=100.0+i) for i in range(offset, offset+count))

def test_return_rows_aligns_by_realization_timestamp():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assets = {"A": bars(start, 5, 0), "B": bars(start, 5, 1)}
    weights = tuple({"A": 0.0, "B": 0.0} for _ in range(5))
    adjusted = {s: {bar.timestamp: bar.close for bar in series} for s, series in assets.items()}
    rows = _return_rows(assets, weights, adjusted)
    assert [row["timestamp"] for row in rows] == [
        datetime(2026, 1, 3, tzinfo=timezone.utc),
        datetime(2026, 1, 4, tzinfo=timezone.utc),
        datetime(2026, 1, 5, tzinfo=timezone.utc),
        datetime(2026, 1, 6, tzinfo=timezone.utc),
    ]
