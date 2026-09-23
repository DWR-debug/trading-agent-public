from datetime import datetime

from backtesting.models import Candle
from data.quality import validate_candles


def test_nan_price_is_rejected():
    candles = [
        Candle(
            timestamp=datetime.fromisoformat("2026-01-01T00:00:00"),
            open=float("nan"),
            high=101.0,
            low=99.0,
            close=100.0,
            volume=1000.0,
        )
    ]

    try:
        validate_candles(candles)
    except ValueError:
        return

    raise AssertionError("NaN-Preis wurde akzeptiert.")


def test_infinite_price_is_rejected():
    candles = [
        Candle(
            timestamp=datetime.fromisoformat("2026-01-01T00:00:00"),
            open=float("inf"),
            high=float("inf"),
            low=99.0,
            close=100.0,
            volume=1000.0,
        )
    ]

    try:
        validate_candles(candles)
    except ValueError:
        return

    raise AssertionError("Unendlicher Preis wurde akzeptiert.")
