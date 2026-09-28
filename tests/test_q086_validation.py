from pathlib import Path
import json

def test_q086_prereg_is_not_authorized():
    p=json.loads(Path("research/preregistrations/q086_performance_2026_09_28.json").read_text())
    assert p["status"]=="PREREGISTERED_PERFORMANCE"
    assert p["governance"]["performance_trial_authorized"] is False
    assert p["selection_used"] is False
    assert p["holdout_used_for_selection"] is False

def test_q086_safety():
    p=json.loads(Path("research/preregistrations/q086_performance_2026_09_28.json").read_text())
    assert p["safety"]=={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}

def test_q086_harness_present():
    assert Path("automation/q086_coverage_pit.py").exists()
