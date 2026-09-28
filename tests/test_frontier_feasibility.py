from __future__ import annotations

import math

import pytest

from automation.frontier_feasibility import (
    illusion_momentum_gap,
    illusion_momentum_gap_at,
    industry_relative_reversal_residual,
    industry_relative_reversal_residual_at,
    simple_returns_from_closes,
)


def test_c29_matches_compound_minus_sum() -> None:
    returns = (0.10, -0.05, 0.02)
    expected = (1.10 * 0.95 * 1.02 - 1.0) - sum(returns)
    assert math.isclose(illusion_momentum_gap(returns), expected, rel_tol=0, abs_tol=1e-15)


def test_c29_rejects_invalid_return_domain() -> None:
    with pytest.raises(ValueError):
        illusion_momentum_gap((0.05, -1.0))


def test_c29_future_mutation_is_inert() -> None:
    closes = [100.0 + i for i in range(80)]
    decision_index = 50
    baseline = illusion_momentum_gap_at(closes, decision_index)
    mutated = closes.copy()
    for i in range(decision_index + 1, len(mutated)):
        mutated[i] *= 10.0 + i
    assert illusion_momentum_gap_at(mutated, decision_index) == baseline


def test_c29_next_session_mutation_is_inert() -> None:
    closes = [100.0 + i for i in range(80)]
    decision_index = 50
    baseline = illusion_momentum_gap_at(closes, decision_index)
    mutated = closes.copy()
    mutated[decision_index + 1] = 1.0
    assert illusion_momentum_gap_at(mutated, decision_index) == baseline


def test_m4_subtracts_industry_mean() -> None:
    returns = {"AAA": 0.10, "BBB": 0.02, "CCC": 0.04}
    industries = {"AAA": "X", "BBB": "X", "CCC": "Y"}
    residuals = industry_relative_reversal_residual(returns, industries)
    assert math.isclose(residuals["AAA"], 0.04, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(residuals["BBB"], -0.04, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(residuals["CCC"], 0.0, rel_tol=0, abs_tol=1e-15)


def test_m4_requires_pit_industry_mapping() -> None:
    with pytest.raises(ValueError):
        industry_relative_reversal_residual(
            {"AAA": 0.1, "BBB": 0.2},
            {"AAA": "X"},
        )


def test_m4_future_mutation_is_inert() -> None:
    closes = {
        "AAA": [100.0 + i for i in range(80)],
        "BBB": [80.0 + i for i in range(80)],
        "CCC": [120.0 + i for i in range(80)],
    }
    industries = {"AAA": "X", "BBB": "X", "CCC": "Y"}
    decision_index = 50
    baseline = industry_relative_reversal_residual_at(closes, industries, decision_index)
    mutated = {symbol: values.copy() for symbol, values in closes.items()}
    for values in mutated.values():
        for i in range(decision_index + 1, len(values)):
            values[i] *= 8.0
    assert industry_relative_reversal_residual_at(mutated, industries, decision_index) == baseline


def test_m4_next_session_mutation_is_inert() -> None:
    closes = {
        "AAA": [100.0 + i for i in range(80)],
        "BBB": [80.0 + i for i in range(80)],
        "CCC": [120.0 + i for i in range(80)],
    }
    industries = {"AAA": "X", "BBB": "X", "CCC": "Y"}
    decision_index = 50
    baseline = industry_relative_reversal_residual_at(closes, industries, decision_index)
    mutated = {symbol: values.copy() for symbol, values in closes.items()}
    for values in mutated.values():
        values[decision_index + 1] = 1.0
    assert industry_relative_reversal_residual_at(mutated, industries, decision_index) == baseline


def test_close_conversion_is_deterministic() -> None:
    closes = (100.0, 101.0, 99.0)
    assert simple_returns_from_closes(closes) == pytest.approx((0.01, -0.019801980198019804))
