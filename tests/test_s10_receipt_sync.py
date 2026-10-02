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


def test_s10_receipt_sync_rejects_failed_workflow_even_with_acceptance(tmp_path):
    _write(tmp_path / "provenance_receipt.json", {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "scientific_evidence": False,
        "performance_authorization": False,
    })
    _write(tmp_path / "s10_acceptance_receipt.json", {"status": "S10_UTILITY_ACCEPTED"})
    _write(tmp_path / "evidence_critic.json", {"status": "BENCHMARK_COMPLETED"})
    out = build_status(
        tmp_path,
        workflow_run_id="124",
        workflow_conclusion="failure",
        source_commit="def",
        artifact_id=None,
        artifact_digest=None,
    )
    assert out["eligible"] is False
    assert out["status"] == "S10_RESULT_AVAILABLE"


def test_s10_receipt_sync_merge_keeps_newer_existing_status():
    from automation.s10_receipt_sync import merge_status
    old = {"workflow_run_updated_at": "2026-10-02T10:00:00Z", "workflow_run_id": "200"}
    new = {"workflow_run_updated_at": "2026-10-02T09:59:00Z", "workflow_run_id": "201"}
    assert merge_status(old, new) == old


def test_s10_workflows_are_master_canonical_only():
    from pathlib import Path
    worker = Path(".github/workflows/s10-phone-worker.yml").read_text(encoding="utf-8")
    sync = Path(".github/workflows/s10-receipt-sync.yml").read_text(encoding="utf-8")
    assert "    branches:\n      - master" in worker
    assert "github.event.workflow_run.head_branch == 'master'" in sync


def test_s10_workflow_pins_seed_in_environment():
    from pathlib import Path
    worker = Path(".github/workflows/s10-phone-worker.yml").read_text(encoding="utf-8")
    assert 'S10_SEED: "271828"' in worker
    assert '"s10_seed": os.environ.get("S10_SEED")' in worker
