from pathlib import Path

from automation.project_integrity_check import ACTIVE_WORKFLOWS, ROOT
from automation.q220_source_hash_timeline_reconciliation import (
    AUDIT_GIT_BLOB_SHA1,
    AUDIT_PATH,
    CURRENT_LINEAGE_GIT_BLOB_SHA1,
    EXPECTED_SHA,
    FIRST_NEGATIVE_RUN_ID,
    INDEPENDENT_RUN_ID,
    LINEAGE_PATH,
    POSITIVE_RUN_ID,
    SAFETY,
    TimelineError,
    build_analysis,
    read_pinned_json,
)

REQUEST = ROOT / "research" / "run_requests" / "q220_source_hash_timeline_reconciliation.trigger"
WORKFLOW = ROOT / ".github" / "workflows" / "q220-source-hash-timeline-reconciliation.yml"


def _inputs():
    audit, _ = read_pinned_json(ROOT, AUDIT_PATH, AUDIT_GIT_BLOB_SHA1)
    current, _ = read_pinned_json(ROOT, LINEAGE_PATH, CURRENT_LINEAGE_GIT_BLOB_SHA1)
    return audit, current


def test_historical_hash_match_and_current_absence_are_distinguished():
    audit, current = _inputs()
    report = build_analysis(audit, current)
    assert report["status"] == "HISTORICAL_HASH_MATCH_ATTESTED_CURRENT_LINEAGE_UNRESOLVED"
    assert report["frozen_expected"]["sha256"] == EXPECTED_SHA
    assert report["frozen_expected"]["historical_match_attested"] is True
    assert report["frozen_expected"]["historical_raw_body_preserved"] is False
    assert report["frozen_expected"]["present_in_current_whole_primary_observation_set"] is False
    assert report["current_observation_state"]["distinct_whole_primary_hash_count"] == 4
    assert report["current_observation_state"]["whole_primary_observation_count"] == 4
    assert report["interpretation_scope"]["current_gate_positive"] is False


def test_historical_positive_and_first_negative_share_exact_compiler_identity():
    audit, current = _inputs()
    report = build_analysis(audit, current)
    positive = report["historical_positive"]
    negative = report["first_known_blocked"]
    assert positive["compiler_run_id"] == POSITIVE_RUN_ID
    assert positive["independent_run_id"] == INDEPENDENT_RUN_ID
    assert positive["verified_primary_document_count"] == 55
    assert positive["source_hash_failure_count"] == 0
    assert negative["compiler_run_id"] == FIRST_NEGATIVE_RUN_ID
    assert negative["verified_primary_document_count"] == 0
    assert negative["source_hash_failure_count"] == 55
    assert negative["same_compiler_code_as_last_positive"] is True
    assert positive["compiler_code_sha256"] == negative["compiler_code_sha256"]
    assert positive["compiler_source_git_blob_sha1"] == negative["compiler_source_git_blob_sha1"]
    assert report["first_observed_transition_window"]["elapsed_seconds"] == 24830.828977
    assert report["first_observed_transition_window"]["server_side_transition_time_proven"] is False


def test_same_code_population_capture_shift_did_not_prove_root_cause():
    audit, current = _inputs()
    report = build_analysis(audit, current)
    shift = report["same_code_population_capture_shift"]
    assert shift["changed_hash_rows"] == 55
    assert shift["changed_byte_length_rows"] == 55
    assert shift["byte_delta_distribution"] == {"-5": 55}
    assert shift["header_hash_rows_changed"] == 55
    assert shift["directory_index_hashes_unchanged"] is True
    assert shift["root_cause_proven"] is False
    assert report["interpretation_scope"]["authoritative_source_vintage_proven"] is False


def test_historical_reconciliation_preserves_paper_only_and_closed_gates():
    audit, current = _inputs()
    report = build_analysis(audit, current)
    assert report["safety"] == SAFETY
    scope = report["interpretation_scope"]
    assert scope["historical_hash_match_attested"] is True
    assert scope["current_gate_positive"] is False
    assert scope["scientific_evidence"] is False
    assert scope["performance_authorization"] is False
    assert scope["holdout_selection"] is False
    assert scope["ranking"] is False
    assert scope["tuning"] is False
    assert scope["promotion"] is False
    assert scope["live_execution"] is False


def test_q220_timeline_workflow_is_integrity_registered_and_explicit_request_only():
    workflow_name = "q220-source-hash-timeline-reconciliation.yml"
    assert workflow_name in ACTIVE_WORKFLOWS
    assert WORKFLOW.is_file()
    workflow = WORKFLOW.read_text(encoding="utf-8")
    trigger = workflow.split("\npermissions:", 1)[0]
    assert 'paths:\n      - "research/run_requests/q220_source_hash_timeline_reconciliation.trigger"' in trigger
    assert "workflow_dispatch:" not in workflow
    assert "https://www.sec.gov" not in workflow
    assert "actions/download-artifact@v6" in workflow
    assert 'path: q220-arm64' in workflow
    assert 'Path("q220-arm64/receipt.json")' in workflow
    assert 'Path("q220-arm64/arm64/receipt.json")' not in workflow


def test_timeline_request_freezes_both_committed_receipt_blobs_and_no_network_sources():
    values = dict(
        line.split("=", 1)
        for line in REQUEST.read_text(encoding="utf-8").splitlines()
        if line
    )
    assert values["HISTORICAL_AUDIT_GIT_BLOB_SHA1"] == AUDIT_GIT_BLOB_SHA1
    assert values["CURRENT_LINEAGE_GIT_BLOB_SHA1"] == CURRENT_LINEAGE_GIT_BLOB_SHA1
    assert values["REQUEST_SEQUENCE"] == "2026-10-15T11:15:00Z"
    assert values["EXPECTED_SHA256"] == EXPECTED_SHA
    assert values["NO_SEC_REQUESTS"] == "true"
    assert values["NO_BODY_REDOWNLOADS"] == "true"
    assert values["NO_HASH_REWRITES"] == "true"
    assert values["PAPER_ONLY"] == "true"
    assert values["LIVE_TRADING_ENABLED"] == "false"
    assert values["ORDERS_ENABLED"] == "false"
    assert values["AUTOMATIC_PROMOTION"] == "false"
