import json
from pathlib import Path

from automation.q091_contract_audit import EXPECTED_GATES, EXPECTED_VARIANTS, audit


def test_q091_contract_audit_accepts_current_master_contract(tmp_path):
    root = Path(".").resolve()
    result = audit(root)
    assert result["status"] == "PASS", result["findings"]
    assert result["performance_authorization_changed"] is False
    assert result["performance_executed"] is False


def test_q091_gate_and_variant_sets_are_frozen():
    assert len(EXPECTED_GATES) == 13
    assert EXPECTED_VARIANTS == {
        "E1_EQUAL_WEIGHT_Q069_5SLEEVE",
        "E2_CROSS_SECTIONAL_RESIDUALIZED_Q069_5SLEEVE",
    }
