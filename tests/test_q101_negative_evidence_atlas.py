from __future__ import annotations

import json
from pathlib import Path

from automation.q101_negative_evidence_atlas import analyze


def test_q101_is_retrospective_and_detects_recurring_risk_failures() -> None:
    root = Path(__file__).parents[1]
    inputs = [
        root / "research/evidence/q077r1_performance_result.json",
        root / "research/evidence/q081r4_performance_result.json",
        root / "research/evidence/q089_performance_result.json",
        root / "research/evidence/q091_performance_result.json",
        root / "research/evidence/q094_performance_result.json",
        root / "research/evidence/q095_performance_result.json",
        root / "research/evidence/c29_performance_result.json",
        root / "research/evidence/cross_trial_failure_diagnosis_2026_09_25.json",
    ]
    result = analyze(inputs)
    assert result["status"] == "RETROSPECTIVE_DIAGNOSTIC_ONLY"
    assert result["trial_count"] == 7
    assert result["governance"]["new_backtest"] is False
    assert result["governance"]["candidate_selection"] is False
    assert result["governance"]["holdout_selection"] is False
    gate_names = {row["gate"] for row in result["gate_recurrence"]}
    assert "research_drawdown_lte_10pct" in gate_names
    assert "rolling_average_drawdown_lte_10pct" in gate_names
    assert "holdout_drawdown_lte_10pct" in gate_names
    assert any(lesson["id"] == "NEG-01" for lesson in result["lessons"])


def test_q101_fingerprint_is_stable() -> None:
    root = Path(__file__).parents[1]
    inputs = [
        root / "research/evidence/q077r1_performance_result.json",
        root / "research/evidence/q081r4_performance_result.json",
        root / "research/evidence/q089_performance_result.json",
        root / "research/evidence/q091_performance_result.json",
        root / "research/evidence/q094_performance_result.json",
        root / "research/evidence/q095_performance_result.json",
        root / "research/evidence/c29_performance_result.json",
        root / "research/evidence/cross_trial_failure_diagnosis_2026_09_25.json",
    ]
    a = analyze(inputs)
    b = analyze(inputs)
    assert a["analysis_fingerprint"] == b["analysis_fingerprint"]
