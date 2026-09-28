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


def test_canonical_snapshot_invalidates_previous_snapshot_on_failure(tmp_path):
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    valid = True

    def fake_loader(symbol, interval, total, **kwargs):
        if valid:
            return [Bar(base + timedelta(days=i), 100.0 + i) for i in range(8)]
        return [Bar(base + timedelta(days=i), 100.0 + i) for i in range(4)]

    spec = SnapshotSpec(
        universe="test",
        symbols=("AAA", "BBB"),
        interval="1d",
        requested_candles=8,
        target_common_candles=8,
        output_dir=tmp_path,
    )

    successful = build_frozen_snapshot(spec, loader=fake_loader)
    assert successful["status"] == "COVERAGE_PASSED"
    assert (tmp_path / "snapshot_manifest.json").exists()
    assert (tmp_path / "datasets").exists()

    valid = False
    failed = build_frozen_snapshot(spec, loader=fake_loader)

    assert failed["status"] == "DATA_INVALID"
    assert failed["data_snapshot"] is None
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


def test_snapshot_from_preregistration_accepts_frozen_top_level_target_geometry(tmp_path):
    from data.canonical_snapshot import snapshot_from_preregistration

    base = datetime(2020, 1, 1, tzinfo=timezone.utc)

    def fake_loader(symbol, interval, total, **kwargs):
        assert total == 10
        return [Bar(base + timedelta(days=i), 100.0 + i) for i in range(10)]

    result = snapshot_from_preregistration(
        {
            "trial_id": "T-Q067-GEOMETRY-COMPAT",
            "universe": "test",
            "symbols": ["AAA", "BBB"],
            "interval": "1d",
            "requested_candles": 10,
            "target_common_candles": 8,
        },
        output_root=tmp_path,
        loader=fake_loader,
    )

    assert result["status"] == "COVERAGE_PASSED"
    assert result["requested_candles"] == 10
    assert result["target_common_candles"] == 8


def test_canonical_snapshot_direct_layout_can_be_reloaded_and_verified(tmp_path):
    from data.canonical_snapshot import load_frozen_snapshot

    base = datetime(2020, 1, 1, tzinfo=timezone.utc)

    def fake_loader(symbol, interval, total, **kwargs):
        return [Bar(base + timedelta(days=i), 100.0 + i) for i in range(8)]

    result = build_frozen_snapshot(
        SnapshotSpec(
            universe="test",
            symbols=("AAA", "BBB"),
            interval="1d",
            requested_candles=8,
            target_common_candles=8,
            output_dir=tmp_path / "h06_repair_datasets",
            dataset_subdir=".",
        ),
        loader=fake_loader,
    )

    manifest = tmp_path / "h06_repair_datasets" / "snapshot_manifest.json"
    loaded = load_frozen_snapshot(manifest)

    assert result["status"] == "COVERAGE_PASSED"
    assert set(loaded) == {"AAA", "BBB"}
    assert all(len(candles) == 8 for candles in loaded.values())
    assert loaded["AAA"][0].timestamp == base
    assert loaded["AAA"][-1].timestamp == base + timedelta(days=7)


def test_load_frozen_snapshot_accepts_lowercase_coverage_status(tmp_path):
    from data.canonical_snapshot import load_frozen_snapshot

    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    root = tmp_path / "lowercase_status"
    dataset = root / "datasets"
    dataset.mkdir(parents=True)
    bars = [Bar(base + timedelta(days=i), 100.0 + i) for i in range(8)]

    import csv
    for symbol in ("AAA", "BBB"):
        path = dataset / f"{symbol}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp","open","high","low","close","volume"])
            for bar in bars:
                writer.writerow([bar.timestamp.isoformat(),bar.open,bar.high,bar.low,bar.close,bar.volume])

    from data.canonical_snapshot import dataset_fingerprint
    fp = dataset_fingerprint(tuple(
        type("Candle", (), {
            "timestamp": b.timestamp, "open": b.open, "high": b.high,
            "low": b.low, "close": b.close, "volume": b.volume
        })() for b in bars
    ))
    manifest = root / "snapshot_manifest.json"
    payload = {
        "status": "coverage_passed",
        "data_snapshot": {
            "datasets": [
                {"symbol":"AAA","path":str(dataset / "AAA.csv"),"candle_count":8,"fingerprint":fp},
                {"symbol":"BBB","path":str(dataset / "BBB.csv"),"candle_count":8,"fingerprint":fp},
            ]
        }
    }
    manifest.write_text(__import__("json").dumps(payload), encoding="utf-8")
    loaded = load_frozen_snapshot(manifest)
    assert set(loaded) == {"AAA","BBB"}
    assert len(loaded["AAA"]) == 8



def test_load_frozen_snapshot_normalizes_windows_manifest_separators(tmp_path):
    from data.canonical_snapshot import load_frozen_snapshot
    import csv
    import json
    from backtesting.models import Candle
    from research.protocol import dataset_fingerprint

    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    root = tmp_path / "windows_paths"
    dataset = root / "datasets"
    dataset.mkdir(parents=True)
    candles = tuple(
        Candle(
            timestamp=base + timedelta(days=i),
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.5 + i,
            volume=1000.0 + i,
        )
        for i in range(8)
    )
    path = dataset / "AAA.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for candle in candles:
            writer.writerow([
                candle.timestamp.isoformat(),
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
            ])

    windows_style_path = str(path).replace("/", "\\")
    manifest = root / "snapshot_manifest.json"
    manifest.write_text(json.dumps({
        "status": "COVERAGE_PASSED",
        "data_snapshot": {
            "datasets": [{
                "symbol": "AAA",
                "path": windows_style_path,
                "candle_count": len(candles),
                "fingerprint": dataset_fingerprint(candles),
            }]
        }
    }), encoding="utf-8")

    loaded = load_frozen_snapshot(manifest)
    assert tuple(loaded) == ("AAA",)
    assert loaded["AAA"] == candles
