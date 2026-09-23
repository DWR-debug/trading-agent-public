import json
from urllib.parse import parse_qs, urlparse

from data import binance_loader


def _response(payload):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    return Response()


def _kline(timestamp_ms):
    return [
        timestamp_ms,
        "100.0",
        "101.0",
        "99.0",
        "100.5",
        "10.0",
    ]


def test_load_binance_candles(monkeypatch):
    payload = [
        _kline(1704067200000),
        _kline(1704070800000),
        _kline(1704074400000),
    ]

    monkeypatch.setattr(
        binance_loader.urllib.request,
        "urlopen",
        lambda url, timeout: _response(payload),
    )

    candles = binance_loader.load_binance_candles(
        symbol="BTCUSDT",
        interval="1h",
        limit=3,
    )

    assert len(candles) == 3
    assert all(candle.timestamp.tzinfo is not None for candle in candles)
    assert all(candle.open > 0 for candle in candles)
    assert all(candle.high > 0 for candle in candles)
    assert all(candle.low > 0 for candle in candles)
    assert all(candle.close > 0 for candle in candles)
    assert all(candle.volume >= 0 for candle in candles)
    assert candles[0].timestamp < candles[1].timestamp
    assert candles[1].timestamp < candles[2].timestamp


def test_binance_uses_market_data_endpoint():
    assert binance_loader.BASE_URL == (
        "https://data-api.binance.vision/api/v3/klines"
    )


def test_build_url_encodes_market_data_parameters():
    url = binance_loader._build_url(
        "btcusdt",
        "1h",
        1000,
        end_time=1234567890,
    )

    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "data-api.binance.vision"
    assert parsed.path == "/api/v3/klines"

    query = parse_qs(parsed.query)
    assert query["symbol"] == ["BTCUSDT"]
    assert query["interval"] == ["1h"]
    assert query["limit"] == ["1000"]
    assert query["endTime"] == ["1234567890"]
