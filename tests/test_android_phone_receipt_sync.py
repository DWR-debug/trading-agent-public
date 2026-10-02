from automation.android_phone_receipt_sync import build_status


def _write(path, payload):
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")


def test_preserves_prior_acceptance_on_utility_run(tmp_path):
    _write(tmp_path / "utility_task.json", {"status": "S10_UTILITY_REVIEW_COMPLETED", "task_id": "U1"})
    existing = {
        "status": "ANDROID_PHONE_UTILITY_ACCEPTED",
        "eligible": True,
        "acceptance_contract_version": "2026-10-02-R3",
        "acceptance_receipt_sha256": "r1",
        "runner_name": "PHONE-01",
        "model": "Qwen",
        "endpoint": "http://127.0.0.1:8765",
    }
    out = build_status(
        tmp_path, resource_id="SAMSUNG-PHONE-01", workflow_run_id="2",
        workflow_conclusion="success", source_commit="abc",
        workflow_run_updated_at="2026-10-02T12:00:00Z", existing=existing,
    )
    assert out["status"] == "ANDROID_PHONE_UTILITY_ACCEPTED"
    assert out["eligible"] is True
    assert out["acceptance_preserved"] is True
    assert out["acceptance_receipt_sha256"] == "r1"
    assert out["utility_task_id"] == "U1"


def test_explicit_acceptance_failure_reverses_eligibility(tmp_path):
    _write(tmp_path / "android_phone_acceptance_receipt.json", {
        "status": "ANDROID_PHONE_UTILITY_NOT_ACCEPTED",
        "acceptance_contract_version": "2026-10-02-R3",
    })
    existing = {
        "status": "ANDROID_PHONE_UTILITY_ACCEPTED",
        "eligible": True,
        "acceptance_contract_version": "2026-10-02-R3",
    }
    out = build_status(
        tmp_path, resource_id="SAMSUNG-PHONE-01", workflow_run_id="3",
        workflow_conclusion="success", source_commit="def",
        workflow_run_updated_at="2026-10-02T13:00:00Z", existing=existing,
    )
    assert out["eligible"] is False
    assert out["status"] == "ANDROID_PHONE_UTILITY_NOT_ACCEPTED"


def test_acceptance_receipt_is_accepted(tmp_path):
    _write(tmp_path / "android_phone_acceptance_receipt.json", {
        "status": "ANDROID_PHONE_UTILITY_ACCEPTED",
        "acceptance_contract_version": "2026-10-02-R3",
        "runner_name": "PHONE-01",
        "model": "Qwen",
        "endpoint": "http://127.0.0.1:8765",
        "result_sha256": "r2",
    })
    out = build_status(
        tmp_path, resource_id="SAMSUNG-PHONE-01", workflow_run_id="4",
        workflow_conclusion="success", source_commit="ghi",
        workflow_run_updated_at="2026-10-02T14:00:00Z", existing=None,
    )
    assert out["eligible"] is True
    assert out["status"] == "ANDROID_PHONE_UTILITY_ACCEPTED"
    assert out["acceptance_preserved"] is False
