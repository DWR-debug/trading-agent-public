from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from automation.prepare_research_data import manifest_fingerprint, prepare, workflow_provenance
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
