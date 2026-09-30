from __future__ import annotations

import json
from pathlib import Path


def test_c29r1_preregistration_is_exact_repair_and_non_authorizing() -> None:
    spec = json.loads(
        Path("research/preregistrations/c29r1_fresh_coverage_pit_2026_09_30.json")
        .read_text(encoding="utf-8")
    )
    assert spec["trial_type"] == "repair_successor"
    assert spec["parent_trial_id"] == "T-2026-09-30-C29-COVERAGE-PIT"
    assert spec["universe"] == "validation_2026_09_30_c29r1_ice_repair_input"
    assert spec["symbols"] == ["PPG", "GWW", "PGR", "TT", "ICE", "KLAC", "SNA", "SWK"]
    assert spec["coverage_repair_basis"]["replacement_symbol"] == "ICE"
    assert spec["coverage_repair_basis"]["failed_parent_symbol"] == "IR"
    assert spec["fixed_mechanism"]["candidate"] == "frontier:C29"
    assert spec["fixed_mechanism"]["lookback_sessions"] == 21
    assert spec["governance"]["performance_evaluation"] is False
    assert spec["governance"]["holdout_evaluation"] is False
    assert spec["governance"]["asset_search"] is False
    assert spec["governance"]["candidate_ranking"] is False
    assert spec["governance"]["performance_trial_authorized"] is False


def test_c29r1_script_declares_fixed_identity() -> None:
    source = Path("automation/c29r1_fresh_pit.py").read_text(encoding="utf-8")
    assert 'TRIAL_ID = "T-2026-09-30-C29R1-COVERAGE-PIT"' in source
    assert 'SYMBOLS = ("PPG", "GWW", "PGR", "TT", "ICE", "KLAC", "SNA", "SWK")' in source
    assert '"performance_authorized": False' in source
    assert '"repair_only": True' in source
