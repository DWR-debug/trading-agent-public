import json

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


def test_history_loads_more_than_1000_candles(monkeypatch):
    batches = [
        [_kline(timestamp * 3_600_000) for timestamp in range(1000, 2000)],
        [_kline(timestamp * 3_600_000) for timestamp in range(200)],
    ]

    def fake_urlopen(url, timeout):
        return _response(batches.pop(0))

    monkeypatch.setattr(
        binance_loader.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    candles = binance_loader.load_binance_history(
        symbol="BTCUSDT",
        interval="1h",
        total=1200,
    )

    assert len(candles) == 1200

    for i in range(1, len(candles)):
        assert candles[i - 1].timestamp < candles[i].timestamp


def test_history_rejects_invalid_total():
    for total in (0, -1):
        try:
            binance_loader.load_binance_history(
                symbol="BTCUSDT",
                interval="1h",
                total=total,
            )
        except ValueError:
            continue

        raise AssertionError(
            f"Ungültige Anzahl {total} wurde akzeptiert."
        )
