from pathlib import Path

from automation.project_integrity_check import ACTIVE_WORKFLOWS, ROOT


def test_candidate_next_gate_wave_workflow_is_registered_in_integrity_inventory():
    workflow_name = "candidate-next-gate-runner-wave.yml"
    assert workflow_name in ACTIVE_WORKFLOWS
    assert (ROOT / ".github" / "workflows" / workflow_name).is_file()


def test_q221_failure_audit_uses_the_actual_frozen_attempt_sequence():
    path = ROOT / "research" / "run_requests" / "q221_transaction_parent_uei_failure_audit.trigger"
    values = dict(
        line.split("=", 1)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )
    assert values["REQUEST_SEQUENCE"] == "2026-10-14T07:50:00Z"
    assert values["SOURCE_RECEIPT_FINGERPRINT"] == "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
    assert values["FREEZE_RECIPIENT_TO_ISSUER_MAPPING"] == "false"
    assert values["LIVE_EXECUTION"] == "false"
