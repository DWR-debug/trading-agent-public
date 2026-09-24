from pathlib import Path

import pytest

from automation.trial_015_mean_reversion_global_etf_2026_09_24 import (
    SYMBOLS,
    THRESHOLD,
    WINDOW,
    _target_path,
)
from strategies.mean_reversion import MeanReversionStrategy
from strategies.signals import SignalType


def test_trial_015_signal_contract_is_fixed():
    assert WINDOW == 5
    assert THRESHOLD == 0.02
    assert len(SYMBOLS) == 8


def test_mean_reversion_target_enters_after_downside_deviation():
    strategy = MeanReversionStrategy(window=5, threshold=0.02)
    prices = [100.0, 100.0, 100.0, 100.0, 97.0]
    targets = _target_path(prices, strategy)
    assert targets[-1] == 1.0


def test_mean_reversion_target_exits_after_upside_deviation():
    strategy = MeanReversionStrategy(window=5, threshold=0.02)
    prices = [100.0, 100.0, 100.0, 100.0, 97.0, 103.0]
    targets = _target_path(prices, strategy)
    assert targets[-2] == 1.0
    assert targets[-1] == 0.0


def test_mean_reversion_target_holds_inside_band():
    strategy = MeanReversionStrategy(window=5, threshold=0.02)
    prices = [100.0, 100.0, 100.0, 100.0, 97.0, 99.0]
    targets = _target_path(prices, strategy)
    assert targets[-2:] == [1.0, 1.0]


def test_mean_reversion_signal_types_are_long_flat_only():
    strategy = MeanReversionStrategy(window=5, threshold=0.02)
    buy = strategy.generate_signal_validated("x", [100, 100, 100, 100, 97])
    sell = strategy.generate_signal_validated("x", [100, 100, 100, 100, 103])
    assert buy.signal is SignalType.BUY
    assert sell.signal is SignalType.SELL
    assert buy.confidence <= 1.0
    assert sell.confidence <= 1.0
