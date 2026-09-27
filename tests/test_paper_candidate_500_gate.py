from pathlib import Path
import json
import pytest

from automation.paper_candidate_500_gate import (
    Paper500GateError,
    REQUIRED_CAPITAL_EUR,
    validate_manifest,
)

def _evidence_payload(status="VALIDATED_PASS"):
    return {
        "trial_id": "T-CI-500",
        "strategy_id": "ci-fixed-pass-strategy",
        "status": status,
        "artifact_id": 1,
        "artifact_digest_sha256": "a" * 64,
        "report_fingerprint_sha256": "b" * 64,
        "manifest_fingerprint_sha256": "c" * 64,
        "code_commit_sha": "1234567",
        "research_count": 1000,
        "holdout_count": 300,
        "holdout_used_for_selection": False,
        "gates": [{"name": "synthetic_gate", "passed": True}],
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }

def _write_fixture(tmp_path, status="VALIDATED_PASS", capital=500.0):
    evidence = tmp_path / "evidence.json"
    returns = tmp_path / "returns.json"
    manifest = tmp_path / "manifest.json"
    evidence.write_text(json.dumps(_evidence_payload(status)), encoding="utf-8")
    returns.write_text(json.dumps({
        "strategy_id": "ci-fixed-pass-strategy",
        "daily_returns": [0.001] * 30,
        "net_of_costs": True,
        "source": "synthetic-ci",
    }), encoding="utf-8")
    manifest.write_text(json.dumps({
        "schema_version": 1,
        "frozen": True,
        "candidate_id": "ci-candidate-500",
        "evidence_path": str(evidence),
        "returns_path": str(returns),
        "initial_capital_eur": capital,
        "auto_select": False,
        "comparison_mode": False,
        "orders_enabled": False,
    }), encoding="utf-8")
    return manifest

def test_valid_500_manifest(tmp_path):
    result = validate_manifest(_write_fixture(tmp_path))
    assert result["eligible"] is True
    assert result["initial_capital_eur"] == REQUIRED_CAPITAL_EUR

def test_noneligible_evidence_is_fail_closed(tmp_path):
    with pytest.raises(Paper500GateError):
        validate_manifest(_write_fixture(tmp_path, status="BLOCKED"))

def test_wrong_capital_is_fail_closed(tmp_path):
    with pytest.raises(Paper500GateError):
        validate_manifest(_write_fixture(tmp_path, capital=10.0))
