import json
from pathlib import Path


def test_q071_source_feasibility_design_has_six_frozen_families():
    p = json.loads(
        Path("research/exploration/q071_information_source_feasibility_2026_09_28.json")
        .read_text(encoding="utf-8")
    )
    assert p["status"] == "DESIGN_ONLY"
    assert [c["id"] for c in p["candidates"]] == ["I1", "I2", "I3", "I4", "I5", "I6"]
    assert p["governance"]["performance_trial_authorized"] is False
    assert p["governance"]["no_family_ranking"] is True
    assert p["governance"]["coverage_before_pit"] is True
    assert p["governance"]["pit_before_performance"] is True


def test_q071_probe_script_is_design_only():
    text = Path("automation/q071_source_feasibility.py").read_text(encoding="utf-8")
    assert "performance_evaluation" in text
    assert "holdout_used_for_selection" in text
    assert "selection_used" in text
    assert "no_family_ranking" in text
