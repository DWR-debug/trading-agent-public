from automation.autonomous_control_plane import eligible_issues, plan, validate_assignment_contracts


def issue(number: int, created_at: str, *, labels=None, assignees=None):
    task_id = f"AGENT-{number}"
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


def test_eligible_filters_owner_label_assignment_and_pr():
    good = issue(1, "2026-09-27T11:00:00Z")
    assigned = issue(2, "2026-09-27T11:01:00Z", assignees=[{"login": "x"}])
    assert [x["number"] for x in eligible_issues([assigned, good], "DWR-debug")] == [1]


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
