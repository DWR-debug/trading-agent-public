from __future__ import annotations

from types import SimpleNamespace

from automation.rccsm_observational_feasibility import _fp, _mutate_future, _sample_indices


def _assets(n: int = 500):
    out = {}
    for offset, symbol in enumerate(("AAA", "BBB", "CCC", "DDD")):
        price = 100.0 + offset
        bars = []
        for i in range(n):
            price *= 1.0 + 0.0004 * (1 if i % 20 < 10 else -1)
            bars.append(SimpleNamespace(
                timestamp=f"2026-01-{(i % 28) + 1:02d}T00:00:00+00:00",
                open=price,
                high=price,
                low=price,
                close=price,
                volume=1000.0 + i,
            ))
        out[symbol] = tuple(bars)
    return out


def test_sample_indices_are_frozen():
    assert _sample_indices(1000) == (273, 400, 631, 862)


def test_future_mutation_preserves_observed_prefix():
    assets = _assets()
    mutated = _mutate_future(assets, 200, 11.0)
    for symbol in assets:
        assert mutated[symbol][:201] == assets[symbol][:201]


def test_future_mutation_changes_only_future_data():
    assets = _assets()
    mutated = _mutate_future(assets, 200, 11.0)
    assert mutated["AAA"][201].close != assets["AAA"][201].close
    assert mutated["AAA"][200] == assets["AAA"][200]


def test_fingerprint_is_deterministic():
    assert _fp({"a": 1, "b": [2, 3]}) == _fp({"b": [2, 3], "a": 1})


def test_observational_module_has_no_performance_authorization():
    import automation.rccsm_observational_feasibility as module
    assert module.Q089_COVERAGE_ID == "T-2026-09-28-089-COVERAGE"
