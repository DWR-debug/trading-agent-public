from __future__ import annotations

import json
from pathlib import Path

from automation import q081r3_python_literal_fix_performance as runner

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research" / "preregistrations" / "q081r3_python_literal_fix_2026_09_30.json"


def test_q081r3_runner_identity_matches_preregistration() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert prereg["trial_id"] == "T-2026-09-30-081R3-PERFORMANCE"
    assert runner.TRIAL_ID == prereg["trial_id"]
    assert prereg["governance"]["performance_trial_authorized"] is False
    correction = prereg["correction"]
    assert correction["new_parameters"] is False
    assert correction["new_thresholds"] is False
    assert correction["asset_selection"] is False
    assert correction["direction_reversal"] is False
    assert correction["changed_data"] is False
    assert correction["changed_pit"] is False
    assert correction["changed_horizon"] is False
    assert correction["changed_variants"] is False
    assert correction["predecessor_implementation_incident"] == "T-2026-09-28-081R2-PERFORMANCE"
    assert correction["predecessor_execution_run_id"] == "36639171349"


def test_q081r3_source_contract_is_dedicated_and_literal_fixed() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    source_contract = prereg["source_contract"]
    assert "automation/q081r3_python_literal_fix_performance.py" in source_contract
    assert "automation/q081r2_corrected_e1_e2_performance.py" not in source_contract
    source = (ROOT / "automation" / "q081r3_python_literal_fix_performance.py").read_text(encoding="utf-8")
    assert '"new_tunable_parameters": False' in source
    assert '"new_tunable_parameters": false' not in source
    assert "Q081R2" not in source
