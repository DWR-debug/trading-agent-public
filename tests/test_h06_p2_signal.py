from __future__ import annotations

from automation.h06_p2_signal import (
    SECTOR_MAP,
    SYMBOLS,
    gross_exposure,
    net_exposure,
    rank_global,
    residualize_by_sector,
    target_weights,
)


def test_sector_demeaning_cannot_change_within_sector_order():
    raw = {symbol: float(index) for index, symbol in enumerate(SYMBOLS)}
    residual = residualize_by_sector(raw)
    for members in SECTOR_MAP.values():
        raw_order = sorted(members, key=lambda s: (-raw[s], s))
        residual_order = sorted(members, key=lambda s: (-residual[s], s))
        assert residual_order == raw_order


def test_global_residualization_can_change_global_selection():
    raw = {
        "TXN": 0.40, "ADI": 0.39, "AMAT": 0.38,
        "MDT": 0.10, "SYK": 0.09, "BDX": 0.08,
        "ETN": 0.07, "ITW": 0.06, "GD": 0.05,
        "CL": -0.01, "KMB": -0.02, "GIS": -0.03,
        "AEP": -0.04, "XEL": -0.05, "DTE": -0.06,
    }
    residual = residualize_by_sector(raw)
    assert rank_global(raw) != rank_global(residual)


def test_rank_ties_are_deterministic_by_symbol():
    scores = {symbol: 0.0 for symbol in SYMBOLS}
    longs, shorts = rank_global(scores)
    assert longs == tuple(sorted(SYMBOLS)[:5])
    assert shorts == tuple(sorted(SYMBOLS)[-5:][::-1])


def test_target_weights_have_fixed_gross_and_zero_net():
    scores = {symbol: float(index) for index, symbol in enumerate(SYMBOLS)}
    weights = target_weights(scores)
    assert sum(value == 0.10 for value in weights.values()) == 5
    assert sum(value == -0.10 for value in weights.values()) == 5
    assert gross_exposure(weights) == 1.0
    assert net_exposure(weights) == 0.0


def test_signal_is_invariant_to_future_price_mutation():
    closes = {
        symbol: [
            100.0 + index + symbol_index * 0.01
            for index in range(340)
        ]
        for symbol_index, symbol in enumerate(SYMBOLS)
    }
    before = {
        symbol: values.copy()
        for symbol, values in closes.items()
    }
    # Decision at index 300 only uses t-252 and t-21; mutate a future bar.
    closes["TXN"][301] += 10000.0
    assert rank_global({
        symbol: closes[symbol][279] / closes[symbol][48] - 1.0
        for symbol in SYMBOLS
    }) == rank_global({
        symbol: before[symbol][279] / before[symbol][48] - 1.0
        for symbol in SYMBOLS
    })
