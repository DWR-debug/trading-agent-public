import json
from pathlib import Path

from automation.research_governance_audit import audit


def _write(root: Path, relative: str, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _safety() -> dict:
    return {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def _receipt(trial_id: str, status: str, fp_key: str, fp: str, **extra: str) -> dict:
    return {
        "schema_version": "1.0",
        "trial_id": trial_id,
        "status": status,
        fp_key: fp,
        **extra,
        "safety": _safety(),
    }


def _registry(root: Path) -> None:
    _write(root, "research/governance/active_research_registry.json", {
        "schema_version": 1,
        "policy": {
            "only_listed_performance_trials_may_be_authorized": True,
        },
        "active_trials": [{
            "code": "089",
            "trial_id": "T-2026-09-28-089-PERFORMANCE",
            "class": "fresh_validation",
            "state": "PREREGISTERED_WAITING_PREFLIGHT",
            "performance_authorization_allowed": False,
            "preregistration_path": "research/preregistrations/q089_performance_2026_09_28.json",
        }],
    })


def _prereg(root: Path, *, foreign: bool = False) -> None:
    _registry(root)
    _write(root, "research/evidence/coverage.json", _receipt(
        "T-2026-09-28-089-COVERAGE", "COVERAGE_PASSED",
        "result_fingerprint", "coverage-fp", snapshot_fingerprint="snapshot-fp",
    ))
    _write(root, "research/evidence/pit.json", _receipt(
        "T-2026-09-28-089-PIT", "PIT_PASSED",
        "result_fingerprint", "pit-fp",
    ))
    _write(root, "research/evidence/input.json", _receipt(
        "T-2026-09-28-089-INPUT-FREEZE", "INPUT_BUNDLE_FROZEN",
        "bundle_fingerprint", "bundle-fp",
    ))

    data_contract = {
        "coverage_trial_id": "T-2026-09-28-089-COVERAGE",
        "coverage_result_fingerprint": "coverage-fp",
        "snapshot_fingerprint": "snapshot-fp",
        "pit_trial_id": "T-2026-09-28-089-PIT",
        "pit_result_fingerprint": "pit-fp",
        "input_bundle_trial_id": "T-2026-09-28-089-INPUT-FREEZE",
        "input_bundle_fingerprint": "bundle-fp",
    }
    identity = {
        "trial_id": "T-2026-09-28-089-PERFORMANCE",
        "expected_trial_code": "089",
        "mode": "fresh_trial",
        "reused_source_trials": [],
        "required_receipts": [
            {
                "role": "coverage",
                "path": "research/evidence/coverage.json",
                "trial_id": "T-2026-09-28-089-COVERAGE",
                "fingerprint_key": "result_fingerprint",
                "expected_data_contract_key": "coverage_result_fingerprint",
            },
            {
                "role": "pit",
                "path": "research/evidence/pit.json",
                "trial_id": "T-2026-09-28-089-PIT",
                "fingerprint_key": "result_fingerprint",
                "expected_data_contract_key": "pit_result_fingerprint",
            },
            {
                "role": "input",
                "path": "research/evidence/input.json",
                "trial_id": "T-2026-09-28-089-INPUT-FREEZE",
                "fingerprint_key": "bundle_fingerprint",
                "expected_data_contract_key": "input_bundle_fingerprint",
            },
        ],
    }

    if foreign:
        data_contract["coverage_trial_id"] = "T-2026-09-28-079-COVERAGE"
        data_contract["coverage_result_fingerprint"] = "old-coverage"
        identity["mode"] = "immutable_reuse"
        identity["reused_source_trials"] = ["T-2026-09-28-079-COVERAGE"]
        data_contract["coverage_trial_id"] = "T-2026-09-28-079-COVERAGE"
        identity["required_receipts"][0]["trial_id"] = "T-2026-09-28-079-COVERAGE"
        _write(root, "research/evidence/coverage.json", _receipt(
            "T-2026-09-28-079-COVERAGE", "COVERAGE_PASSED",
            "result_fingerprint", "old-coverage", snapshot_fingerprint="snapshot-fp",
        ))

    if foreign:
        payload_prior = "T-2026-09-28-079-PERFORMANCE"
    else:
        payload_prior = None
    payload = {
        "schema_version": "1.0",
        "trial_id": "T-2026-09-28-089-PERFORMANCE",
        "status": "PREREGISTERED_PERFORMANCE",
        "governance_contract_version": 2,
        "identity_contract": identity,
        "data_contract": data_contract,
        "prior_trial_id": payload_prior,
        "safety": _safety(),
    }
    _write(root, "research/preregistrations/q089_performance_2026_09_28.json", payload)


def test_clean_fresh_trial_passes(tmp_path):
    _prereg(tmp_path)
    result = audit(tmp_path)
    assert result["status"] == "PASS"
    assert result["error_count"] == 0


def test_explicit_immutable_reuse_passes(tmp_path):
    _prereg(tmp_path, foreign=True)
    result = audit(tmp_path)
    assert result["status"] == "PASS"


def test_silent_cross_trial_reference_is_blocked(tmp_path):
    _prereg(tmp_path)
    path = tmp_path / "research/preregistrations/q089_performance_2026_09_28.json"
    data = json.loads(path.read_text())
    data["data_contract"]["coverage_trial_id"] = "T-2026-09-28-079-COVERAGE"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = audit(tmp_path)
    assert result["status"] == "BLOCKED"
    assert any("foreign prerequisite" in item for item in result["errors"])


def test_receipt_trial_identity_mismatch_is_blocked(tmp_path):
    _prereg(tmp_path)
    path = tmp_path / "research/evidence/pit.json"
    data = json.loads(path.read_text())
    data["trial_id"] = "T-2026-09-28-079-PIT"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = audit(tmp_path)
    assert result["status"] == "BLOCKED"
    assert any("trial_id mismatch" in item for item in result["errors"])

from automation.research_governance_audit import audit


def test_retired_authorizations_are_not_active(tmp_path):
    from pathlib import Path
    import json

    _prereg(tmp_path)
    _write(tmp_path, "research/authorizations/legacy.json", {
        "trial_id": "T-2026-09-27-052",
        "authorized": True,
        "performance_execution_authorized": True,
    })
    _write(tmp_path, "research/governance/retired_authorizations.json", {
        "entries": [{
            "path": "research/authorizations/legacy.json",
            "trial_id": "T-2026-09-27-052",
            "status": "RETIRED_HISTORICAL_AUTHORIZATION",
        }]
    })
    result = audit(tmp_path)
    assert result["status"] == "PASS"


def test_unregistered_authorization_remains_blocked(tmp_path):
    _registry(tmp_path)
    _write(tmp_path, "research/authorizations/legacy.json", {
        "trial_id": "T-2026-09-27-052",
        "authorized": True,
        "performance_execution_authorized": True,
    })
    result = audit(tmp_path)
    assert result["status"] == "BLOCKED"
    assert any("not in active research registry" in item for item in result["errors"])


def test_infrastructure_invalidated_trial_is_not_active(tmp_path):
    _registry(tmp_path)
    registry = json.loads(
        (tmp_path / "research/governance/active_research_registry.json").read_text()
    )
    registry["active_trials"].insert(0, {
        "code": "081R1",
        "trial_id": "T-2026-09-28-081R1-PERFORMANCE",
        "class": "historical_infrastructure_invalidated",
        "state": "HISTORICAL_INFRASTRUCTURE_INVALIDATED",
        "preregistration_path": "research/preregistrations/q081r1_performance_2026_09_28.json",
        "performance_authorization_allowed": False,
    })
    (tmp_path / "research/governance/active_research_registry.json").write_text(
        json.dumps(registry), encoding="utf-8"
    )
    _prereg(tmp_path)
    result = audit(tmp_path)
    assert result["status"] == "PASS"



def test_terminal_historical_preregistration_can_remain_v1(tmp_path):
    _write(tmp_path, "research/governance/active_research_registry.json", {
        "schema_version": 1,
        "policy": {"only_listed_performance_trials_may_be_authorized": True},
        "active_trials": [{
            "code": "094",
            "trial_id": "T-2026-09-29-094",
            "class": "fresh_validation",
            "state": "PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES",
            "performance_authorization_allowed": False,
            "preregistration_path": "research/preregistrations/q094_monthly_rebalance_q091_low_turnover_2026_09_29.json",
        }],
    })
    _write(tmp_path, "research/preregistrations/q094_monthly_rebalance_q091_low_turnover_2026_09_29.json", {
        "schema_version": "1.0",
        "trial_id": "T-2026-09-29-094",
        "status": "PREREGISTERED_PERFORMANCE",
        "safety": _safety(),
    })
    result = audit(tmp_path)
    assert result["status"] == "PASS"
    assert result["error_count"] == 0


def test_superseded_pre_execution_authorization_is_historical(tmp_path):
    _prereg(tmp_path)
    _write(tmp_path, "research/authorizations/legacy.json", {
        "trial_id": "T-2026-09-27-052",
        "authorized": True,
        "performance_execution_authorized": True,
    })
    _write(tmp_path, "research/governance/retired_authorizations.json", {
        "entries": [{
            "path": "research/authorizations/legacy.json",
            "trial_id": "T-2026-09-27-052",
            "status": "SUPERSEDED_PRE_EXECUTION",
        }]
    })
    result = audit(tmp_path)
    assert result["status"] == "PASS"
