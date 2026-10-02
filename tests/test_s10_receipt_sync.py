from automation.s10_receipt_sync import build_status


def _write(path, payload):
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")


def test_s10_receipt_sync_accepts_valid_operational_artifact(tmp_path):
    _write(tmp_path / "provenance_receipt.json", {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "runner_name": "S10-TERMUX",
        "runner_arch": "ARM64",
    })
    _write(tmp_path / "s10_acceptance_receipt.json", {
        "status": "S10_UTILITY_ACCEPTED",
        "model": "S10-Qwen",
    })
    _write(tmp_path / "evidence_critic.json", {"status": "BENCHMARK_COMPLETED", "model": "S10-Qwen"})
    out = build_status(tmp_path, workflow_run_id="123", workflow_conclusion="success",
                       source_commit="abc", artifact_id="7", artifact_digest="sha256:x")
    assert out["eligible"] is True
    assert out["status"] == "S10_UTILITY_ACCEPTED"
    assert out["scientific_evidence"] is False
    assert out["performance_authorization"] is False


def test_s10_receipt_sync_rejects_policy_violation(tmp_path):
    _write(tmp_path / "provenance_receipt.json", {
        "paper_only": True,
        "live_trading_enabled": True,
        "orders_enabled": False,
        "automatic_promotion": False,
        "scientific_evidence": False,
        "performance_authorization": False,
    })
    out = build_status(tmp_path, workflow_run_id="123", workflow_conclusion="success",
                       source_commit="abc", artifact_id=None, artifact_digest=None)
    assert out["eligible"] is False
    assert out["status"] == "S10_ARTIFACT_POLICY_INVALID"
