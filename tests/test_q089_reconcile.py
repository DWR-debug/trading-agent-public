from __future__ import annotations

import json
from pathlib import Path

from automation import q089_reconcile

def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

def _fixture(tmp_path: Path) -> None:
    root = tmp_path
    result = {
        "trial_id": q089_reconcile.TRIAL_ID, "status": "COMPLETED",
        "performance_evaluation": True, "oos_evaluation": True, "holdout_evaluation": True,
        "selection_used": False, "holdout_used_for_selection": False,
        "parameter_search": False, "threshold_search": False, "asset_search": False,
        "horizon_search": False, "variant_search": False, "family_ranking": False,
        "governance": {"performance_trial_authorized": True, "promotion_decision": False, "automatic_promotion": False},
        "safety": q089_reconcile.SAFETY,
        "research_periods": 2798, "holdout_periods": 700, "symbols": ["A", "B"],
        "requested_candles": 5000, "target_common_candles": 3500,
        "coverage_prerequisite": {"result_fingerprint": "cov"},
        "pit_prerequisite": {"result_fingerprint": "pit"},
        "input_bundle_prerequisite": {"trial_id": q089_reconcile.INPUT_ID, "bundle_fingerprint": "bundle"},
        "arms": {"C7_LOW_MAX_21": {"all_gates_passed": False}},
        "report_fingerprint": "report-fp",
    }
    _write(root / q089_reconcile.RESULT_PATH, result)
    _write(root / q089_reconcile.COVERAGE_PATH, {"trial_id": q089_reconcile.COVERAGE_ID, "status": "COVERAGE_PASSED", "result_fingerprint": "cov"})
    _write(root / q089_reconcile.PIT_PATH, {"trial_id": q089_reconcile.PIT_ID, "status": "PIT_PASSED", "result_fingerprint": "pit"})
    _write(root / q089_reconcile.PREREG_PATH, {"data_contract": {"input_bundle_fingerprint": "bundle"}})
    _write(root / q089_reconcile.AUTH_PATH, {"authorized": True, "performance_execution_authorized": True, "one_shot": True, "authorization_contract_version": 2, "trial_id": q089_reconcile.TRIAL_ID})
    _write(root / q089_reconcile.REGISTRY_PATH, {"active_trials": [{"code": "089", "trial_id": q089_reconcile.TRIAL_ID, "performance_authorization_allowed": True}]})
    _write(root / q089_reconcile.LEDGER_PATH, {"trials": []})

def test_reconcile_consumes_q089_authorization(tmp_path: Path) -> None:
    _fixture(tmp_path)
    status = q089_reconcile.reconcile(tmp_path, "12345")
    assert status == "performance_completed_no_arm_passed_all_13_gates"
    registry = json.loads((tmp_path / q089_reconcile.REGISTRY_PATH).read_text())
    assert registry["active_trials"][0]["performance_authorization_allowed"] is False
    ledger = json.loads((tmp_path / q089_reconcile.LEDGER_PATH).read_text())
    assert ledger["trials"][0]["trial_id"] == q089_reconcile.TRIAL_ID
    retired = json.loads((tmp_path / q089_reconcile.RETIRED_AUTH_PATH).read_text())
    assert retired["entries"][0]["trial_id"] == q089_reconcile.TRIAL_ID

def test_reconcile_refuses_duplicate_trial(tmp_path: Path) -> None:
    _fixture(tmp_path)
    first = q089_reconcile.reconcile(tmp_path, "1")
    assert first
    try:
        q089_reconcile.reconcile(tmp_path, "2")
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("duplicate Q089 reconciliation was accepted")
