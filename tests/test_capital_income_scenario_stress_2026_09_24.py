import pytest

from automation.capital_income_scenario_stress_2026_09_24 import (
    POLICIES,
    SCENARIOS,
    run,
)


def test_scenario_matrix_is_fixed_and_complete():
    assert len(SCENARIOS) == 6
    assert len(POLICIES) == 3
    assert all(len(values) == 252 for values in SCENARIOS.values())


def test_scenario_paths_are_not_optimized():
    assert SCENARIOS["flat"] == (0.0,) * 252
    assert SCENARIOS["steady_growth"] == (0.0004,) * 252
    assert SCENARIOS["early_drawdown"][:42] == (-0.005,) * 42
    assert SCENARIOS["early_drawdown"][42:] == (0.0015,) * 210


def test_fixed_income_matrix_is_deterministic(tmp_path):
    a = run(tmp_path / "a.json")
    b = run(tmp_path / "b.json")
    assert a["report_fingerprint"] == b["report_fingerprint"]
    assert a["results"] == b["results"]


def test_flat_scenario_produces_no_payouts(tmp_path):
    report = run(tmp_path / "report.json")
    for policy in POLICIES:
        result = report["results"]["flat"][policy]
        assert result["total_payout_eur"] == pytest.approx(0.0)
        assert result["final_equity_eur"] == pytest.approx(500.0)


def test_protection_changes_payout_not_safety_floor(tmp_path):
    report = run(tmp_path / "report.json")
    full = report["results"]["steady_growth"]["full_payout"]
    protected = report["results"]["steady_growth"]["protected_income"]
    assert protected["total_payout_eur"] < full["total_payout_eur"]
    assert protected["ending_protected_capital_eur"] == pytest.approx(500.0)


def test_early_and_late_drawdown_have_distinct_sequence_payout_paths(tmp_path):
    report = run(tmp_path / "report.json")
    early = report["results"]["early_drawdown"]["balanced_capitalization"]
    late = report["results"]["late_drawdown"]["balanced_capitalization"]
    assert early["sequence_payout_difference_eur"] != late["sequence_payout_difference_eur"]
