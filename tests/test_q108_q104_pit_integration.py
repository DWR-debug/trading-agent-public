from __future__ import annotations

from automation.q108_q104_pit_integration import synthetic_future_mutation


def test_q108_all_future_mutation_invariants_pass():
    checks = synthetic_future_mutation()
    assert checks
    assert all(value is True for value in checks.values())
