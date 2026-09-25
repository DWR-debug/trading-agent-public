from __future__ import annotations

import json
from pathlib import Path

from automation.wide_search_triage import _classify, run


def test_wide_search_classes_are_deterministic():
    assert _classify({"fixed_rule": True, "fresh_disjoint_required": True, "coverage_stage": "available", "pit_path": "decision_bar_next_bar", "action": "coverage"}) == "ADVANCE_TO_COVERAGE"
    assert _classify({"fixed_rule": True, "fresh_disjoint_required": True, "coverage_stage": "unavailable", "pit_path": "missing", "action": "prune_data_contract"}) == "PRUNE_DATA_CONTRACT"
    assert _classify({"fixed_rule": True, "fresh_disjoint_required": True, "coverage_stage": "available", "pit_path": "decision_bar_next_bar", "action": "prune_duplicate_family"}) == "PRUNE_DUPLICATE_FAMILY"


def test_wide_search_catalog_is_fixed_at_twelve_hypotheses():
    catalog = json.loads(Path("research/exploration/hypothesis_catalog_2026_09_25.json").read_text(encoding="utf-8"))
    assert len(catalog["hypotheses"]) == 12
    assert len({item["id"] for item in catalog["hypotheses"]}) == 12


def test_wide_search_run_never_authorizes_performance(tmp_path):
    report = run(output_path=tmp_path / "triage.json")
    assert report["governance"]["performance_evaluation"] is False
    assert report["governance"]["holdout_evaluation"] is False
    assert report["governance"]["performance_trial_authorized"] is False
    assert all(item["performance_evaluation"] is False for item in report["results"])
