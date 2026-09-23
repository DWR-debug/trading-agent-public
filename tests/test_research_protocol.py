from datetime import datetime, timedelta, timezone

from backtesting.models import Candle
from research.protocol import (
    ResearchProtocol,
    dataset_fingerprint,
    permutation_positive_tail_probability,
    split_holdout,
)


def make_candles(count=10):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=start + timedelta(minutes=i),
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000.0,
        )
        for i in range(count)
    )


def test_split_holdout_is_temporally_separate():
    candles = make_candles(10)
    research, holdout = split_holdout(
        candles,
        ResearchProtocol(holdout_ratio=0.2),
    )
    assert research == candles[:8]
    assert holdout == candles[8:]
    assert research[-1].timestamp < holdout[0].timestamp


def test_split_rejects_too_few_candles():
    try:
        split_holdout(
            make_candles(1),
            ResearchProtocol(),
        )
    except ValueError:
        return
    raise AssertionError("Zu wenige Candles wurden akzeptiert.")


def test_dataset_fingerprint_is_deterministic():
    candles = make_candles()
    assert dataset_fingerprint(candles) == dataset_fingerprint(candles)


def test_permutation_is_deterministic():
    pnls = (2.0, -1.0, 3.0, -0.5, 1.0, -0.5, 2.0, -1.0, 1.0, -0.5)
    first = permutation_positive_tail_probability(
        pnls,
        trials=100,
        seed=7,
    )
    second = permutation_positive_tail_probability(
        pnls,
        trials=100,
        seed=7,
    )
    assert first == second


def test_permutation_requires_enough_trades():
    assert permutation_positive_tail_probability(
        (1.0, -1.0),
        trials=100,
        seed=7,
    ) is None
