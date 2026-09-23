import json
from datetime import datetime, timedelta, timezone

import pytest

from automation.verify_rolling_raw_archive import verify
from backtesting.models import Candle
from data.market_store import MarketDataStore
from research.protocol import dataset_fingerprint


def _candles(count=3):
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=start + timedelta(days=i),
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.5 + i,
            volume=1000.0 + i,
        )
        for i in range(count)
    )


def _manifest(store: MarketDataStore, candles):
    path = store.save("TEST", "1d", list(candles))
    return {
        "source": "yahoo_chart",
        "universe": "benchmark",
        "target_count": len(candles),
        "manifest_fingerprint": "manifest-fp",
        "datasets": [{
            "symbol": "TEST",
            "interval": "1d",
            "candle_count": len(candles),
            "fingerprint": dataset_fingerprint(candles),
        }],
    }, path


def test_verify_accepts_exact_archived_dataset(tmp_path):
    candles = _candles()
    store = MarketDataStore(base_dir=tmp_path / "data")
    manifest, _ = _manifest(store, candles)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = verify(
        manifest_path,
        data_dir=tmp_path / "data",
        expected_count=3,
        expected_symbols=("TEST",),
    )

    assert result["datasets"][0]["dataset_fingerprint"] == manifest["datasets"][0]["fingerprint"]
    assert result["datasets"][0]["candle_count"] == 3
    assert result["safety"]["paper_only"] is True
    assert result["safety"]["live_trading_enabled"] is False


def test_verify_rejects_modified_dataset(tmp_path):
    candles = _candles()
    store = MarketDataStore(base_dir=tmp_path / "data")
    manifest, _ = _manifest(store, candles)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    modified = list(candles)
    modified[-1] = Candle(
        timestamp=modified[-1].timestamp,
        open=modified[-1].open,
        high=modified[-1].high + 1.0,
        low=modified[-1].low,
        close=modified[-1].close,
        volume=modified[-1].volume,
    )
    store.save("TEST", "1d", modified)

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        verify(
            manifest_path,
            data_dir=tmp_path / "data",
            expected_count=3,
            expected_symbols=("TEST",),
        )


def test_verify_rejects_wrong_source(tmp_path):
    candles = _candles()
    store = MarketDataStore(base_dir=tmp_path / "data")
    manifest, _ = _manifest(store, candles)
    manifest["source"] = "other"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="Unexpected research data source"):
        verify(
            manifest_path,
            data_dir=tmp_path / "data",
            expected_count=3,
            expected_symbols=("TEST",),
        )
