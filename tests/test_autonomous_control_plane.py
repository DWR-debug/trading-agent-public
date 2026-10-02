import json

import pytest

from automation.agent_dispatch import AgentDispatchError
from automation.autonomous_control_plane import (
    validate_lease_snapshot,
    eligible_issues,
    plan,
    validate_assignment_contracts,
    validate_request_snapshot,
)


def issue(number: int, created_at: str, *, labels=None, assignees=None, task_id=None):
    task_id = task_id or f"AGENT-{number}"
    body = (
        "<!-- TRADING_AGENT_TASK_V1\n"
        + "{\"schema_version\":1,\"task_id\":\"" + task_id
        + "\",\"worker_class\":\"engineering\",\"custom_agent\":\"trading-agent-engineer\","
        + "\"base_branch\":\"master\",\"scope\":\"bounded engineering\",\"max_session_minutes\":30,"
        + "\"deterministic_compute\":false,\"holdout_selection\":false,\"parameter_selection\":false,"
        + "\"asset_selection\":false,\"threshold_selection\":false,\"horizon_selection\":false,"
        + "\"research_gate_changes\":false,\"promotion_decision\":false,\"live_execution\":false,"
        + "\"paid_usage\":false,\"research_decision\":false,\"manual_handoff_required\":false}\n-->"
    )
    return {
        "number": number,
        "state": "open",
        "user": {"login": "DWR-debug"},
        "labels": [{"name": x} for x in (labels if labels is not None else ["agent-cli-ready"])],
        "assignees": assignees or [],
        "created_at": created_at,
        "body": body,
    }


def request(lane, task_id):
    return {
        "lane": lane,
        "task_id": task_id,
        "path": f"agent_requests/lane{lane}/{task_id}.request",
    }


def test_validate_lease_snapshot_enforces_two_slot_state():
    state = {
        "schema_version": 1,
        "slot_count": 2,
        "slots": [
            {"task_id": "AGENT-A", "issue_number": 1, "manifest_fingerprint": "a" * 64, "run_id": "r1", "binding_fingerprint": "b" * 64, "acquired_at": 100.0, "expires_at": 200.0, "status": "ACTIVE"},
            {"task_id": "AGENT-B", "issue_number": 2, "manifest_fingerprint": "c" * 64, "run_id": "r2", "binding_fingerprint": "d" * 64, "acquired_at": 100.0, "expires_at": 200.0, "status": "ACTIVE"},
        ],
    }
    normalized = validate_lease_snapshot(state, now=150.0)
    assert len([x for x in normalized["slots"] if x is not None]) == 2


def test_validate_lease_snapshot_prunes_stale_slots():
    state = {
        "schema_version": 1,
        "slot_count": 2,
        "slots": [
            {"task_id": "AGENT-A", "issue_number": 1, "manifest_fingerprint": "a" * 64, "run_id": "r1", "binding_fingerprint": "b" * 64, "acquired_at": 100.0, "expires_at": 100.0, "status": "ACTIVE"},
            None,
        ],
    }
    normalized = validate_lease_snapshot(state, now=100.0)
    assert normalized["slots"] == [None, None]

def test_eligible_filters_owner_label_assignment_and_pr():
    good = issue(1, "2026-09-27T11:00:00Z")
    assigned = issue(2, "2026-09-27T11:01:00Z", assignees=[{"login": "x"}])
    assert [x["number"] for x in eligible_issues([assigned, good], "DWR-debug")] == [1]


def test_eligible_accepts_agent_ready_before_cli_activation():
    candidate = issue(11, "2026-09-27T10:59:00Z", labels=["agent-ready"])
    assert [x["number"] for x in eligible_issues([candidate], "DWR-debug")] == [11]


def test_plan_retires_published_branch_and_fills_lane():
    result = plan(
        issues=[issue(2, "2026-09-27T11:00:00Z"), issue(3, "2026-09-27T11:01:00Z")],
        requests=[request("0", "AGENT-1")],
        existing_branches={"agent/AGENT-1-copilot-cli"},
        owner="DWR-debug",
    )
    assert result["retire"][0]["task_id"] == "AGENT-1"
    assert result["assign"] == [{
        "lane": "0",
        "issue_number": 2,
        "task_id": "AGENT-2",
        "path": "agent_requests/lane0/AGENT-2.request",
    }, {
        "lane": "1",
        "issue_number": 3,
        "task_id": "AGENT-3",
        "path": "agent_requests/lane1/AGENT-3.request",
    }]


def test_plan_uses_second_lane_when_first_is_occupied():
    result = plan(
        issues=[issue(2, "2026-09-27T11:00:00Z")],
        requests=[request("0", "AGENT-1")],
        existing_branches=set(),
        owner="DWR-debug",
    )
    assert result["assign"][0]["lane"] == "1"


def test_plan_never_exceeds_two_lanes():
    result = plan(
        issues=[issue(i, f"2026-09-27T11:{i:02d}:00Z") for i in range(1, 8)],
        requests=[],
        existing_branches=set(),
        owner="DWR-debug",
    )
    assert len(result["assign"]) == 2


def test_plan_assigns_duplicate_task_id_only_once():
    result = plan(
        issues=[
            issue(2, "2026-09-27T11:00:00Z", task_id="AGENT-DUPLICATE"),
            issue(3, "2026-09-27T11:01:00Z", task_id="AGENT-DUPLICATE"),
        ],
        requests=[],
        existing_branches=set(),
        owner="DWR-debug",
    )
    assert len(result["assign"]) == 1
    assert result["assign"][0]["task_id"] == "AGENT-DUPLICATE"


def test_plan_rejects_duplicate_task_id_already_in_queue():
    with pytest.raises(AgentDispatchError, match="Duplicate queued task_id"):
        plan(
            issues=[],
            requests=[request("0", "AGENT-DUPLICATE"), request("1", "AGENT-DUPLICATE")],
            existing_branches=set(),
            owner="DWR-debug",
        )


def test_queue_snapshot_fails_closed_when_api_omits_checked_out_request(tmp_path):
    lane = tmp_path / "lane0"
    lane.mkdir()
    (lane / "AGENT-5.request").write_text(
        json.dumps({"issue_number": 5, "task_id": "AGENT-5"}),
        encoding="utf-8",
    )

    with pytest.raises(AgentDispatchError, match="does not match"):
        validate_request_snapshot([], lanes=("0", "1"), request_root=tmp_path)


def test_queue_snapshot_accepts_matching_request_inventory(tmp_path):
    lane = tmp_path / "lane0"
    lane.mkdir()
    (lane / "AGENT-5.request").write_text(
        json.dumps({"issue_number": 5, "task_id": "AGENT-5"}),
        encoding="utf-8",
    )

    validate_request_snapshot(
        [request("0", "AGENT-5")],
        lanes=("0", "1"),
        request_root=tmp_path,
    )


def test_unsafe_task_fails_closed():
    bad = issue(9, "2026-09-27T11:00:00Z")
    bad["body"] = bad["body"].replace('\"paid_usage\":false', '\"paid_usage\":true')
    try:
        validate_assignment_contracts(
            {9: bad},
            [{"lane": "0", "issue_number": 9, "task_id": "AGENT-9"}],
            "a" * 40,
        )
    except Exception as exc:
        assert "paid_usage" in str(exc)
    else:
        raise AssertionError("unsafe task accepted")


def test_master_sha_is_required_even_when_plan_has_no_assignments():
    with pytest.raises(AgentDispatchError, match="explicitly supplied"):
        validate_assignment_contracts({}, [], "")


def test_queue_snapshot_rejects_embedded_performance_result_fields(tmp_path):
    lane = tmp_path / "lane0"
    lane.mkdir()
    payload = {
        "issue_number": 5,
        "task_id": "AGENT-5",
        "metadata": {"holdout_return": 0.42},
    }
    (lane / "AGENT-5.request").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(AgentDispatchError, match="Forbidden research-result field"):
        validate_request_snapshot(
            [request("0", "AGENT-5")],
            lanes=("0", "1"),
            request_root=tmp_path,
        )
