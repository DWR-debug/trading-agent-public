from pathlib import Path

from automation.project_integrity_check import ACTIVE_WORKFLOWS, ROOT
from automation.q221_pre_event_identity_bridge_pilot import parse_key_value_request


WORKFLOW_NAME = "q221-pre-event-identity-bridge-recovery.yml"
WORKFLOW = ROOT / ".github" / "workflows" / WORKFLOW_NAME
REQUEST = ROOT / "research" / "run_requests" / "q221_pre_event_identity_bridge_recovery_38760595610.trigger"


def test_recovery_workflow_is_registered_and_triggered_only_by_frozen_recovery_request():
    assert WORKFLOW_NAME in ACTIVE_WORKFLOWS
    workflow = WORKFLOW.read_text(encoding="utf-8")
    trigger = workflow.split("\npermissions:", 1)[0]
    assert 'paths:\n      - "research/run_requests/q221_pre_event_identity_bridge_recovery_38760595610.trigger"' in trigger
    assert "workflow_dispatch:" not in trigger
    assert "schedule:" not in trigger
    assert REQUEST.is_file()


def test_recovery_uses_only_pinned_existing_capture_and_parent_artifacts():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "38760595610" in workflow
    assert "11985846368" in workflow
    assert "fce7dee0fe123d4564c188bda60d2e8b00a7f1083fb9cc4971e6ceeaeeaec643" in workflow
    assert "q221-pre-event-identity-capture-38760595610-1" in workflow
    assert "q221-current-parent-identity-map-38305074104-1" in workflow
    assert "--mode verify" in workflow
    assert "--mode publish" in workflow
    assert "--mode capture" not in workflow
    assert "network_requests_made" in workflow
    assert "network_requests_attempted" in workflow


def test_recovery_request_exactly_pins_one_existing_capture_and_keeps_all_gates_closed():
    request = parse_key_value_request(REQUEST)
    assert request == {
        "RUN_Q221_PRE_EVENT_IDENTITY_BRIDGE_RECOVERY": "true",
        "SOURCE_OF_TRUTH": "DWR-debug/trading-agent-public",
        "CAPTURE_RUN_ID": "38760595610",
        "CAPTURE_HEAD_SHA": "737dfd64fbfb19b2737fc0cbac01fde5aecc58b0",
        "CAPTURE_ARTIFACT_ID": "11985846368",
        "CAPTURE_ARTIFACT_NAME": "q221-pre-event-identity-capture-38760595610-1",
        "CAPTURE_ARTIFACT_SHA256": "fce7dee0fe123d4564c188bda60d2e8b00a7f1083fb9cc4971e6ceeaeeaec643",
        "SOURCE_REQUESTS_ALREADY_COMPLETED": "true",
        "NO_SOURCE_RETRIES": "true",
        "OFFLINE_REPRODUCTION_ONLY": "true",
        "PAPER_ONLY": "true",
        "LIVE_TRADING_ENABLED": "false",
        "ORDERS_ENABLED": "false",
        "AUTOMATIC_PROMOTION": "false",
        "PERFORMANCE": "false",
        "HOLDOUT_SELECTION": "false",
        "RANKING": "false",
        "TUNING": "false",
        "PROMOTION": "false",
        "LIVE_EXECUTION": "false",
    }
