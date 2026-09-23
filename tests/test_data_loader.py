from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from data.binance_loader import load_binance_history

from data.csv_loader import load_candles


def test_load_valid_csv():
    path = "tests/sample_candles.csv"

    candles = load_candles(path)

    assert len(candles) == 3
    assert candles[0].timestamp == datetime(
        2026,
        1,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )
    assert candles[0].open == 100.0
    assert candles[0].high == 103.0
    assert candles[0].low == 99.0
    assert candles[0].close == 102.0
    assert candles[0].volume == 1000.0


def test_candles_are_sorted_by_timestamp():
    path = "tests/sample_candles_unsorted.csv"

    candles = load_candles(path)

    assert candles[0].timestamp < candles[1].timestamp
    assert candles[1].timestamp < candles[2].timestamp


def test_invalid_price_is_rejected():
    path = "tests/sample_candles_invalid.csv"

    try:
        load_candles(path)
    except ValueError:
        return

    raise AssertionError("Ungültige Candle wurde akzeptiert.")


def test_missing_column_is_rejected():
    path = "tests/sample_candles_missing_column.csv"

    try:
        load_candles(path)
    except ValueError:
        return

    raise AssertionError("CSV mit fehlender Spalte wurde akzeptiert.")


def test_empty_csv_is_rejected():
    path = "tests/sample_candles_empty.csv"

    try:
        load_candles(path)
    except ValueError:
        return

    raise AssertionError("Leere CSV wurde akzeptiert.")


def test_load_binance_history_excludes_open_latest_candle():
    now = datetime.now(timezone.utc)
    interval = timedelta(hours=1)
    closed_start = now - timedelta(hours=5)

    def row(timestamp, price):
        return [
            int(timestamp.timestamp() * 1000),
            str(price),
            str(price + 1),
            str(price - 1),
            str(price),
            "10.0",
        ]

    open_timestamp = now - timedelta(minutes=30)
    payload = [
        row(closed_start + interval * index, 100 + index)
        for index in range(4)
    ] + [row(open_timestamp, 104)]

    with patch(
        "data.binance_loader._fetch_json",
        return_value=payload,
    ) as fetch:
        candles = load_binance_history("BTCUSDT", "1h", 4)

    assert fetch.call_count == 1
    assert len(candles) == 4
    assert candles[-1].timestamp < open_timestamp
