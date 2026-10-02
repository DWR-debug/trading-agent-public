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
        "acceptance_contract_version": "2026-10-02-R3",
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
    _write(tmp_path / "s10_acceptance_receipt.json", {
        "status": "S10_UTILITY_ACCEPTED",
        "acceptance_contract_version": "2026-10-02-R3",
    })
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


def test_s10_receipt_sync_preserves_prior_acceptance_for_utility_only_run():
    from automation.s10_receipt_sync import merge_status
    existing = {
        "workflow_run_id": "100",
        "workflow_run_updated_at": "2026-10-02T10:00:00Z",
        "status": "S10_UTILITY_ACCEPTED",
        "eligible": True,
        "receipt_status": "S10_UTILITY_ACCEPTED",
        "acceptance_contract_version": "2026-10-02-R3",
        "acceptance_receipt_sha256": "receipt-hash",
        "model": "S10-Qwen",
    }
    incoming = {
        "workflow_run_id": "101",
        "workflow_run_updated_at": "2026-10-02T11:00:00Z",
        "status": "S10_RESULT_AVAILABLE",
        "eligible": False,
        "receipt_status": "S10_UTILITY_REVIEW_COMPLETED",
        "acceptance_contract_version": None,
        "model": "S10-Qwen",
        "acceptance_preserved": False,
    }
    merged = merge_status(existing, incoming)
    assert merged["status"] == "S10_UTILITY_ACCEPTED"
    assert merged["eligible"] is True
    assert merged["acceptance_receipt_sha256"] == "receipt-hash"
    assert merged["acceptance_preserved"] is True
    assert merged["acceptance_preserved_from_workflow_run_id"] == "100"


def test_s10_receipt_sync_allows_explicit_acceptance_failure_to_revoke():
    from automation.s10_receipt_sync import merge_status
    existing = {
        "workflow_run_id": "100",
        "workflow_run_updated_at": "2026-10-02T10:00:00Z",
        "status": "S10_UTILITY_ACCEPTED",
        "eligible": True,
        "receipt_status": "S10_UTILITY_ACCEPTED",
        "acceptance_contract_version": "2026-10-02-R3",
    }
    incoming = {
        "workflow_run_id": "102",
        "workflow_run_updated_at": "2026-10-02T11:00:00Z",
        "status": "S10_UTILITY_NOT_ACCEPTED",
        "eligible": False,
        "receipt_status": "S10_UTILITY_NOT_ACCEPTED",
        "acceptance_contract_version": "2026-10-02-R3",
    }
    merged = merge_status(existing, incoming)
    assert merged["eligible"] is False
    assert merged["receipt_status"] == "S10_UTILITY_NOT_ACCEPTED"


def test_acceptance_does_not_claim_current_online_presence(tmp_path):
    from automation.s10_receipt_sync import build_status

    root = tmp_path / "artifact"
    root.mkdir()
    (root / "provenance_receipt.json").write_text(
        '{"paper_only":true,"live_trading_enabled":false,"orders_enabled":false,"automatic_promotion":false,"scientific_evidence":false,"performance_authorization":false}',
        encoding="utf-8",
    )
    (root / "s10_acceptance_receipt.json").write_text(
        '{"status":"S10_UTILITY_ACCEPTED","acceptance_contract_version":"2026-10-02-R3"}',
        encoding="utf-8",
    )
    (root / "evidence_critic.json").write_text('{"status":"S10_UTILITY_REVIEW_COMPLETED"}', encoding="utf-8")
    status = build_status(
        root,
        workflow_run_id="1",
        workflow_conclusion="success",
        source_commit="abc",
        artifact_id=None,
        artifact_digest=None,
        workflow_run_updated_at="2026-10-02T20:39:20Z",
    )
    assert status["eligible"] is True
    assert status["receipt_eligible"] is True
    assert status["current_online"] is None
    assert status["current_online_verification"] == "NOT_PERFORMED"
    assert status["eligibility_basis"] == "completed_workflow_acceptance_receipt"
