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


def test_q091_preregistration_geometry_and_source_contract_are_explicit():
    import json
    from pathlib import Path

    prereg = json.loads(
        Path("research/preregistrations/q091_fixed_portfolio_architecture_2026_09_29.json")
        .read_text(encoding="utf-8")
    )
    assert prereg["requested_candles"] == 5000
    assert prereg["target_common_candles"] == 3500
    assert prereg["research_periods"] == 2798
    assert prereg["holdout_periods"] == 700
    assert {v["id"] for v in prereg["variants"]} == EXPECTED_VARIANTS
    assert all(
        key in prereg["source_contract"]
        for key in (
            "performance_runner_path",
            "performance_runner_sha256",
            "portfolio_architecture_path",
            "portfolio_architecture_sha256",
            "candidate_bank_path",
            "candidate_bank_sha256",
            "cost_contract_path",
            "cost_contract_sha256",
            "settings_path",
            "settings_sha256",
            "input_freeze_path",
            "input_freeze_sha256",
        )
    )
