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
