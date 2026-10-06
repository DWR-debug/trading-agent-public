from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_resource_availability_policy_is_always_routable_and_safe():
    data = json.loads(
        (ROOT / "research/governance/resource_availability_policy_2026_10_03.json").read_text(encoding="utf-8")
    )
    routing = data["routing_policy"]
    assert routing["self_hosted_windows"] == "ASSUMED_ALWAYS_AVAILABLE"
    assert routing["s10"] == "ASSUMED_ALWAYS_AVAILABLE"
    assert routing["android_fleet"] == "RESERVE_ONLY"
    assert data["capacity"]["android_device_pool"] == "reserve-only; no recurring routing"
    assert routing["fresh_receipts_are_required_for_evidence_claims"] is True
    assert data["capacity"]["windows_runner_slots"] == 2
    assert data["capacity"]["permanent_loop_lanes"] == ["local_reproduction", "data_qa"]
    assert data["capacity"]["logical_research_lanes"] == ["formal_readiness", "frontier_discovery"]
    assert data["capacity"]["two_lane_roles"]["formal_readiness"].startswith("Advanced Coverage/PIT")
    assert data["capacity"]["two_lane_roles"]["frontier_discovery"].startswith("Orthogonal source/PIT")
    assert data["capacity"]["lane_isolation_required"] is True
    assert data["capacity"]["performance_authorization_from_capacity"] is False
    assert data["capacity"]["hosted_failover"] == "manual_only"
    assert data["safety"]["PAPER_ONLY"] is True
    assert data["safety"]["LIVE_TRADING_ENABLED"] is False
    assert data["safety"]["ORDERS_ENABLED"] is False
    assert data["safety"]["AUTOMATIC_PROMOTION"] is False


def test_status_sync_exposes_availability_assumption_without_promoting_receipts():
    text = (ROOT / "automation/sync_current_operational_status.py").read_text(encoding="utf-8")
    assert 'ASSUMED_ALWAYS_AVAILABLE' in text
    assert '"routing_uses_presence_receipt": False' in text
    assert '"receipts_remain_diagnostic_and_evidentiary": True' in text
