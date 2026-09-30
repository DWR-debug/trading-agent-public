from __future__ import annotations

import json
from pathlib import Path

import pytest

from automation.frontier_feasibility import ILLUSION_LOOKBACK_SESSIONS, illusion_momentum_gap_at


def test_c29_preregistration_is_fixed_and_non_authorizing() -> None:
    spec = json.loads(
        Path("research/preregistrations/c29_fresh_coverage_pit_2026_09_30.json")
        .read_text(encoding="utf-8")
    )
    assert spec["trial_id"] == "T-2026-09-30-C29-COVERAGE-PIT"
    assert spec["universe"] == "validation_2026_09_30_c29_fresh_input"
    assert spec["symbols"] == ["PPG", "GWW", "PGR", "TT", "IR", "KLAC", "SNA", "SWK"]
    assert spec["fixed_mechanism"]["lookback_sessions"] == 21
    assert spec["governance"]["performance_trial_authorized"] is False
    assert spec["governance"]["holdout_used_for_selection"] is False


def test_c29_pit_mutation_boundary_is_explicit() -> None:
    prices = [100.0 + i for i in range(100)]
    decision = 50
    base = illusion_momentum_gap_at(prices, decision)

    future = prices.copy()
    for i in range(decision + 1, len(future)):
        future[i] *= (i + 3) * 10
    assert illusion_momentum_gap_at(future, decision) == base

    next_session = prices.copy()
    next_session[decision + 1] = 1.0
    assert illusion_momentum_gap_at(next_session, decision) == base


def test_c29_pit_requires_enough_history() -> None:
    with pytest.raises(IndexError):
        illusion_momentum_gap_at([100.0] * 10, 5, lookback_sessions=21)
