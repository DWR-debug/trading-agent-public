from pathlib import Path

from automation.project_integrity_check import ACTIVE_WORKFLOWS, REQUIRED_FILES, ROOT


NAME = "q221-fpds-public-atom-identity-bridge.yml"
WORKFLOW = ROOT / ".github" / "workflows" / NAME
REQUEST = ROOT / "research" / "run_requests" / "q221_fpds_public_atom_identity_bridge.trigger"
PREREG = ROOT / "research" / "preregistrations" / "q221_fpds_public_atom_identity_bridge_2026_10_15.json"
SCRIPT = ROOT / "automation" / "q221_fpds_public_atom_identity_bridge.py"


def test_q221_fpds_workflow_is_registered_and_request_marker_triggered_only():
    assert NAME in ACTIVE_WORKFLOWS
    assert WORKFLOW.is_file()
    assert REQUEST.is_file()
    assert PREREG.is_file()
    trigger = WORKFLOW.read_text(encoding="utf-8").split("\npermissions:", 1)[0]
    assert 'paths:\n      - "research/run_requests/q221_fpds_public_atom_identity_bridge.trigger"' in trigger
    assert trigger.count("paths:") == 1
    assert "workflow_dispatch:" not in trigger


def test_integrity_inventory_includes_every_static_q221_fpds_bridge_input():
    required = {path.relative_to(ROOT).as_posix() for path in REQUIRED_FILES}
    for relative in (
        ".github/workflows/q221-fpds-public-atom-identity-bridge.yml",
        "automation/q221_fpds_public_atom_identity_bridge.py",
        "research/preregistrations/q221_fpds_public_atom_identity_bridge_2026_10_15.json",
        "research/run_requests/q221_fpds_public_atom_identity_bridge.trigger",
        "docs/research_design/Q221_FPDS_HISTORICAL_IDENTIFIER_BRIDGE_2026-10-15.md",
        "tests/test_q221_fpds_public_atom_identity_bridge.py",
        "tests/test_q221_fpds_public_atom_identity_bridge_workflow.py",
    ):
        assert relative in required


def test_workflow_uses_one_bounded_network_stage_and_arm64_is_offline_only():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count("--mode capture") == 1
    assert workflow.count("--mode verify") == 1
    assert "run: curl" not in workflow.lower()
    assert "curl.exe" not in workflow.lower()
    assert "api.contract-awards" not in workflow
    assert "sam.gov/api" not in workflow.lower()
    assert "q221-fpds-public-atom-x64-" in workflow
    assert "q221-fpds-public-atom-arm64-" in workflow
    assert "DETERMINISTIC_CAPTURE_RECEIPT_VALIDATED_NOT_SOURCE_REPLAYED" in workflow
    assert "Q221_FPDS_X64_ARM64_ANALYSIS_FINGERPRINT_MISMATCH" in workflow
    assert "q221_fpds_public_atom_identity_bridge_latest.json" in workflow


def test_preregistered_request_limits_and_safety_flags_are_exact():
    values = dict(
        line.split("=", 1)
        for line in REQUEST.read_text(encoding="utf-8").splitlines()
        if line
    )
    assert values["TARGET_RECORD_COUNT"] == "4"
    assert values["MAX_RESPONSE_BYTES_EACH"] == "1000000"
    assert values["MAX_TOTAL_RESPONSE_BYTES"] == "4000000"
    assert values["MAX_ATOM_ENTRIES_EACH"] == "250"
    assert values["RETRIES"] == "0"
    assert values["FOLLOW_REDIRECTS"] == "false"
    for key in (
        "NO_SAM_API_REQUESTS",
        "NO_NEW_USASPENDING_REQUESTS",
        "NO_SEC_REQUESTS",
        "NO_ARCHIVE_DOWNLOADS",
        "NO_SOURCE_ROW_OR_HASH_CHANGES",
    ):
        assert values[key] == "true"
    assert values["PAPER_ONLY"] == "true"
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


def test_source_script_does_not_follow_redirects_or_persist_source_bodies():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "class _NoRedirect" in source
    assert "redirect_request" in source
    assert '"response_persisted": False' in source
    assert '"source_bodies_persisted": False' in source
    assert 'historical_first_public_observation_proven": False' in source
    assert 'recipient_to_issuer_mapping_frozen": False' in source
