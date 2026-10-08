from __future__ import annotations

import json
from pathlib import Path

import pytest

from automation.q218_independent_replication_authorization_guard import (
    REPLICATION_TRIAL_ID,
    SOURCE_TRIAL_ID,
    sha256_file,
    validate_authorization,
)


def _write_contract(path: Path) -> Path:
    path.write_text(json.dumps({
        "record_type": "q218_independent_replication_contract",
        "replication_trial_id": REPLICATION_TRIAL_ID,
    }), encoding="utf-8")
    return path


def _valid_authorization(contract_path: Path) -> dict:
    return {
        "record_type": "q218_independent_replication_performance_authorization",
        "authorization_id": "AUTH-Q218-REPLICATION-TEST-01",
        "candidate_id": "Q218",
        "source_trial_id": SOURCE_TRIAL_ID,
        "replication_trial_id": REPLICATION_TRIAL_ID,
        "trial_id": REPLICATION_TRIAL_ID,
        "status": "AUTHORIZED",
        "authorized": True,
        "performance_execution_authorized": True,
        "one_shot": True,
        "authorized_at_utc": "2026-10-09T00:00:00Z",
        "replication_contract_sha256": sha256_file(contract_path),
        "authorization_basis": {
            "requested_by_user": True,
            "master_exact_ci_run_id": 123456,
        },
        "selection_used": False,
        "holdout_selection_used": False,
        "parameter_search": False,
        "threshold_search": False,
        "horizon_search": False,
        "asset_search": False,
        "variant_search": False,
        "family_ranking": False,
        "promotion_decision": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def test_q218_replication_authorization_fails_closed_when_missing(tmp_path):
    contract = _write_contract(tmp_path / "contract.json")
    with pytest.raises(RuntimeError, match="authorization is missing"):
        validate_authorization(tmp_path / "missing.json", contract)


def test_q218_replication_authorization_accepts_exact_one_shot(tmp_path):
    contract = _write_contract(tmp_path / "contract.json")
    auth_path = tmp_path / "authorization.json"
    auth_path.write_text(json.dumps(_valid_authorization(contract)), encoding="utf-8")
    assert validate_authorization(auth_path, contract)["trial_id"] == REPLICATION_TRIAL_ID


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("trial_id", SOURCE_TRIAL_ID, "trial_id"),
        ("authorized", False, "authorized"),
        ("performance_execution_authorized", False, "performance_execution_authorized"),
        ("one_shot", False, "one_shot"),
        ("selection_used", True, "prohibited search/selection"),
        ("safety", {"paper_only": False}, "safety boundary"),
    ],
)
def test_q218_replication_authorization_rejects_scope_or_safety_drift(tmp_path, key, value, message):
    contract = _write_contract(tmp_path / "contract.json")
    auth = _valid_authorization(contract)
    auth[key] = value
    auth_path = tmp_path / "authorization.json"
    auth_path.write_text(json.dumps(auth), encoding="utf-8")
    with pytest.raises(RuntimeError, match=message):
        validate_authorization(auth_path, contract)


def test_q218_replication_authorization_rejects_contract_fingerprint_drift(tmp_path):
    contract = _write_contract(tmp_path / "contract.json")
    auth = _valid_authorization(contract)
    auth["replication_contract_sha256"] = "0" * 64
    auth_path = tmp_path / "authorization.json"
    auth_path.write_text(json.dumps(auth), encoding="utf-8")
    with pytest.raises(RuntimeError, match="contract fingerprint"):
        validate_authorization(auth_path, contract)
