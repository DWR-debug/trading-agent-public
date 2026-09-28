from pathlib import Path
import json

def test_q084_design_only():
    p = json.loads(Path("research/preregistrations/q084_design_2026_09_28.json").read_text(encoding="utf-8"))
    assert p["status"] == "PREREGISTERED_DESIGN_ONLY"
    assert p["governance"]["performance_trial_authorized"] is False
    assert p["governance"]["holdout_evaluation"] is False
    assert p["governance"]["family_ranking"] is False

def test_q084_automation_present():
    assert Path("automation/q084_candidate_feasibility.py").exists()
