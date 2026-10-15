from pathlib import Path

from automation.project_integrity_check import ACTIVE_WORKFLOWS, REQUIRED_FILES, ROOT


WORKFLOW_NAME = "q221-pre-event-parent-identity-feasibility.yml"
WORKFLOW = ROOT / ".github" / "workflows" / WORKFLOW_NAME
REQUEST = ROOT / "research" / "run_requests" / "q221_pre_event_parent_identity_feasibility.trigger"
PREREG = ROOT / "research" / "preregistrations" / "q221_pre_event_parent_identity_feasibility_2026_10_15.json"


def test_q221_pre_event_workflow_is_registered_and_request_triggered_only():
    assert WORKFLOW_NAME in ACTIVE_WORKFLOWS
    assert WORKFLOW.is_file()
    assert REQUEST.is_file()
    assert PREREG.is_file()
    workflow = WORKFLOW.read_text(encoding="utf-8")
    trigger = workflow.split("\npermissions:", 1)[0]
    assert 'paths:\n      - "research/run_requests/q221_pre_event_parent_identity_feasibility.trigger"' in trigger
    assert trigger.count("paths:") == 1
    assert "workflow_dispatch:" not in workflow


def test_only_x64_job_may_fetch_exactly_five_sec_source_documents():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count("--fetch-sources") == 1
    assert workflow.count("--expected-analysis-fingerprint") == 1
    assert workflow.count("actions/download-artifact@v6") == 4
    assert workflow.count("actions/upload-artifact@v6") == 3
    assert "q221-current-parent-identity-map-38305074104-1" in workflow
    assert "run-id: 38305074104" in workflow
    assert "artifact id 11772786096" not in workflow.lower()  # artifact ID is verified through gh api below
    assert ".id == 11772786096" in workflow
    assert ".expired == false" in workflow
    assert "Q221_CROSS_ARCH_MISMATCH" in workflow
    assert "DETERMINISTIC_ANALYSIS_MATCHED" in workflow
    assert "q221_pre_event_parent_identity_feasibility_latest.json" in workflow


def test_five_document_download_bounds_and_no_mapping_authority_are_enforced():
    values = dict(
        line.split("=", 1)
        for line in REQUEST.read_text(encoding="utf-8").splitlines()
        if line
    )
    assert values["SOURCE_OF_TRUTH"] == "DWR-debug/trading-agent-public"
    assert values["MAX_SEC_REQUESTS"] == "5"
    assert values["MAX_RESPONSE_BYTES_EACH"] == "250000"
    assert values["MAX_AGGREGATE_RESPONSE_BYTES"] == "1000000"
    assert values["AUTOMATIC_RETRIES"] == "false"
    assert values["NO_ISSUER_MAPPING_FREEZE"] == "true"
    assert values["NO_HISTORICAL_GATE_UNLOCK"] == "true"
    assert values["PAPER_ONLY"] == "true"
    assert values["LIVE_TRADING_ENABLED"] == "false"
    assert values["ORDERS_ENABLED"] == "false"
    assert values["AUTOMATIC_PROMOTION"] == "false"
    assert values["PAID_API_BUDGET_USD"] == "0"


def test_new_q221_feasibility_files_are_in_the_integrity_inventory():
    required = {p.relative_to(ROOT).as_posix() for p in REQUIRED_FILES}
    assert "automation/q221_pre_event_parent_identity_feasibility.py" in required
    assert "research/preregistrations/q221_pre_event_parent_identity_feasibility_2026_10_15.json" in required
    assert "research/run_requests/q221_pre_event_parent_identity_feasibility.trigger" in required
    assert "tests/test_q221_pre_event_parent_identity_feasibility.py" in required
    assert "tests/test_q221_pre_event_parent_identity_workflow.py" in required
