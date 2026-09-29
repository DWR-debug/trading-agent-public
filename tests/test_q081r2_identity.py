from __future__ import annotations

import json
from pathlib import Path

from automation import q081r2_corrected_e1_e2_performance as runner


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research" / "preregistrations" / "q081r2_performance_2026_09_28.json"


def test_q081r2_runner_identity_matches_preregistration() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert prereg["trial_id"] == "T-2026-09-28-081R2-PERFORMANCE"
    assert runner.TRIAL_ID == prereg["trial_id"]
    assert isinstance(prereg["governance"]["performance_trial_authorized"], bool)
    assert prereg["correction"]["new_parameters"] is False
    assert prereg["correction"]["new_thresholds"] is False
    assert prereg["correction"]["asset_selection"] is False
    assert prereg["correction"]["direction_reversal"] is False


def test_q081r2_source_contract_names_dedicated_runner() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    source_contract = prereg["source_contract"]
    assert "automation/q081r2_corrected_e1_e2_performance.py" in source_contract
    assert "automation/q081r1_corrected_e1_e2_performance.py" not in source_contract
