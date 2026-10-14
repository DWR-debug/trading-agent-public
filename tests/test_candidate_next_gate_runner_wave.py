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



def test_priority_wave_uses_hosted_windows_python_not_self_hosted_bootstrap():
    workflow = (ROOT / ".github" / "workflows" / "candidate-next-gate-runner-wave.yml").read_text(encoding="utf-8")
    windows_jobs = workflow.split("  q104_r3_date_change_capture:", 1)[1].split("  q104_cross_vintage_aggregate:", 1)[0]
    assert windows_jobs.count("runs-on: windows-latest") == 3
    assert windows_jobs.count("uses: actions/setup-python@v6") == 3
    assert windows_jobs.count('python-version: "3.13.15"') == 3
    assert "runs-on: [self-hosted, trading-agent-research" not in windows_jobs
    assert "name: Bootstrap pinned Python" not in windows_jobs
    assert "python -m pytest" in windows_jobs


def test_candidate_wave_q221_audit_uses_the_frozen_failure_audit_request():
    workflow = (ROOT / ".github" / "workflows" / "candidate-next-gate-runner-wave.yml").read_text(encoding="utf-8")
    assert "--request research/run_requests/q221_transaction_parent_uei_failure_audit.trigger" in workflow
    assert "--request research/run_requests/q221_transaction_parent_uei_probe.trigger" not in workflow
