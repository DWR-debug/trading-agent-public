from pathlib import Path

from automation.source_readiness_snapshot_guard import classify


def test_live_probe_only_source_receipt_is_provisional():
    receipt = {
        "status": "SOURCE_COMPONENT_READY",
        "content_sha256": "abc123",
        "source_results": {"X": {"http_status": 200}},
    }
    assert classify(receipt) == "PROVISIONAL_LIVE_PROBE_ONLY"


def test_dated_snapshot_binding_is_durable():
    receipt = {
        "status": "SOURCE_COMPONENT_READY",
        "content_sha256": "abc123",
        "archive_contract": {"dated_snapshot": "2026-09-01", "snapshot_sha256": "def456"},
    }
    assert classify(receipt) == "DURABLE_HISTORICAL_BOUND"


def test_blocked_source_is_not_promoted_by_guard():
    receipt = {"status": "BLOCKED_SOURCE_COMPONENTS"}
    assert classify(receipt) == "NON_SOURCE_READY_STATE"


def test_guard_is_not_a_performance_gate():
    text = Path("automation/source_readiness_snapshot_guard.py").read_text(encoding="utf-8")
    assert "performance_authorized" in text
    assert "holdout_selection" in text
    assert "live_execution" in text
