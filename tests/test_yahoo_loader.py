from datetime import datetime, timedelta, timezone

import pytest

from data import yahoo_loader


def test_yahoo_loader_parses_daily_history(monkeypatch):
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [
                        int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()),
                        int(datetime(2026, 1, 2, tzinfo=timezone.utc).timestamp()),
                    ],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10.0, 11.0],
                                "high": [11.0, 12.0],
                                "low": [9.0, 10.0],
                                "close": [10.5, 11.5],
                                "volume": [1000.0, 1200.0],
                            }
                        ]
                    },
                }
            ]
        }
    }

    monkeypatch.setattr(yahoo_loader, "_fetch_json", lambda _url: payload)

    candles = yahoo_loader.load_yahoo_history("TEST", total=2)

    assert len(candles) == 2
    assert candles[0].close == 10.5
    assert candles[1].volume == 1200.0


def test_yahoo_loader_excludes_unclosed_daily_candle_before_ohlc_validation(
    monkeypatch,
):
    now = datetime.now(timezone.utc)
    closed = now - timedelta(days=2)
    open_candle = now - timedelta(hours=12)

    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [
                        int(closed.timestamp()),
                        int(open_candle.timestamp()),
                    ],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10.0, 11.0],
                                "high": [11.0, 12.0],
                                "low": [9.0, 11.1],
                                "close": [10.5, 11.5],
                                "volume": [1000.0, 1200.0],
                            }
                        ]
                    },
                }
            ]
        }
    }

    monkeypatch.setattr(yahoo_loader, "_fetch_json", lambda _url: payload)

    candles = yahoo_loader.load_yahoo_history(
        "TEST", total=2, allow_partial=True
    )

    assert len(candles) == 1
    assert candles[0].close == 10.5


def test_yahoo_loader_excludes_unclosed_daily_candle(monkeypatch):
    now = datetime.now(timezone.utc)
    closed = now - timedelta(days=2)
    open_candle = now - timedelta(hours=12)

    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [
                        int(closed.timestamp()),
                        int(open_candle.timestamp()),
                    ],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10.0, 11.0],
                                "high": [11.0, 12.0],
                                "low": [9.0, 10.0],
                                "close": [10.5, 11.5],
                                "volume": [1000.0, 1200.0],
                            }
                        ]
                    },
                }
            ]
        }
    }

    monkeypatch.setattr(yahoo_loader, "_fetch_json", lambda _url: payload)

    candles = yahoo_loader.load_yahoo_history(
        "TEST", total=2, allow_partial=True
    )

    assert len(candles) == 1
    assert candles[0].close == 10.5


def test_yahoo_loader_rejects_unsupported_interval():
    with pytest.raises(ValueError, match="Intervall"):
        yahoo_loader.load_yahoo_history("TEST", interval="1h", total=2)



def test_yahoo_loader_can_explicitly_skip_invalid_vendor_ohlc(monkeypatch):
    closed = datetime.now(timezone.utc) - timedelta(days=2)

    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [
                        int((closed - timedelta(days=1)).timestamp()),
                        int(closed.timestamp()),
                    ],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10.0, 11.0],
                                "high": [11.0, 12.0],
                                "low": [9.0, 11.5],
                                "close": [10.5, 11.5],
                                "volume": [1000.0, 1200.0],
                            }
                        ]
                    },
                }
            ]
        }
    }

    monkeypatch.setattr(yahoo_loader, "_fetch_json", lambda _url: payload)

    quality = {}
    candles = yahoo_loader.load_yahoo_history(
        "TEST",
        total=2,
        allow_partial=True,
        skip_invalid_ohlc=True,
        quality_report=quality,
    )

    assert len(candles) == 1
    assert quality["rows_skipped_invalid_ohlc"] == 1
    assert quality["rows_returned"] == 1


def test_yahoo_loader_remains_strict_by_default(monkeypatch):
    closed = datetime.now(timezone.utc) - timedelta(days=2)

    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [int(closed.timestamp())],
                    "indicators": {
                        "quote": [
                            {
                                "open": [11.0],
                                "high": [12.0],
                                "low": [11.5],
                                "close": [11.5],
                                "volume": [1200.0],
                            }
                        ]
                    },
                }
            ]
        }
    }

    monkeypatch.setattr(yahoo_loader, "_fetch_json", lambda _url: payload)

    with pytest.raises(ValueError, match="Low muss höchstens"):
        yahoo_loader.load_yahoo_history("TEST", total=1)
