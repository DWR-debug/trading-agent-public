from pathlib import Path

from automation.project_integrity_check import ACTIVE_WORKFLOWS, ROOT


REQUEST = ROOT / "research" / "run_requests" / "q220_hash_provenance_diagnostic.trigger"
WORKFLOW = ROOT / ".github" / "workflows" / "q220-offline-source-hash-lineage.yml"


def _request_values():
    return dict(
        line.split("=", 1)
        for line in REQUEST.read_text(encoding="utf-8").splitlines()
        if line
    )


def test_q220_offline_workflow_is_registered_and_explicitly_request_triggered():
    assert "q220-offline-source-hash-lineage.yml" in ACTIVE_WORKFLOWS
    assert WORKFLOW.is_file()
    workflow = WORKFLOW.read_text(encoding="utf-8")
    trigger = workflow.split("\npermissions:", 1)[0]
    assert 'paths:\n      - "research/run_requests/q220_hash_provenance_diagnostic.trigger"' in trigger
    assert trigger.count('paths:') == 1
    assert "workflow_dispatch:" not in workflow


def test_q220_request_pins_all_three_immutable_receipts_and_current_compiler():
    values = _request_values()
    expected = {
        "RUN_Q220_OFFLINE_SOURCE_HASH_LINEAGE_DIAGNOSTIC": "true",
        "SOURCE_OF_TRUTH": "DWR-debug/trading-agent-public",
        "Q220_COMPILER_RECEIPT_FINGERPRINT": "1ca885190d7b277c809ac8a6c3386a637e7750df6bb51755260c9bd7351f868d",
        "Q220_COMPILER_CODE_SHA256": "08f904ef38cbf8b1fb3adbf8542d9642c786ffc0d2be51fd56546263e7f1264c",
        "Q220_FORENSICS_RUN_ID": "38254139755",
        "Q220_FORENSICS_ARTIFACT_ID": "11749259509",
        "Q220_HEADER_RUN_ID": "38258251764",
        "Q220_HEADER_ARTIFACT_ID": "11751436149",
        "Q220_SENSITIVITY_RUN_ID": "38590133217",
        "Q220_SENSITIVITY_ARTIFACT_ID": "11907246485",
        "Q220_SENSITIVITY_RECEIPT_FINGERPRINT": "870aa4fdae7eda932bb8f50ebb9eab1a7781ee503fb5120dea5b0f099e4fd65c",
        "Q220_SENSITIVITY_REQUEST_FINGERPRINT": "211b2afacf8eddf0b8b56aaf9ee7896e14d5788ba88e9ada0d98be101158f0e2",
        "Q220_EXPECTED_PRIMARY_SHA256": "27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83",
        "Q220_ORIGINAL_CAPTURE_SHA256": "08039132d6d6d1692d1f7552193c70a04cad4c1dcadad1cfa3ca2b8b4efe3fdb",
        "Q220_HTTP_PROBE_SHA256": "fc7dfedd605cdbc9e497bb0c0bc306c74e3f90493a68fb6025d762540ef600f3",
        "Q220_CURRENT_COMPILER_SHA256": "ccd9060d023c3ca8e5fc5d3fd43a67c394dfd97ef1e42a72f71c4ca630cd2f63",
        "Q220_SINGLE_FEED_SHA256": "2693819652172f0c218394ef036eb3f4af95c2a7077f624f6efcd990df370172",
        "Q220_DISTINCT_WHOLE_PRIMARY_HASH_COUNT": "4",
    }
    for key, value in expected.items():
        assert values[key] == value
    assert values["NO_NEW_FEED_DOWNLOADS"] == "true"
    assert values["NO_NEW_PRIMARY_DOCUMENT_DOWNLOADS"] == "true"
    assert values["NO_HASH_REWRITES"] == "true"
    assert values["NO_POPULATION_CHANGES"] == "true"
    assert values["NO_CENSUS_RESTART"] == "true"


def test_q220_request_holds_all_execution_and_selection_authorities_closed():
    values = _request_values()
    for key in (
        "LIVE_TRADING_ENABLED",
        "ORDERS_ENABLED",
        "AUTOMATIC_PROMOTION",
        "PERFORMANCE",
        "HOLDOUT_SELECTION",
        "RANKING",
        "TUNING",
        "PROMOTION",
        "LIVE_EXECUTION",
    ):
        assert values[key] == "false"
    assert values["PAPER_ONLY"] == "true"


def test_q220_workflow_only_downloads_pinned_receipts_and_never_requests_source_documents():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count("actions/download-artifact@v6") == 6
    assert "q220-primary-source-vintage-forensics-38254139755-1" in workflow
    assert "q220-bounded-header-evidence-38258251764-1" in workflow
    assert workflow.count("q220-http-representation-sensitivity-38590133217-1") == 2
    assert "https://www.sec.gov" not in workflow
    assert "curl " not in workflow
    assert "curl.exe" not in workflow
    assert "--sensitivity-artifact q220-work/inputs/sensitivity" in workflow
    assert "--sensitivity-artifact q220-first-result/inputs/sensitivity" in workflow


def test_q220_publish_contract_reproduces_determinism_without_opening_any_gate():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "needs: [analyze-x64, reproduce-arm64]" in workflow
    assert "Q220_CROSS_ARCH_ANALYSIS_FINGERPRINT_MISMATCH" in workflow
    assert "DETERMINISTIC_ANALYSIS_MATCHED" in workflow
    assert "q220_source_hash_lineage_latest.json" in workflow
    assert 'base-sha latest' in workflow
    assert '"distinct_whole_primary_sha256_count"] == 4' in workflow
    assert '"frozen_expected_hash_reproduced"] is False' in workflow
    assert '"gate_positive"] is False' in workflow
    assert '"performance_authorization"] is False' in workflow
    assert '"promotion"] is False' in workflow
