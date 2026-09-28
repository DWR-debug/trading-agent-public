import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from automation.q067_alpha_mechanisms import (
    Q067_SLEEVES,
    apply_turnover_hysteresis,
    build_alpha_sleeves,
    equal_weight_ensemble,
)
from automation.q068_fresh_coverage import FROZEN_SYMBOLS
from automation import q068_pit


def _bar(ts, value):
    return type(
        "Bar",
        (),
        {
            "timestamp": ts,
            "open": value,
            "high": value + 1.0,
            "low": value - 1.0,
            "close": value,
            "volume": 1000.0,
        },
    )()


def _assets(count=3500):
    base = datetime(2011, 1, 3, tzinfo=timezone.utc)
    return {
        symbol: tuple(
            _bar(base + timedelta(days=i), 100.0 + i + slot)
            for i in range(count)
        )
        for slot, symbol in enumerate(FROZEN_SYMBOLS)
    }


def test_q068_symbols_are_frozen_and_distinct():
    assert FROZEN_SYMBOLS == ("ETR", "PPL", "WEC", "FE", "D", "EXR", "PSA", "O")
    assert len(FROZEN_SYMBOLS) == len(set(FROZEN_SYMBOLS))


def test_q068_reuses_exact_six_sleeves_without_sleeve_drift():
    assets = _assets(300)
    sleeves = build_alpha_sleeves(assets, symbols=FROZEN_SYMBOLS)
    assert tuple(sleeves) == Q067_SLEEVES


def test_q068_ensemble_is_bounded():
    assets = _assets(3500)
    sleeves = build_alpha_sleeves(assets, symbols=FROZEN_SYMBOLS)
    ensemble = equal_weight_ensemble(sleeves, symbols=FROZEN_SYMBOLS)
    assert all(sum(row.values()) <= 1.0 + 1e-12 for row in ensemble)


def test_q068_turnover_hysteresis_keeps_entry_exit_semantics():
    symbols = FROZEN_SYMBOLS
    aggregate = (
        {symbol: (0.125 if symbol == symbols[0] else 0.0) for symbol in symbols},
        {symbol: (0.10 if symbol == symbols[0] else 0.0) for symbol in symbols},
        {symbol: 0.0 for symbol in symbols},
    )
    out = apply_turnover_hysteresis(aggregate, symbols=symbols)
    assert out[1][symbols[0]] == out[0][symbols[0]]
    assert out[2][symbols[0]] == 0.0


def test_q068_pit_constants_are_fixed():
    assert q068_pit.Q068_SYMBOLS == FROZEN_SYMBOLS
    assert q068_pit.COVERAGE_TRIAL_ID == "T-2026-09-28-068-COVERAGE"
    assert q068_pit.PIT_TRIAL_ID == "T-2026-09-28-068-PIT"
    assert q068_pit.STEP == 113
    assert q068_pit.MIN_HISTORY == 273
