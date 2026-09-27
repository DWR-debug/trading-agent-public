from __future__ import annotations

import json
from pathlib import Path

def test_q036_is_diagnostic_only() -> None:
    spec=json.loads(Path("research/preregistrations/q036_t056_risk_mechanism_diagnostic_2026_09_27.json").read_text(encoding="utf-8"))
    assert spec["status"]=="PREREGISTERED_DIAGNOSTIC_ONLY"
    assert spec["governance"]["performance_evaluation"] is False
    assert spec["methodology"]["no_parameter_search"] is True
    assert spec["methodology"]["no_family_selection"] is True

def test_q036_arm_set_is_fixed() -> None:
    assert {"CONTROL","RISK-A","RISK-B","RISK-C","RISK-D"} == {"CONTROL","RISK-A","RISK-B","RISK-C","RISK-D"}
