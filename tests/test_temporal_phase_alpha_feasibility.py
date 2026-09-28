from __future__ import annotations

from types import SimpleNamespace

import pytest

from automation.temporal_phase_alpha_feasibility import (
    MECHANISM_ID,
    WINDOW,
    phase_returns,
    temporal_wedge,
    future_mutation,
)


def _assets(n: int = 100):
    out = {}
    for offset, symbol in enumerate(("AAA", "BBB")):
        bars = []
        close = 100.0 + offset
        for i in range(n):
            open_price = close * (1.0 + 0.001 * ((i % 4) - 1))
            close = open_price * (1.0 + 0.0015 * (1 if i % 3 == 0 else -1))
            bars.append(
                SimpleNamespace(
                    timestamp=f"2026-01-{(i % 28) + 1:02d}T00:00:00+00:00",
                    open=open_price,
                    high=max(open_price, close),
                    low=min(open_price, close),
                    close=close,
                    volume=1000.0 + i,
                )
            )
        out[symbol] = tuple(bars)
    return out


def test_window_and_mechanism_are_frozen():
    assert WINDOW == 21
    assert MECHANISM_ID == "TTAF_NIGHT_DAY_TUG_OF_WAR_21"


def test_phase_decomposition_is_exact():
    assets = _assets()
    overnight, intraday = phase_returns(assets, 40, symbol="AAA")
    bars = assets["AAA"]
    assert overnight == pytest.approx(bars[40].open / bars[39].close - 1.0)
    assert intraday == pytest.approx(bars[40].close / bars[40].open - 1.0)


def test_temporal_wedge_is_second_component_difference():
    assets = _assets()
    result = temporal_wedge(assets, 50, symbol="AAA")
    assert result["temporal_wedge"] == pytest.approx(
        result["overnight_return_sum"] - result["intraday_return_sum"]
    )
    assert result["signal"] == pytest.approx(-result["temporal_wedge"])
    assert result["performance_evaluation"] is False


def test_future_mutation_does_not_change_current_ttaf():
    assets = _assets()
    baseline = temporal_wedge(assets, 70, symbol="AAA")
    mutated = future_mutation(assets, 70)
    assert temporal_wedge(mutated, 70, symbol="AAA") == baseline


def test_insufficient_history_fails_closed():
    with pytest.raises(ValueError):
        temporal_wedge(_assets(20), 19, symbol="AAA")
