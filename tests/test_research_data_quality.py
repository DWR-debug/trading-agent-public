from datetime import datetime, timedelta, timezone

import pytest

from backtesting.models import Candle
from research.data_quality import validate_research_dataset


def make_candles(count=4, interval=timedelta(hours=1)):
    start = datetime(2026, 9, 21, 8, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=start + interval * i,
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.0,
            volume=1000.0,
        )
        for i in range(count)
    )


def make_daily_candles(timestamps):
    return tuple(
        Candle(
            timestamp=timestamp,
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.0,
            volume=1000.0,
        )
        for timestamp in timestamps
    )


def test_research_quality_accepts_complete_dataset():
    candles = make_candles()
    now = candles[-1].timestamp + timedelta(hours=1)

    validate_research_dataset(
        candles,
        "1h",
        expected_count=4,
        now=now,
    )


def test_research_quality_accepts_normal_daily_market_gap():
    candles = make_daily_candles(
        (
            datetime(2026, 9, 18, tzinfo=timezone.utc),
            datetime(2026, 9, 21, tzinfo=timezone.utc),
        )
    )
    now = candles[-1].timestamp + timedelta(days=1)

    validate_research_dataset(candles, "1d", now=now)


def test_research_quality_accepts_daily_dataset_after_weekend():
    candles = make_daily_candles(
        (
            datetime(2026, 9, 18, 13, 30, tzinfo=timezone.utc),
        )
    )
    now = datetime(2026, 9, 21, 20, 8, tzinfo=timezone.utc)

    validate_research_dataset(candles, "1d", now=now)


def test_research_quality_rejects_time_gap():
    candles = list(make_candles(count=3))
    candles[2] = Candle(
        timestamp=candles[2].timestamp + timedelta(hours=1),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.0,
        volume=1000.0,
    )

    with pytest.raises(ValueError, match="Zeitlücke"):
        validate_research_dataset(
            candles,
            "1h",
            now=candles[-1].timestamp + timedelta(minutes=30),
        )


def test_research_quality_rejects_excessive_daily_gap():
    candles = make_daily_candles(
        (
            datetime(2026, 9, 1, tzinfo=timezone.utc),
            datetime(2026, 9, 9, tzinfo=timezone.utc),
        )
    )
    now = candles[-1].timestamp + timedelta(days=1)

    with pytest.raises(ValueError, match="mehr als sieben"):
        validate_research_dataset(candles, "1d", now=now)


def test_research_quality_rejects_duplicate_timestamp():
    candles = list(make_candles(count=3))
    candles[2] = Candle(
        timestamp=candles[1].timestamp,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.0,
        volume=1000.0,
    )

    with pytest.raises(ValueError, match="Doppelte Candle-Timestamps"):
        validate_research_dataset(
            candles,
            "1h",
            now=candles[-1].timestamp + timedelta(minutes=30),
        )


def test_research_quality_rejects_wrong_interval():
    candles = make_candles(count=3)

    with pytest.raises(ValueError, match="Zeitlücke"):
        validate_research_dataset(
            candles,
            "15m",
            now=candles[-1].timestamp + timedelta(minutes=30),
        )


def test_research_quality_rejects_ohlc_inconsistency():
    candles = list(make_candles())
    object.__setattr__(candles[1], "high", 99.0)

    with pytest.raises(ValueError, match="High ist zu klein"):
        validate_research_dataset(
            candles,
            "1h",
            now=candles[-1].timestamp + timedelta(minutes=30),
        )


def test_research_quality_rejects_incomplete_last_candle():
    candles = make_candles()
    now = candles[-1].timestamp + timedelta(minutes=30)

    with pytest.raises(ValueError, match="noch nicht abgeschlossen"):
        validate_research_dataset(candles, "1h", now=now)


def test_research_quality_rejects_future_candle():
    candles = make_candles()
    now = candles[-1].timestamp - timedelta(minutes=1)

    with pytest.raises(ValueError, match="Zukünftige Candle"):
        validate_research_dataset(candles, "1h", now=now)


def test_research_quality_rejects_stale_dataset():
    candles = make_candles()
    now = candles[-1].timestamp + timedelta(hours=4)

    with pytest.raises(ValueError, match="zu alt"):
        validate_research_dataset(
            candles,
            "1h",
            now=now,
            max_age_intervals=3,
        )


def test_research_quality_rejects_wrong_count():
    candles = make_candles()

    with pytest.raises(ValueError, match="Falsche Candle-Anzahl"):
        validate_research_dataset(
            candles,
            "1h",
            expected_count=5,
            now=candles[-1].timestamp + timedelta(minutes=30),
        )


def test_research_quality_rejects_negative_volume():
    candles = list(make_candles())
    object.__setattr__(candles[2], "volume", -1.0)

    with pytest.raises(ValueError, match="Ungültiges Volumen"):
        validate_research_dataset(
            candles,
            "1h",
            now=candles[-1].timestamp + timedelta(minutes=30),
        )



def test_research_quality_accepts_exact_intraday_freshness_boundary():
    candles = make_candles()
    now = candles[-1].timestamp + timedelta(hours=3)

    validate_research_dataset(
        candles,
        "1h",
        now=now,
        max_age_intervals=3,
    )


def test_research_quality_rejects_one_second_beyond_intraday_boundary():
    candles = make_candles()
    now = candles[-1].timestamp + timedelta(hours=3, seconds=1)

    with pytest.raises(ValueError, match="zu alt"):
        validate_research_dataset(
            candles,
            "1h",
            now=now,
            max_age_intervals=3,
        )


def test_research_quality_accepts_exact_daily_freshness_boundary():
    candles = make_daily_candles(
        (datetime(2026, 9, 18, 13, 30, tzinfo=timezone.utc),)
    )
    now = candles[-1].timestamp + timedelta(days=7)

    validate_research_dataset(candles, "1d", now=now)


def test_research_quality_rejects_one_second_beyond_daily_boundary():
    candles = make_daily_candles(
        (datetime(2026, 9, 18, 13, 30, tzinfo=timezone.utc),)
    )
    now = candles[-1].timestamp + timedelta(days=7, seconds=1)

    with pytest.raises(ValueError, match="zu alt"):
        validate_research_dataset(candles, "1d", now=now)
