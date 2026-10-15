from pathlib import Path

from automation.project_integrity_check import ACTIVE_WORKFLOWS, ROOT
from automation.q104_i19_residual_policy_applicability_review_r7 import (
    R7_SOURCE_CAPTURE_HEAD_SHA,
    R7_SOURCE_CAPTURE_RECEIPT_FP,
    R7_SOURCE_CAPTURE_RUN_ID,
    R7_SOURCE_CAPTURE_SEQUENCE,
    R7_EXPECTED_INDEX_404_ACCESSIONS,
)


WORKFLOW_NAME = "q104-i19-residual-policy-applicability-recovery.yml"
WORKFLOW = ROOT / ".github" / "workflows" / WORKFLOW_NAME
REQUEST = ROOT / "research/run_requests/q104_i19_residual_policy_applicability_recovery_38762761429.trigger"
CAPTURE_ARTIFACT_ID = 11986177930
CAPTURE_ARTIFACT_NAME = "q104-i19-residual-policy-r7-capture-38762761429-1"
CAPTURE_ARTIFACT_SHA256 = "8dc9f6645389e1ba1513449a61ef9b20cb72243c3279b0592d36c49c5223304c"


def read_marker(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        key, value = line.split("=", 1)
        assert key not in values
        values[key] = value
    return values


def test_recovery_is_registered_and_has_one_explicit_request_path():
    assert WORKFLOW_NAME in ACTIVE_WORKFLOWS
    workflow = WORKFLOW.read_text(encoding="utf-8")
    trigger = workflow.split("\npermissions:", 1)[0]
    assert 'paths:\n      - "research/run_requests/q104_i19_residual_policy_applicability_recovery_38762761429.trigger"' in trigger
    assert "workflow_dispatch:" not in trigger
    assert "schedule:" not in trigger
    assert REQUEST.is_file()


def test_recovery_request_is_bound_to_the_exact_failed_capture_artifact():
    request = read_marker(REQUEST)
    assert request == {
        "RUN_Q104_I19_RESIDUAL_POLICY_APPLICABILITY_RECOVERY": "true",
        "SOURCE_OF_TRUTH": "DWR-debug/trading-agent-public",
        "SOURCE_CAPTURE_RUN_ID": str(R7_SOURCE_CAPTURE_RUN_ID),
        "SOURCE_CAPTURE_HEAD_SHA": R7_SOURCE_CAPTURE_HEAD_SHA,
        "SOURCE_CAPTURE_ARTIFACT_ID": str(CAPTURE_ARTIFACT_ID),
        "SOURCE_CAPTURE_ARTIFACT_NAME": CAPTURE_ARTIFACT_NAME,
        "SOURCE_CAPTURE_ARTIFACT_SHA256": CAPTURE_ARTIFACT_SHA256,
        "SOURCE_CAPTURE_RECEIPT_FINGERPRINT": R7_SOURCE_CAPTURE_RECEIPT_FP,
        "SOURCE_CAPTURE_REQUEST_SEQUENCE": R7_SOURCE_CAPTURE_SEQUENCE,
        "EXPECTED_INDEX_HEADER_404_COUNT": "4",
        "EXPECTED_INDEX_HEADER_404_ACCESSIONS": "|".join(sorted(R7_EXPECTED_INDEX_404_ACCESSIONS)),
        "OFFLINE_REPLAY_ONLY": "true",
        "NO_SEC_SOURCE_REQUESTS": "true",
        "NO_SOURCE_RETRIES": "true",
        "NO_DAILY_FEED_REQUESTS": "true",
        "NO_PRIMARY_DOCUMENT_REQUESTS": "true",
        "NO_CENSUS_RESTART": "true",
        "NO_SOURCE_RECEIPT_REWRITES": "true",
        "FIELD_PRECEDENCE_APPLIED": "false",
        "PRODUCTION_JOIN_CHANGED": "false",
        "ACCEPTANCE_TIME_GATE_CLEARED": "false",
        "HISTORICAL_ARCHIVE_GATE_CLEARED": "false",
        "PERFORMANCE": "false",
        "HOLDOUT_SELECTION": "false",
        "RANKING": "false",
        "TUNING": "false",
        "PROMOTION": "false",
        "LIVE_EXECUTION": "false",
        "RECOVERY_REQUEST_SEQUENCE": "2026-10-15T16:14:00Z",
    }


def test_workflow_replays_pinned_artifact_and_never_runs_source_capture():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for value in (
        "38762761429",
        "9caaa609f8793180c6518f52df1f595450d9ff0b",
        str(CAPTURE_ARTIFACT_ID),
        CAPTURE_ARTIFACT_NAME,
        CAPTURE_ARTIFACT_SHA256,
        R7_SOURCE_CAPTURE_RECEIPT_FP,
        R7_SOURCE_CAPTURE_SEQUENCE,
    ):
        assert value in workflow
    assert "automation.q104_i19_residual_policy_applicability_review_r7 replay" in workflow
    assert "automation.q104_i19_residual_policy_applicability_review_r7 capture" not in workflow
    assert "offline_source_requests_made" in workflow
    assert "network_requests_made_on_arm64" in workflow
    assert "runs-on: ubuntu-24.04-arm" in workflow
    assert "expected-analysis-fingerprint" in workflow


def test_recovery_has_no_scientific_or_execution_authority():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'assert receipt["interpretation_scope"]["field_precedence_applied"] is False' in workflow
    assert 'assert receipt["interpretation_scope"]["acceptance_time_gate_cleared"] is False' in workflow
    assert 'assert receipt["interpretation_scope"]["historical_archive_gate_cleared"] is False' in workflow
    assert 'assert receipt["interpretation_scope"]["performance_authorization"] is False' in workflow
    assert 'assert receipt["interpretation_scope"]["promotion"] is False' in workflow
    assert 'assert receipt["interpretation_scope"]["live_execution"] is False' in workflow
    assert "no sec requests" in workflow.lower() or "no sec source requests" in workflow.lower()
