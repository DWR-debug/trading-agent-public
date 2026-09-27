import json
from datetime import datetime, timedelta, timezone

import pytest

from automation.paper_forward_market_feed import fetch_closed_candles, update_from_binance
from tests.test_paper_forward_shadow import (
    make_candidate,
    make_candles as make_shadow_candles,
)
from backtesting.models import Candle


def make_candles():
    origin = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        Candle(
            timestamp=origin + timedelta(hours=i),
            open=100+i,
            high=101+i,
            low=99+i,
            close=100+i,
            volume=1000,
        )
        for i in range(3)
    ]


def test_fetch_closed_candles_drops_unclosed(monkeypatch):
    candles = make_candles()
    import automation.paper_forward_market_feed as feed

    class Clock:
        @staticmethod
        def now(tz=None):
            return datetime(2026, 1, 1, 2, 30, tzinfo=timezone.utc)

    monkeypatch.setattr(feed, "datetime", Clock)
    monkeypatch.setattr(feed, "load_binance_candles", lambda symbol, interval, limit: candles)
    result = fetch_closed_candles("BTCUSDT", "1h", limit=3)
    assert [c.timestamp for c in result] == [candles[0].timestamp, candles[1].timestamp]


def test_fetch_closed_candles_fails_on_empty(monkeypatch):
    monkeypatch.setattr(
        "automation.paper_forward_market_feed.load_binance_candles",
        lambda symbol, interval, limit: [],
    )
    with pytest.raises(Exception, match="no closed candles"):
        fetch_closed_candles("BTCUSDT", "1h", limit=3)


def test_update_links_deterministic_receipt_hashes_to_shadow_state(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    from automation import paper_forward_market_feed as feed
    from automation.paper_forward_shadow import start_session

    candidate = make_candidate()
    start_session(candidate, make_shadow_candles(3), state_path)
    incoming = make_shadow_candles(4, start=2)
    monkeypatch.setattr(feed, "fetch_closed_candles", lambda symbol, interval, limit: incoming)
    monkeypatch.setattr(feed, "BASE_URL", "https://example.invalid/klines")

    receipt_path = tmp_path / "receipt.json"
    updated = update_from_binance(state_path, fetch_limit=4, receipt_path=receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert receipt["fetched_at_utc"]
    assert receipt["receipt_fingerprint"] == updated["feed_receipt_fingerprint"]
    assert receipt["candle_fingerprint"] == updated["feed_candle_fingerprint"]
    assert receipt["fetch_fingerprint"] == updated["feed_fetch_fingerprint"]
    assert receipt["state_input_fingerprint"] == updated["input_fingerprint"]

    second = update_from_binance(state_path, fetch_limit=4)
    assert second["input_fingerprint"] == updated["input_fingerprint"]
