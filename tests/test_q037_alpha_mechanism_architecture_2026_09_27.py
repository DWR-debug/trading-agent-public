from __future__ import annotations

import json
from pathlib import Path


def test_q037_is_design_only() -> None:
    spec=json.loads(Path("research/preregistrations/q037_alpha_mechanism_architecture_2026_09_27.json").read_text(encoding="utf-8"))
    assert spec["status"] == "PREREGISTERED_DESIGN_ONLY"
    assert spec["protocol"]["family_ranking"] is False
    assert spec["protocol"]["family_selection"] is False
    assert spec["protocol"]["parameter_search"] is False
    assert spec["protocol"]["new_performance_execution"] is False
    assert spec["protocol"]["fresh_symbol_disjoint_validation_required"] is True


def test_q037_future_performance_preserves_existing_contract() -> None:
    spec=json.loads(Path("research/preregistrations/q037_alpha_mechanism_architecture_2026_09_27.json").read_text(encoding="utf-8"))
    contract=spec["future_performance_contract"]
    assert contract["target_common_candles"] == 3500
    assert contract["requested_candles"] == 4000
    assert contract["unchanged_13_gate_contract"] is True
    assert contract["cost_stress_required"] is True
    assert contract["rolling_required"] is True
    assert contract["oos_to_is_required"] is True


def test_q037_safety_authorization_is_non_performance() -> None:
    auth=json.loads(Path("research/authorizations/q037_alpha_mechanism_architecture_2026_09_27.json").read_text(encoding="utf-8"))
    assert auth["authorized"] is True
    assert auth["execution_scope"] == "DESIGN_ONLY"
    assert auth["performance_execution_authorized"] is False
    assert auth["data_acquisition_authorized"] is False
    assert auth["deterministic_performance_compute_authorized"] is False
    assert auth["paid_usage"] is False
