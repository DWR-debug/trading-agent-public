from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from backtesting.models import Candle
from data.market_store import MarketDataStore


def make_candle(timestamp, close):
    return Candle(
        timestamp=timestamp,
        open=close,
        high=close + 1,
        low=close - 1,
        close=close,
        volume=10.0,
    )


def test_save_and_load():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        candles = [
            make_candle(start, 100),
            make_candle(start + timedelta(hours=1), 101),
        ]

        path = store.save("btcusdt", "1h", candles)

        assert Path(path).exists()
        loaded = store.load("BTCUSDT", "1h")
        assert loaded == candles


def test_missing_file_returns_empty_list():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)
        assert store.load("BTCUSDT", "1h") == []


def test_merge_deduplicates_and_replaces_newer_candle():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        store.save(
            "BTCUSDT",
            "1h",
            [
                make_candle(start, 100),
                make_candle(start + timedelta(hours=1), 101),
            ],
        )

        merged = store.merge(
            "BTCUSDT",
            "1h",
            [
                make_candle(start + timedelta(hours=1), 111),
                make_candle(start + timedelta(hours=2), 102),
            ],
        )

        assert len(merged) == 3
        assert merged[1].close == 111
        assert merged[2].close == 102


def test_merge_can_trim_to_target_count():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        candles = [
            make_candle(
                start + timedelta(hours=index),
                100 + index,
            )
            for index in range(5)
        ]

        result = store.merge(
            "BTCUSDT",
            "1h",
            candles,
            target_count=3,
        )

        assert len(result) == 3
        assert [c.close for c in result] == [102, 103, 104]


def test_merge_and_save_persists_merged_data():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        path = store.merge_and_save(
            "ETHUSDT",
            "15m",
            [
                make_candle(start, 200),
                make_candle(start + timedelta(minutes=15), 201),
            ],
        )

        assert Path(path).exists()
        assert len(store.load("ETHUSDT", "15m")) == 2


def test_invalid_target_count_is_rejected():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        try:
            store.merge(
                "BTCUSDT",
                "1h",
                [make_candle(start, 100)],
                target_count=0,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "target_count=0 muss abgelehnt werden."
            )


def test_invalid_empty_save_is_rejected():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)

        try:
            store.save("BTCUSDT", "1h", [])
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Leere Candle-Liste muss abgelehnt werden."
            )


if __name__ == "__main__":
    tests = [
        test_save_and_load,
        test_missing_file_returns_empty_list,
        test_merge_deduplicates_and_replaces_newer_candle,
        test_merge_can_trim_to_target_count,
        test_merge_and_save_persists_merged_data,
        test_invalid_target_count_is_rejected,
        test_invalid_empty_save_is_rejected,
    ]

    for test in tests:
        test()

    print(f"{len(tests)}/{len(tests)} Market-Store-Tests bestanden.")
