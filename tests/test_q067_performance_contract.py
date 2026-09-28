import json
from pathlib import Path


def test_q067_performance_preregistration_is_fixed_and_unranked():
    p = json.loads(
        Path("research/preregistrations/q067_performance_2026_09_28.json").read_text(
            encoding="utf-8"
        )
    )
    assert p["status"] == "PREREGISTERED_PERFORMANCE"
    assert p["symbols"] == ["ANSS", "ROP", "NVR", "ZION", "SLB", "EIX", "K", "CCL"]
    assert p["governance"]["parameter_search"] is False
    assert p["governance"]["family_ranking"] is False
    assert p["governance"]["selection"] is False
    assert p["governance"]["holdout_used_for_selection"] is False
    assert p["governance"]["automatic_promotion"] is False
    assert len(p["arms"]) == 3


def test_q067_formal_workflow_path_is_retired():
    assert not Path(".github/workflows/q067-fixed-mechanism-performance.yml").exists()
    assert Path("automation/q067_performance.py").exists()

def test_q067_performance_authorization_is_retired_and_not_present():
    assert not Path("research/authorizations/q067_performance_2026_09_28.json").exists()
    assert not Path("research/evidence/q067_performance_result.json").exists()
