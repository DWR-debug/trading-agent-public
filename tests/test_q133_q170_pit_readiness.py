from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_q133_q170_pit_wave_preserves_source_receipt_boundary():
    data = json.loads(
        (ROOT / "research/frontier/q133_q170_pit_readiness_wave_2026_10_03.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["status"] == "PIT_READINESS_GATE_ONLY"
    assert data["source_receipt"]["source_probe_pass_count"] == 25
    assert data["source_receipt"]["source_feasible_candidate_count"] == 21
    assert data["candidate_status_boundary"]["pit_validated"] is False


def test_q133_q170_pit_module_is_fail_closed_for_science():
    text = (ROOT / "automation/q133_q170_pit_readiness.py").read_text(encoding="utf-8")
    for marker in (
        '"performance": False',
        '"holdout_selection": False',
        '"candidate_ranking": False',
        '"parameter_search": False',
        '"horizon_search": False',
        '"live_execution": False',
        '"AUTOMATIC_PROMOTION": False',
    ):
        assert marker in text


def test_q133_q170_pit_module_has_no_return_metric_or_search_logic():
    text = (ROOT / "automation/q133_q170_pit_readiness.py").read_text(encoding="utf-8")
    forbidden = ("Sharpe", "profit factor", "grid search", "threshold sweep", "return evaluation")
    lowered = text.lower()
    for marker in forbidden:
        assert marker.lower() not in lowered
