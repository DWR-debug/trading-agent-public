"""Tests for the paper-only 5m turn-of-the-candle control."""

from datetime import datetime, timezone

import pytest

from backtesting.models import Candle
from automation.microtrading_turn_candle_5m_2026_09_23 import (
    COST_MULTIPLIERS,
    EXPOSURE_LEVELS,
    PREVIOUS_MICRO_SYMBOLS,
    SYMBOLS,
    TURN_MINUTES,
    _is_turn_of_candle,
    _simulate_asset,
)


def _candle(minute: int, open_: float, close: float) -> Candle:
    return Candle(
        timestamp=datetime(
            2026, 1, 1, 12, minute, tzinfo=timezone.utc
        ),
        open=open_,
        high=max(open_, close),
        low=min(open_, close),
        close=close,
        volume=1.0,
    )


def test_turn_minutes_are_fixed() -> None:
    assert TURN_MINUTES == (0, 15, 30, 45)


@pytest.mark.parametrize("minute", [0, 15, 30, 45])
def test_turn_minute_is_detected(minute: int) -> None:
    assert _is_turn_of_candle(_candle(minute, 100.0, 101.0)) is True


@pytest.mark.parametrize("minute", [5, 10, 20, 25, 35, 40, 50, 55])
def test_non_turn_minute_is_not_detected(minute: int) -> None:
    assert _is_turn_of_candle(_candle(minute, 100.0, 101.0)) is False


def test_turn_signal_does_not_use_price_information() -> None:
    assert _is_turn_of_candle(_candle(15, 100.0, 130.0)) is True
    assert _is_turn_of_candle(_candle(15, 130.0, 100.0)) is True


def test_non_turn_bars_are_flat() -> None:
    rows = _simulate_asset(
        [
            _candle(10, 100.0, 105.0),
            _candle(15, 100.0, 110.0),
        ],
        1.0,
        2.0,
        0.0,
    )
    assert rows[0]["net_return"] == pytest.approx(0.0)
    assert rows[1]["gross_return"] == pytest.approx(0.20)


def test_cost_is_entry_plus_exit() -> None:
    rows = _simulate_asset(
        [_candle(15, 100.0, 101.0)],
        1.0,
        2.0,
        1.0,
    )
    assert rows[0]["turnover"] == pytest.approx(4.0)
    assert rows[0]["gross_return"] == pytest.approx(0.02)
    assert rows[0]["net_return"] == pytest.approx(
        0.02 - 0.0015 * 4.0
    )


def test_symbol_universe_is_disjoint() -> None:
    assert set(SYMBOLS).isdisjoint(PREVIOUS_MICRO_SYMBOLS)


def test_fixed_grids() -> None:
    assert EXPOSURE_LEVELS == (1.0, 2.0, 3.0)
    assert COST_MULTIPLIERS == (0.0, 0.25, 0.5, 1.0, 2.0, 4.0)
