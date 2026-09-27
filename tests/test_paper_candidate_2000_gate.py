import json

import pytest

from automation.paper_candidate_2000_gate import (
    Paper2000GateError,
    REQUIRED_CAPITAL_EUR,
    validate_manifest,
)


def _evidence_payload(status="VALIDATED_PASS"):
    return {
        "trial_id": "T-CI-2000",
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


def _write_fixture(tmp_path, monkeypatch, status="VALIDATED_PASS", capital=2000.0):
    monkeypatch.chdir(tmp_path)
    evidence = tmp_path / "research" / "evidence.json"
    returns = tmp_path / "research" / "returns.json"
    manifest = tmp_path / "research" / "paper_candidates_2000" / "manifest.json"
    evidence.parent.mkdir(parents=True)
    returns.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True)
    evidence.write_text(json.dumps(_evidence_payload(status)), encoding="utf-8")
    returns.write_text(
        json.dumps(
            {
                "strategy_id": "ci-fixed-pass-strategy",
                "daily_returns": [0.001] * 30,
                "net_of_costs": True,
                "source": "synthetic-ci",
            }
        ),
        encoding="utf-8",
    )
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "frozen": True,
                "candidate_id": "ci-candidate-2000",
                "evidence_path": "research/evidence.json",
                "returns_path": "research/returns.json",
                "initial_capital_eur": capital,
                "auto_select": False,
                "comparison_mode": False,
                "orders_enabled": False,
            }
        ),
        encoding="utf-8",
    )
    return "research/paper_candidates_2000/manifest.json"


def test_valid_2000_manifest(tmp_path, monkeypatch):
    result = validate_manifest(_write_fixture(tmp_path, monkeypatch))
    assert result["eligible"] is True
    assert result["initial_capital_eur"] == REQUIRED_CAPITAL_EUR
    assert result["capital_semantics"] == "hypothetical_reference_only"


def test_noneligible_evidence_is_fail_closed(tmp_path, monkeypatch):
    with pytest.raises(Paper2000GateError):
        validate_manifest(_write_fixture(tmp_path, monkeypatch, status="BLOCKED"))


def test_wrong_capital_is_fail_closed(tmp_path, monkeypatch):
    with pytest.raises(Paper2000GateError):
        validate_manifest(_write_fixture(tmp_path, monkeypatch, capital=500.0))


def test_holdout_selection_is_fail_closed(tmp_path, monkeypatch):
    manifest = _write_fixture(tmp_path, monkeypatch)
    evidence = tmp_path / "research" / "evidence.json"
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload["holdout_used_for_selection"] = True
    evidence.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(Paper2000GateError, match="(?i)holdout"):
        validate_manifest(manifest)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("paper_only", False),
        ("live_trading_enabled", True),
        ("orders_enabled", True),
    ],
)
def test_unsafe_evidence_is_fail_closed(tmp_path, monkeypatch, field, value):
    manifest = _write_fixture(tmp_path, monkeypatch)
    evidence = tmp_path / "research" / "evidence.json"
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload[field] = value
    evidence.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(Paper2000GateError, match="(?i)safety"):
        validate_manifest(manifest)


def test_evidence_path_outside_checkout_is_fail_closed(tmp_path, monkeypatch):
    manifest = _write_fixture(tmp_path, monkeypatch)
    payload = json.loads((tmp_path / manifest).read_text(encoding="utf-8"))
    payload["evidence_path"] = "../../outside-evidence.json"
    (tmp_path / manifest).write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(Paper2000GateError, match="repository"):
        validate_manifest(manifest)


def test_evidence_symlink_outside_checkout_is_fail_closed(tmp_path, monkeypatch):
    manifest = _write_fixture(tmp_path, monkeypatch)
    outside_evidence = tmp_path.parent / "outside-evidence.json"
    outside_evidence.write_text(json.dumps(_evidence_payload()), encoding="utf-8")
    (tmp_path / "research" / "evidence-link.json").symlink_to(outside_evidence)
    payload = json.loads((tmp_path / manifest).read_text(encoding="utf-8"))
    payload["evidence_path"] = "research/evidence-link.json"
    (tmp_path / manifest).write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(Paper2000GateError, match="repository"):
        validate_manifest(manifest)
