from datetime import datetime, timezone

from backtesting.models import Candle
from data.quality import validate_candles


def make_candle(timestamp):
    return Candle(
        timestamp=datetime.fromisoformat(timestamp),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.0,
        volume=1000.0,
    )


def test_valid_candles_are_accepted():
    candles = [
        make_candle("2026-01-01T00:00:00+00:00"),
        make_candle("2026-01-01T00:01:00+00:00"),
        make_candle("2026-01-01T00:02:00+00:00"),
    ]

    validate_candles(candles)


def test_empty_candles_are_rejected():
    try:
        validate_candles([])
    except ValueError:
        return

    raise AssertionError("Leere Candle-Liste wurde akzeptiert.")


def test_duplicate_timestamps_are_rejected():
    candles = [
        make_candle("2026-01-01T00:00:00+00:00"),
        make_candle("2026-01-01T00:01:00+00:00"),
        make_candle("2026-01-01T00:01:00+00:00"),
    ]

    try:
        validate_candles(candles)
    except ValueError:
        return

    raise AssertionError("Doppelter Timestamp wurde akzeptiert.")


def test_unsorted_timestamps_are_rejected():
    candles = [
        make_candle("2026-01-01T00:00:00+00:00"),
        make_candle("2026-01-01T00:02:00+00:00"),
        make_candle("2026-01-01T00:01:00+00:00"),
    ]

    try:
        validate_candles(candles)
    except ValueError:
        return

    raise AssertionError("Unsortierte Candles wurden akzeptiert.")


def test_naive_timestamp_is_rejected():
    try:
        validate_candles([
            make_candle("2026-01-01T00:00:00")
        ])
    except ValueError:
        return

    raise AssertionError("Naiver Timestamp wurde akzeptiert.")
