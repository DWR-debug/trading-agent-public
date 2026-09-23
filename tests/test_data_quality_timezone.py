from datetime import datetime, timezone

from backtesting.models import Candle
from data.quality import validate_candles


def make_candle(timestamp):
    return Candle(
        timestamp=timestamp,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.0,
        volume=1000.0,
    )


def test_naive_timestamp_is_rejected():
    candles = [
        make_candle(datetime(2026, 1, 1, 0, 0, 0)),
    ]

    try:
        validate_candles(candles)
    except ValueError:
        return

    raise AssertionError(
        "Naiver Timestamp wurde akzeptiert."
    )


def test_utc_timestamp_is_accepted():
    candles = [
        make_candle(
            datetime(
                2026,
                1,
                1,
                0,
                0,
                0,
                tzinfo=timezone.utc,
            )
        ),
    ]

    validate_candles(candles)
