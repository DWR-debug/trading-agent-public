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


def test_priority_wave_uses_three_self_hosted_windows_and_three_github_ubuntu_slots():
    workflow = (ROOT / ".github" / "workflows" / "candidate-next-gate-runner-wave.yml").read_text(encoding="utf-8")
    windows_jobs = workflow.split("  q104_r3_date_change_capture:", 1)[1].split("  q104_cross_vintage_aggregate:", 1)[0]
    assert windows_jobs.count("runs-on: [self-hosted, trading-agent-research") == 3
    assert windows_jobs.count("name: Bootstrap pinned Python") == 3
    assert "python-3.13.15-nuget-wave-q104" in windows_jobs
    assert "python-3.13.15-nuget-wave-q220" in windows_jobs
    assert "actions/setup-python@v6" not in windows_jobs
    assert "runs-on: windows-latest" not in workflow
    assert workflow.count("runs-on: ubuntu-24.04") == 3
    assert workflow.count("uses: actions/setup-python@v6") == 3
    assert workflow.count('python-version: "3.13.15"') == 3
    assert "q104-cross-vintage-ubuntu-arm-" in workflow
    assert "shell: pwsh" not in workflow


def test_candidate_wave_q221_audit_uses_the_frozen_failure_audit_request():
    workflow = (ROOT / ".github" / "workflows" / "candidate-next-gate-runner-wave.yml").read_text(encoding="utf-8")
    assert "--request research/run_requests/q221_transaction_parent_uei_failure_audit.trigger" in workflow
    assert "--request research/run_requests/q221_transaction_parent_uei_probe.trigger" not in workflow


def test_legacy_wave_requires_explicit_request_marker_and_does_not_trigger_on_code_edits():
    workflow = (ROOT / ".github" / "workflows" / "candidate-next-gate-runner-wave.yml").read_text(encoding="utf-8")
    trigger = workflow.split("\npermissions:", 1)[0]
    assert 'paths:\n      - "research/run_requests/candidate_next_gate_runner_wave.trigger"' in trigger
    assert workflow.count("research/run_requests/candidate_next_gate_runner_wave.trigger") == 1
    assert "workflow_dispatch:" not in workflow
    assert "automation/q220_hash_provenance_diagnostic.py" not in trigger
    assert "tests/test_q220_hash_provenance_diagnostic.py" not in trigger


def test_legacy_q220_analysis_and_arm64_reproduction_use_exact_sensitivity_receipt():
    workflow = (ROOT / ".github" / "workflows" / "candidate-next-gate-runner-wave.yml").read_text(encoding="utf-8")
    assert workflow.count("q220-http-representation-sensitivity-38590133217-1") == 2
    assert workflow.count("--sensitivity-artifact q220-sensitivity-source") == 2
    assert "run-id: 38590133217" in workflow
