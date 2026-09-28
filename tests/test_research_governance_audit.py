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


def _prereg(root: Path, *, foreign: bool = False) -> None:
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

    identity["prior_trial_id"] = "T-2026-09-28-079-PERFORMANCE" if foreign else None
    payload = {
        "schema_version": "1.0",
        "trial_id": "T-2026-09-28-089-PERFORMANCE",
        "status": "PREREGISTERED_PERFORMANCE",
        "governance_contract_version": 2,
        "identity_contract": identity,
        "data_contract": data_contract,
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
