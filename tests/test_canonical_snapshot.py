from datetime import datetime, timedelta, timezone

from data.canonical_snapshot import SnapshotSpec, build_frozen_snapshot


class Bar:
    def __init__(self, ts, value):
        self.timestamp = ts
        self.open = value
        self.high = value + 1.0
        self.low = value - 1.0
        self.close = value + 0.25
        self.volume = value


def test_canonical_snapshot_aligns_exact_common_calendar(tmp_path):
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    calendars = {
        "AAA": [base + timedelta(days=i) for i in range(10)],
        "BBB": [base + timedelta(days=i) for i in range(1, 11)],
    }

    def fake_loader(symbol, interval, total, **kwargs):
        assert interval == "1d"
        assert total == 10
        return [Bar(ts, 100.0 + i) for i, ts in enumerate(calendars[symbol])]

    result = build_frozen_snapshot(
        SnapshotSpec(
            universe="test",
            symbols=("AAA", "BBB"),
            interval="1d",
            requested_candles=10,
            target_common_candles=8,
            output_dir=tmp_path,
        ),
        loader=fake_loader,
    )

    assert result["status"] == "COVERAGE_PASSED"
    assert result["coverage"]["common_calendar_count"] == 9
    assert result["selected_common_calendar_start"] == (base + timedelta(days=2)).isoformat()
    assert result["selected_common_calendar_end"] == (base + timedelta(days=9)).isoformat()
    assert all(item["candle_count"] == 8 for item in result["data_snapshot"]["datasets"])
    assert all(item["fingerprint"] for item in result["data_snapshot"]["datasets"])


def test_canonical_snapshot_fails_closed_without_partial_artifacts(tmp_path):
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)

    def fake_loader(symbol, interval, total, **kwargs):
        return [Bar(base + timedelta(days=i), 100.0 + i) for i in range(4)]

    result = build_frozen_snapshot(
        SnapshotSpec(
            universe="test",
            symbols=("AAA", "BBB"),
            interval="1d",
            requested_candles=10,
            target_common_candles=8,
            output_dir=tmp_path,
        ),
        loader=fake_loader,
    )

    assert result["status"] == "DATA_INVALID"
    assert result["data_snapshot"] is None
    assert not (tmp_path / "snapshot_manifest.json").exists()
    assert not (tmp_path / "datasets").exists()


def test_canonical_snapshot_filters_fixed_study_window_before_intersection(tmp_path):
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)

    def fake_loader(symbol, interval, total, **kwargs):
        return [Bar(base + timedelta(days=i), 100.0 + i) for i in range(10)]

    result = build_frozen_snapshot(
        SnapshotSpec(
            universe="test",
            symbols=("AAA", "BBB"),
            interval="1d",
            requested_candles=10,
            target_common_candles=5,
            output_dir=tmp_path,
            study_start=(base + timedelta(days=2)).date(),
            study_end=(base + timedelta(days=8)).date(),
        ),
        loader=fake_loader,
    )

    assert result["status"] == "COVERAGE_PASSED"
    assert result["coverage"]["common_calendar_count"] == 7
    assert result["selected_common_calendar_start"] == (base + timedelta(days=4)).isoformat()
    assert result["selected_common_calendar_end"] == (base + timedelta(days=8)).isoformat()


def test_canonical_snapshot_fingerprint_is_stable_across_runs(tmp_path):
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)

    def fake_loader(symbol, interval, total, **kwargs):
        return [Bar(base + timedelta(days=i), 100.0 + i) for i in range(8)]

    spec = SnapshotSpec(
        universe="test",
        symbols=("AAA", "BBB"),
        interval="1d",
        requested_candles=8,
        target_common_candles=8,
        output_dir=tmp_path,
    )
    first = build_frozen_snapshot(spec, loader=fake_loader)
    second = build_frozen_snapshot(spec, loader=fake_loader)

    assert first["snapshot_fingerprint"] == second["snapshot_fingerprint"]


def test_snapshot_from_preregistration_uses_data_contract(tmp_path):
    from data.canonical_snapshot import snapshot_from_preregistration

    base = datetime(2020, 1, 1, tzinfo=timezone.utc)

    def fake_loader(symbol, interval, total, **kwargs):
        assert total == 10
        return [Bar(base + timedelta(days=i), 100.0 + i) for i in range(10)]

    result = snapshot_from_preregistration(
        {
            "trial_id": "T-TEST",
            "universe": "test",
            "symbols": ["AAA", "BBB"],
            "interval": "1d",
            "data_contract": {
                "requested_raw_candles_per_symbol": 10,
                "target_common_calendar": 8,
            },
        },
        output_root=tmp_path,
        loader=fake_loader,
    )

    assert result["status"] == "COVERAGE_PASSED"
    assert result["target_common_candles"] == 8
    assert result["data_snapshot"]["format"] == "csv_ohlcv_common_calendar"
