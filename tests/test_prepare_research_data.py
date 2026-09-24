from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from automation.prepare_research_data import (
    _trim_to_common_calendar,
    manifest_fingerprint,
    prepare,
    workflow_provenance,
)
from backtesting.models import Candle


def make_candles(
    count=500,
    interval=timedelta(hours=1),
):
    end = datetime.now(timezone.utc) - interval - timedelta(minutes=1)
    start = end - interval * (count - 1)
    return tuple(
        Candle(
            timestamp=start + interval * i,
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.0,
            volume=1000.0,
        )
        for i in range(count)
    )



def test_trim_to_common_calendar_aligns_offset_asset_starts(tmp_path):
    from data.market_store import MarketDataStore

    store = MarketDataStore(tmp_path / "data")
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    assets = {
        "AAA": [
            Candle(
                timestamp=start + timedelta(days=i),
                open=100 + i,
                high=101 + i,
                low=99 + i,
                close=100 + i,
                volume=1000.0,
            )
            for i in range(7)
        ],
        "BBB": [
            Candle(
                timestamp=start + timedelta(days=i),
                open=200 + i,
                high=201 + i,
                low=199 + i,
                close=200 + i,
                volume=1000.0,
            )
            for i in range(1, 8)
        ],
        "CCC": [
            Candle(
                timestamp=start + timedelta(days=i),
                open=300 + i,
                high=301 + i,
                low=299 + i,
                close=300 + i,
                volume=1000.0,
            )
            for i in range(7)
        ],
    }

    for symbol, candles in assets.items():
        store.save(symbol, "1d", candles)

    prepared = [
        ("AAA", "1d", "yahoo_chart"),
        ("BBB", "1d", "yahoo_chart"),
        ("CCC", "1d", "yahoo_chart"),
    ]
    result = _trim_to_common_calendar(store, prepared, 5)

    assert result["raw_common_candle_count"] == 6
    assert result["aligned_candle_count"] == 5

    expected_timestamps = [
        start + timedelta(days=i)
        for i in range(2, 7)
    ]
    for symbol, _, _ in prepared:
        loaded = store.load(symbol, "1d")
        assert len(loaded) == 5
        assert [c.timestamp for c in loaded] == expected_timestamps


def test_trim_to_common_calendar_fails_closed_when_overlap_is_too_short(tmp_path):
    from data.market_store import MarketDataStore

    store = MarketDataStore(tmp_path / "data")
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    store.save(
        "AAA",
        "1d",
        [
            Candle(
                timestamp=start + timedelta(days=i),
                open=100 + i,
                high=101 + i,
                low=99 + i,
                close=100 + i,
                volume=1000.0,
            )
            for i in range(5)
        ],
    )
    store.save(
        "BBB",
        "1d",
        [
            Candle(
                timestamp=start + timedelta(days=i),
                open=200 + i,
                high=201 + i,
                low=199 + i,
                close=200 + i,
                volume=1000.0,
            )
            for i in range(1, 5)
        ],
    )

    prepared = [
        ("AAA", "1d", "yahoo_chart"),
        ("BBB", "1d", "yahoo_chart"),
    ]

    try:
        _trim_to_common_calendar(store, prepared, 5)
    except ValueError as exc:
        assert "Zu wenig gemeinsame Kalender-Candles" in str(exc)
    else:
        raise AssertionError("Zu kurze Kalender-Schnittmenge muss abgelehnt werden.")

def test_prepare_creates_manifest(tmp_path):
    class Result:
        def __init__(self, symbol, interval):
            self.symbol = symbol
            self.interval = interval

    def load(symbol, interval):
        delta = (
            timedelta(hours=1)
            if interval == "1h"
            else timedelta(minutes=15)
        )
        return list(make_candles(interval=delta))

    with patch(
        "automation.prepare_research_data.update_all",
        return_value=[
            Result("BTCUSDT", "1h"),
            Result("BTCUSDT", "15m"),
            Result("ETHUSDT", "1h"),
            Result("ETHUSDT", "15m"),
        ],
    ), patch(
        "automation.prepare_research_data.MarketDataStore.load",
        side_effect=load,
    ):
        manifest, path = prepare(
            500,
            output_path=tmp_path / "manifest.json",
        )

    assert Path(path).exists()
    assert manifest["safety"]["orders_enabled"] is False
    assert len(manifest["datasets"]) == 4
    assert manifest["manifest_fingerprint"] == manifest_fingerprint(manifest)
    assert all(
        item["candle_count"] == 500
        for item in manifest["datasets"]
    )


def test_prepare_records_workflow_provenance(tmp_path, monkeypatch):
    class Result:
        def __init__(self, symbol, interval):
            self.symbol = symbol
            self.interval = interval

    values = {
        "GITHUB_SHA": "abc123",
        "GITHUB_WORKFLOW": "Prepare Research Data",
        "GITHUB_RUN_ID": "12345",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_EVENT_NAME": "schedule",
        "GITHUB_REF_NAME": "master",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)

    def load(symbol, interval):
        delta = (
            timedelta(hours=1)
            if interval == "1h"
            else timedelta(minutes=15)
        )
        return list(make_candles(interval=delta))

    with patch(
        "automation.prepare_research_data.update_all",
        return_value=[
            Result("BTCUSDT", "1h"),
            Result("BTCUSDT", "15m"),
            Result("ETHUSDT", "1h"),
            Result("ETHUSDT", "15m"),
        ],
    ), patch(
        "automation.prepare_research_data.MarketDataStore.load",
        side_effect=load,
    ):
        manifest, _ = prepare(500, output_path=tmp_path / "manifest.json")

    assert manifest["provenance"] == workflow_provenance()
    assert manifest["provenance"]["commit_sha"] == "abc123"
    assert manifest["provenance"]["event_name"] == "schedule"
