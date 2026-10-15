import json
from pathlib import Path

import pytest

from automation import q104_i19_residual_policy_applicability_review_r7 as r7
from automation.project_integrity_check import ACTIVE_WORKFLOWS, ROOT


def test_r7_frozen_target_keys_are_exact_and_disjoint_from_existing_seventeen():
    targets = [a for p in r7.ARCHIVES.values() for a in p["accessions"]]
    assert len(targets) == 19
    assert len(set(targets)) == 19
    assert sum(len(p["accessions"]) for p in r7.ARCHIVES.values()) == 19
    assert r7.TOTAL_ARCHIVE_BYTES == 127_943_839
    assert r7.TOTAL_ARCHIVE_BYTES < r7.MAX_TOTAL_BYTES
    assert all(p["bytes"] <= r7.MAX_ARCHIVE_BYTES for p in r7.ARCHIVES.values())
    assert sum(r7.FAILURE_COUNTS.values()) == 53
    assert sum(r7.FAILURE_COUNTS[k] for k in r7.DATE_FAILURES) == 36


def test_checked_in_request_matches_every_frozen_runtime_pin():
    request = ROOT / "research/run_requests/q104_i19_residual_policy_applicability_r7.trigger"
    values = r7.read_request(request)
    assert values["SOURCE_OF_TRUTH"] == "DWR-debug/trading-agent-public"
    assert values["REQUEST_SEQUENCE"] == "2026-10-15T10:01:00Z"
    assert values["EXPECTED_SOURCE_ARCHIVE_DOWNLOAD_BYTES"] == "127943839"
    assert values["DATE_MISMATCH_TARGET_COUNT"] == "19"
    assert values["HEADER_ROUTE_COUNT"] == "57"


def test_request_contract_is_preregistered_paper_only_and_has_no_gate_authority(tmp_path):
    request = tmp_path / "request.trigger"
    values = dict(r7.FROZEN)
    values["REQUEST_SEQUENCE"] = "2026-10-15T09:59:00Z"
    request.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    assert r7.read_request(request) == values
    for key in (
        "CENSUS_RESTART", "REPAIR_RECEIPTS", "APPLY_FIELD_PRECEDENCE",
        "CHANGE_PRODUCTION_JOIN", "PERFORMANCE", "HOLDOUT_SELECTION",
        "RANKING", "TUNING", "PROMOTION", "LIVE_EXECUTION",
    ):
        assert values[key] == "false"
    assert values["NO_NEW_DAILY_FEED_REQUESTS"] == "true"
    assert values["NO_PRIMARY_DOCUMENT_REQUESTS"] == "true"
    assert values["NO_SOURCE_RECEIPT_REWRITES"] == "true"
    assert values["RESEARCH_GATES_REMAIN_CLOSED"] == "true"
    assert values["PAID_API_BUDGET_USD"] == "0"


def test_request_rejects_a_mutated_performance_or_hash_policy(tmp_path):
    vals = dict(r7.FROZEN)
    vals["REQUEST_SEQUENCE"] = "2026-10-15T09:59:00Z"
    vals["APPLY_FIELD_PRECEDENCE"] = "true"
    p = tmp_path / "bad.trigger"
    p.write_text("".join(f"{k}={v}\n" for k, v in vals.items()), encoding="utf-8")
    with pytest.raises(r7.ReviewError, match="REQUEST_VALUE_MISMATCH:APPLY_FIELD_PRECEDENCE"):
        r7.read_request(p)


def test_combined_budget_enforces_total_and_header_limits_separately():
    budget = r7.CombinedBudget(total=20, header=4)
    budget.add(7)
    budget.is_header_phase = True
    budget.add(4)
    assert budget.used == 11
    assert budget.header_used == 4
    with pytest.raises(r7.ReviewError, match="HEADER_DOWNLOAD_BUDGET_EXCEEDED"):
        budget.add(1)
    budget2 = r7.CombinedBudget(total=3, header=3)
    with pytest.raises(r7.ReviewError, match="TOTAL_DOWNLOAD_BUDGET_EXCEEDED"):
        budget2.add(4)


def test_current_pinned_helper_implementations_match_the_frozen_contract():
    assert r7.validate_helpers() == r7.HELPER_BLOBS


def test_capture_validator_fails_closed_before_it_can_authorize_incomplete_evidence():
    incomplete = {
        "record_type": "q104_i19_residual_policy_applicability_r7_capture",
        "status": "Q104_I19_RESIDUAL_R7_CAPTURE_INCOMPLETE",
        "receipt_fingerprint": "not-a-valid-fingerprint",
    }
    with pytest.raises(r7.ReviewError, match="CAPTURE_RECEIPT_FINGERPRINT_OR_STATUS_INVALID"):
        r7.validate_capture_payload({}, incomplete)


def test_safety_contract_has_no_live_orders_or_automatic_promotion():
    assert r7.SAFETY == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "paid_api_budget_usd": 0,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    }


def test_workflow_is_registered_and_requires_only_the_explicit_request_marker():
    name = "q104-i19-residual-policy-applicability-r7.yml"
    assert name in ACTIVE_WORKFLOWS
    workflow = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
    trigger = workflow.split("\npermissions:", 1)[0]
    assert 'paths:\n      - "research/run_requests/q104_i19_residual_policy_applicability_r7.trigger"' in trigger
    assert "workflow_dispatch:" not in trigger
    assert "q104-i19-residual-policy-applicability-r7.yml" in ACTIVE_WORKFLOWS


def test_workflow_uses_immutable_input_artifact_ids_and_no_primary_document_downloads():
    workflow = (ROOT / ".github" / "workflows" / "q104-i19-residual-policy-applicability-r7.yml").read_text(encoding="utf-8")
    for value in (
        "38250105408", "11747003791", "38557631541", "11890995910", "11891525016",
        "38574180245", "11899236364", "38582684174", "11902804060", "38588100012", "11905763813",
        "q104_i19_residual_policy_applicability_r7.trigger",
    ):
        assert value in workflow
    assert "no-new-primary" in workflow.lower()
    assert "NO_PRIMARY_DOCUMENT_REQUESTS" in (ROOT / "research" / "run_requests" / "q104_i19_residual_policy_applicability_r7.trigger").read_text(encoding="utf-8")
    assert "runs-on: ubuntu-24.04-arm" in workflow
    assert "--expected-analysis-fingerprint" in workflow
    assert "Q104_R7_CROSS_ARCH" in workflow or "cross-arch" in workflow.lower()
