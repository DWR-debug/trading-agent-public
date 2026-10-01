from __future__ import annotations

from automation.q105_q104_historical_pit import synthetic_multi_source_clock, synthetic_sec_future_mutation


def test_q105_synthetic_sec_future_mutation_is_invariant():
    assert synthetic_sec_future_mutation() is True


def test_q105_synthetic_multi_source_clock_respects_public_availability():
    assert synthetic_multi_source_clock() is True
