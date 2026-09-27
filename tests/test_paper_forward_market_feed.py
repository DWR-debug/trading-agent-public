from datetime import datetime, timedelta, timezone

import pytest

from automation.paper_forward_market_feed import fetch_closed_candles
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
