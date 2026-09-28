from __future__ import annotations

from types import SimpleNamespace

import pytest

from automation.rccsm_state import state_at
from automation.rccsm_disagreement import disagreement_at


def _assets(n: int = 700):
    out = {}
    for offset, symbol in enumerate(("AAA", "BBB", "CCC", "DDD")):
        bars = []
        price = 100.0 + offset
        for i in range(n):
            drift = 0.0005 * (1 if i % 30 < 15 else -1)
            price *= 1.0 + drift + (offset - 1.5) * 0.00005
            bars.append(SimpleNamespace(close=price, volume=1000.0 + i))
        out[symbol] = tuple(bars)
    return out


def test_state_is_deterministic_and_bounded():
    assets = _assets()
    result = state_at(assets, 500, symbols=tuple(assets))
    assert 0.0 <= result["trend_coherence"] <= 1.0
    assert 0.0 <= result["breadth"] <= 1.0
    assert 0.0 <= result["dispersion_percentile"] <= 1.0
    assert 0.0 <= result["shock_density"] <= 1.0
    assert result["uses_future_bars"] is False
    assert result["uses_holdout"] is False
    assert result["uses_optimizer"] is False
    assert result == state_at(assets, 500, symbols=tuple(assets))


def test_future_bars_cannot_change_state():
    assets = _assets()
    baseline = state_at(assets, 500, symbols=tuple(assets))
    mutated = {symbol: list(bars) for symbol, bars in assets.items()}
    for bars in mutated.values():
        for i in range(501, len(bars)):
            bars[i] = SimpleNamespace(close=bars[i].close * 9.0, volume=bars[i].volume)
    assert state_at(mutated, 500, symbols=tuple(assets)) == baseline


def test_state_requires_sufficient_history():
    assets = _assets(100)
    with pytest.raises(ValueError):
        state_at(assets, 99, symbols=tuple(assets))


def test_disagreement_is_bounded_and_deterministic():
    assets = _assets(1000)
    result = disagreement_at(assets, 800, symbols=tuple(assets))
    assert 0.0 <= result["mechanism_disagreement"] <= 1.0
    assert 0.0 <= result["mean_pairwise_jaccard_overlap"] <= 1.0
    assert result["performance_evaluation"] is False
    assert result["uses_future_data"] is False
    assert result == disagreement_at(assets, 800, symbols=tuple(assets))


def test_future_bars_cannot_change_disagreement():
    assets = _assets(1000)
    baseline = disagreement_at(assets, 800, symbols=tuple(assets))
    mutated = {symbol: list(bars) for symbol, bars in assets.items()}
    for bars in mutated.values():
        for i in range(801, len(bars)):
            bars[i] = SimpleNamespace(close=bars[i].close * 0.05, volume=bars[i].volume)
    assert disagreement_at(mutated, 800, symbols=tuple(assets)) == baseline


def test_bad_prices_fail_closed():
    assets = _assets()
    assets["AAA"] = tuple(
        SimpleNamespace(close=(-1.0 if i == 300 else bar.close), volume=bar.volume)
        for i, bar in enumerate(assets["AAA"])
    )
    with pytest.raises(ValueError):
        state_at(assets, 500, symbols=tuple(assets))
