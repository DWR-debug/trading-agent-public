from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory

from backtesting.models import Candle
from data.market_store import MarketDataStore
from data.market_updater import update_all, update_dataset


def make_candle(timestamp, close):
    return Candle(
        timestamp=timestamp,
        open=close,
        high=close + 1,
        low=close - 1,
        close=close,
        volume=10.0,
    )


def fake_loader(symbol, interval, limit):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    return [
        make_candle(
            start + timedelta(hours=index),
            100 + index,
        )
        for index in range(limit)
    ]


def test_update_new_dataset():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)

        result = update_dataset(
            "BTCUSDT",
            "1h",
            5,
            store=store,
            loader=fake_loader,
            refresh_count=5,
        )

        assert result.symbol == "BTCUSDT"
        assert result.previous_count == 0
        assert result.fetched_count == 5
        assert result.final_count == 5
        assert len(store.load("BTCUSDT", "1h")) == 5



def test_initial_import_requests_full_target_count():
    calls = []

    def tracking_loader(symbol, interval, limit):
        calls.append(limit)
        return fake_loader(symbol, interval, limit)

    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)

        result = update_dataset(
            "BTCUSDT",
            "1h",
            20,
            store=store,
            loader=tracking_loader,
            refresh_count=3,
        )

    assert calls == [20]
    assert result.final_count == 20



def test_update_existing_dataset_merges():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)

        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        store.save(
            "BTCUSDT",
            "1h",
            [
                make_candle(start + timedelta(hours=index), 50 + index)
                for index in range(3)
            ],
        )

        result = update_dataset(
            "BTCUSDT",
            "1h",
            5,
            store=store,
            loader=fake_loader,
            refresh_count=5,
        )

        candles = store.load("BTCUSDT", "1h")

        assert result.previous_count == 3
        assert result.fetched_count == 5
        assert result.final_count == 5
        assert [c.close for c in candles] == [
            100,
            101,
            102,
            103,
            104,
        ]


def test_refresh_count_limits_download():
    calls = []

    def tracking_loader(symbol, interval, limit):
        calls.append(limit)
        return fake_loader(symbol, interval, limit)

    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)

        start = datetime(2025, 12, 1, tzinfo=timezone.utc)
        store.save(
            "BTCUSDT",
            "1h",
            [
                make_candle(
                    start + timedelta(hours=index),
                    50 + index,
                )
                for index in range(5)
            ],
        )

        update_dataset(
            "BTCUSDT",
            "1h",
            20,
            store=store,
            loader=tracking_loader,
            refresh_count=3,
        )

    assert calls == [3]


def test_update_all():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)

        results = update_all(
            [
                ("BTCUSDT", "1h", 3),
                ("ETHUSDT", "1h", 3),
            ],
            store=store,
            loader=fake_loader,
            refresh_count=3,
        )

        assert len(results) == 2
        assert results[0].final_count == 3
        assert results[1].final_count == 3


def test_invalid_target_count():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)

        try:
            update_dataset(
                "BTCUSDT",
                "1h",
                0,
                store=store,
                loader=fake_loader,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "target_count=0 muss abgelehnt werden."
            )


def test_invalid_refresh_count():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)

        try:
            update_dataset(
                "BTCUSDT",
                "1h",
                10,
                store=store,
                loader=fake_loader,
                refresh_count=0,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "refresh_count=0 muss abgelehnt werden."
            )



def test_update_existing_dataset_drops_open_candle():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)
        now = datetime.now(timezone.utc)
        open_timestamp = now - timedelta(minutes=30)

        store.save(
            "BTCUSDT",
            "1h",
            [
                make_candle(
                    datetime(2026, 1, 1, tzinfo=timezone.utc)
                    + timedelta(hours=index),
                    50 + index,
                )
                for index in range(3)
            ]
            + [make_candle(open_timestamp, 60)],
        )

        update_dataset(
            "BTCUSDT",
            "1h",
            5,
            store=store,
            loader=fake_loader,
            refresh_count=5,
        )

        candles = store.load("BTCUSDT", "1h")
        assert open_timestamp not in [
            candle.timestamp for candle in candles
        ]
        assert len(candles) == 5


if __name__ == "__main__":
    tests = [
        test_update_new_dataset,
        test_initial_import_requests_full_target_count,
        test_update_existing_dataset_merges,
        test_refresh_count_limits_download,
        test_update_all,
        test_invalid_target_count,
        test_invalid_refresh_count,
    ]

    for test in tests:
        test()

    print(f"{len(tests)}/{len(tests)} Market-Updater-Tests bestanden.")

    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)
        now = datetime.now(timezone.utc)
        open_timestamp = now - timedelta(minutes=30)

        store.save(
            "BTCUSDT",
            "1h",
            [
                make_candle(
                    datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=index),
                    50 + index,
                )
                for index in range(3)
            ] + [make_candle(open_timestamp, 60)],
        )

        update_dataset(
            "BTCUSDT",
            "1h",
            5,
            store=store,
            loader=fake_loader,
            refresh_count=5,
        )

        candles = store.load("BTCUSDT", "1h")
        assert open_timestamp not in [candle.timestamp for candle in candles]
        assert len(candles) == 5
