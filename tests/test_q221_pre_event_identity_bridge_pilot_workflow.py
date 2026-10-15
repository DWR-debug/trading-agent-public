from pathlib import Path

from automation.project_integrity_check import ACTIVE_WORKFLOWS, ROOT


WORKFLOW_NAME = "q221-pre-event-identity-bridge-pilot.yml"
WORKFLOW = ROOT / ".github" / "workflows" / WORKFLOW_NAME


def test_q221_pilot_workflow_is_registered_and_triggered_only_by_frozen_request():
    assert WORKFLOW_NAME in ACTIVE_WORKFLOWS
    workflow = WORKFLOW.read_text(encoding="utf-8")
    trigger = workflow.split("\npermissions:", 1)[0]
    assert 'paths:\n      - "research/run_requests/q221_pre_event_identity_bridge_pilot.trigger"' in trigger
    assert "automation/q221_pre_event_identity_bridge_pilot.py" not in trigger
    assert "workflow_dispatch:" not in trigger
    assert "schedule:" not in trigger


def test_q221_pilot_uses_exact_existing_artifact_and_two_architecture_offline_reproduction():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count("q221-current-parent-identity-map-38305074104-1") == 4
    assert workflow.count("run-id: 38305074104") == 3
    assert "ubuntu-24.04-arm" in workflow
    assert "Q221_PRE_EVENT_IDENTITY_BRIDGE_REPRODUCED_OFFLINE" in workflow
    assert "DETERMINISTIC_ANALYSIS_MATCHED" in workflow


def test_q221_pilot_publishes_only_when_source_and_offline_receipt_agree_and_never_maps_issuer():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "needs: [capture, verify]" in workflow
    assert "q221_pre_event_identity_bridge_pilot_latest.json" in workflow
    assert "base-sha latest" in workflow
    assert "historical_first_public_observation_proven" in workflow
    assert "recipient_to_issuer_mapping_frozen" in workflow
    assert "live_trading_enabled" in workflow
    assert "automatic_promotion" in workflow
 
def test_capture_output_heredoc_terminator_is_not_nested_under_shell_if():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    capture = workflow.split(
        "      - name: Capture exact pre-registered public pages once", 1
    )[1].split("\n      - name: Preserve bounded capture and failure receipt", 1)[0]
    assert "\n          PY\n          fi" in capture
    assert "\n            PY\n          fi" not in capture
