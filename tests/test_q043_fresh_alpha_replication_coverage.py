import json
from pathlib import Path

def test_q043_preregistration_is_coverage_only():
    p=json.loads(Path("research/preregistrations/q043_fresh_alpha_replication_coverage_2026_09_27.json").read_text())
    assert p["status"]=="PREREGISTERED_COVERAGE_ONLY"
    assert p["requested_candles"]==4000
    assert p["target_candles"]==3500
    assert len(p["symbols"])==8
    assert p["governance"]["performance_trial_authorized"] is False
    assert p["governance"]["holdout_used_for_selection"] is False
