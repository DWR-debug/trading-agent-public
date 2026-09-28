import json
from pathlib import Path

from automation.q068_reconcile import TRIAL_ID, reconcile


def _result():
    return {
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "performance_evaluation": True,
        "oos_evaluation": True,
        "holdout_evaluation": True,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "requested_candles": 4000,
        "target_common_candles": 3500,
        "research_periods": 2798,
        "holdout_periods": 700,
        "symbols": ["ETR", "PPL", "WEC", "FE", "D", "EXR", "PSA", "O"],
        "coverage_prerequisite": {"trial_id": "T-2026-09-28-068-COVERAGE", "result_fingerprint": "c"},
        "pit_prerequisite": {"trial_id": "T-2026-09-28-068-PIT", "result_fingerprint": "p"},
        "report_fingerprint": "report",
        "arms": {
            "CONTROL_6SLEEVE_ENSEMBLE": {"all_gates_passed": False, "gates_passed": 9, "gates_total": 13},
            "E1_ALPHA_COMMON_MODE_THROTTLE": {"all_gates_passed": False, "gates_passed": 10, "gates_total": 13},
            "E2_TURNOVER_HYSTERESIS": {"all_gates_passed": False, "gates_passed": 9, "gates_total": 13},
        },
        "governance": {"promotion_decision": False, "automatic_promotion": False},
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def test_reconcile_appends_exactly_one_non_promoting_entry(tmp_path):
    (tmp_path / "research" / "evidence").mkdir(parents=True)
    (tmp_path / "research" / "evidence" / "q068_performance_result.json").write_text(
        json.dumps(_result()), encoding="utf-8"
    )
    ledger = {"generated_at": "old", "trials": []}
    ledger_path = tmp_path / "research" / "evidence" / "trial_ledger.json"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

    status = reconcile(tmp_path)
    updated = json.loads(ledger_path.read_text(encoding="utf-8"))

    assert status == "performance_completed_no_arm_passed_all_gates"
    assert len(updated["trials"]) == 1
    entry = updated["trials"][0]
    assert entry["trial_id"] == TRIAL_ID
    assert entry["selection"]["selected"] is False
    assert entry["outcome"]["promotion"] is False
    assert entry["safety"]["live_trading_enabled"] is False


def test_reconcile_refuses_duplicate_entry(tmp_path):
    (tmp_path / "research" / "evidence").mkdir(parents=True)
    result_path = tmp_path / "research" / "evidence" / "q068_performance_result.json"
    result_path.write_text(json.dumps(_result()), encoding="utf-8")
    ledger_path = tmp_path / "research" / "evidence" / "trial_ledger.json"
    ledger_path.write_text(
        json.dumps({"trials": [{"trial_id": TRIAL_ID}]}),
        encoding="utf-8",
    )
    try:
        reconcile(tmp_path)
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("duplicate Q068 ledger entry was accepted")
