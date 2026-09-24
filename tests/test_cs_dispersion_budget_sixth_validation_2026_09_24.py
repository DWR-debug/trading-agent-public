import pytest

from automation.cs_dispersion_budget_sixth_validation_2026_09_24 import (
    CS_DISPERSION_LOOKBACK,
    CS_REBALANCE,
    CS_SKIP,
    CS_TOP_N,
    DISPERSION_REFERENCE_WINDOW,
    HOLDOUT_COUNT,
    RESEARCH_COUNT,
    TARGET_COUNT,
    _effective_cs_weights,
)


def test_fixed_sixth_validation_contract():
    assert (TARGET_COUNT, RESEARCH_COUNT, HOLDOUT_COUNT) == (3500, 2798, 700)
    assert (CS_DISPERSION_LOOKBACK, CS_REBALANCE, CS_SKIP, CS_TOP_N) == (21, 21, 21, 2)
    assert DISPERSION_REFERENCE_WINDOW == 63


def test_effective_cs_weight_never_exceeds_original_one_sleeve():
    bars = tuple(
        type("Bar", (), {"close": float(100 + i)})()
        for i in range(100)
    )
    assets = {symbol: bars for symbol in ("A", "B", "C", "D", "E")}
    fixed = tuple(
        {symbol: (0.5 if symbol in ("A", "B") else 0.0) for symbol in assets}
        for _ in range(100)
    )
    effective = _effective_cs_weights(assets, fixed)
    assert all(sum(weights.values()) <= 1.0 + 1e-15 for weights in effective)


def test_early_history_keeps_fixed_cs_selection_unchanged():
    bars = tuple(
        type("Bar", (), {"close": float(100 + i)})()
        for i in range(100)
    )
    assets = {symbol: bars for symbol in ("A", "B", "C", "D", "E")}
    fixed = tuple(
        {symbol: (0.5 if symbol in ("A", "B") else 0.0) for symbol in assets}
        for _ in range(100)
    )
    effective = _effective_cs_weights(assets, fixed)
    for index in range(84):
        assert effective[index] == fixed[index]
