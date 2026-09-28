from pathlib import Path
import json


def test_q083_is_design_only():
    p = json.loads(
        Path("research/preregistrations/q083_design_2026_09_28.json")
        .read_text(encoding="utf-8")
    )
    assert p["status"] == "PREREGISTERED_DESIGN_ONLY"
    assert p["governance"]["performance_trial_authorized"] is False
    assert p["governance"]["holdout_evaluation"] is False
    assert p["governance"]["selection_used"] is False


def test_q083_safety_is_fail_closed():
    p = json.loads(
        Path("research/preregistrations/q083_design_2026_09_28.json")
        .read_text(encoding="utf-8")
    )
    assert p["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_q083_automation_is_present():
    assert Path("automation/q083_candidate_feasibility.py").exists()
