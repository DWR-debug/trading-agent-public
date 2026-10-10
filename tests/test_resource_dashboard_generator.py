from pathlib import Path
from automation.generate_resource_dashboard import infer_lane, infer_resource


def test_dashboard_lane_mapping_is_deterministic():
    assert infer_lane("Q121-R6 SEC Acceptance-Time Compilation") == "FORMAL READINESS"
    assert infer_lane("Q205 NLRB Source Feasibility") == "FRONTIER DISCOVERY"
    assert infer_lane("Top-4 Candidate Research Capacity", "Windows Top-4 Q218") == "FRONTIER DISCOVERY"
    assert infer_lane("Top-4 Candidate Research Capacity", "Windows Top-4 Q220") == "FRONTIER DISCOVERY"
    assert infer_lane("Top-4 Candidate Research Capacity", "Windows Top-4 Q221") == "FRONTIER DISCOVERY"
    assert infer_lane("T052 Exact Master CI Gate") == "PLATFORM / GOVERNANCE"


def test_dashboard_resource_mapping_is_deterministic():
    assert infer_resource("Any", "job", "LHT-N133732") == "Windows self-hosted A"
    assert infer_resource("Any", "job", "LHT-N133732-2") == "Windows self-hosted B"
    assert infer_resource("Any", "job", "LHT-N133732-3") == "Windows self-hosted C"
    assert infer_resource("Free AI Worker Fabric", "worker", None) == "Free AI pool"
    assert infer_resource("T052 Exact Master CI Gate", "gate", None) == "GitHub-hosted CI"


def test_dashboard_resource_identity_never_grants_authority():
    assert infer_resource("Q205 NLRB Source Feasibility", "source_feasibility", None)


def test_dashboard_research_board_exposes_q202_to_q205_without_duplicates():
    from automation.generate_resource_dashboard import expanded_candidate_board, research_board
    import json
    from pathlib import Path

    root = Path(__file__).parents[1]
    evidence = json.loads((root / "research/evidence/current_operational_state.json").read_text(encoding="utf-8"))
    os_state = json.loads((root / "ops/trading_agent_os_state.json").read_text(encoding="utf-8"))
    board = expanded_candidate_board(evidence, os_state, research_board(evidence, os_state))
    ids = [x["code"] for x in board]
    for candidate_id in ("Q202", "Q203", "Q204", "Q205"):
        assert candidate_id in ids
        assert ids.count(candidate_id) == 1



def test_dashboard_duration_benchmark_excludes_cancelled_and_uses_median():
    from automation.generate_resource_dashboard import duration_benchmarks

    runs = [
        {"name":"Demo","status":"completed","conclusion":"success","run_started_at":"2026-10-06T10:00:00Z","completed_at":"2026-10-06T10:01:00Z"},
        {"name":"Demo","status":"completed","conclusion":"success","run_started_at":"2026-10-06T10:00:00Z","completed_at":"2026-10-06T10:02:00Z"},
        {"name":"Demo","status":"completed","conclusion":"cancelled","run_started_at":"2026-10-06T10:00:00Z","completed_at":"2026-10-06T10:20:00Z"},
    ]
    bench = duration_benchmarks(runs)
    assert bench["Demo"]["p50_seconds"] == 90
    assert bench["Demo"]["sample_count"] == 2


def test_dashboard_capacity_state_is_explicit():
    from automation.generate_resource_dashboard import capacity_state

    physical = {"type":"physical"}
    cloud = {"type":"cloud"}
    assert capacity_state(physical, {"status":"online","busy":True}, []) == "available"
    assert capacity_state(physical, {"status":"online","busy":True}, [{"lane":"FRONTIER DISCOVERY"}]) == "operating"
    assert capacity_state(physical, {"status":"online","busy":False}, []) == "available"
    assert capacity_state(physical, None, []) == "unknown"
    assert capacity_state(cloud, None, []) == "available"


def test_dashboard_runner_busy_does_not_inflate_research_work():
    from automation.generate_resource_dashboard import enrich_resources

    resource = {
        "name": "Windows self-hosted A",
        "type": "physical",
        "research_capacity_slots": 1,
        "configured_runner": "runner-a",
        "role": "test",
    }
    enriched = enrich_resources(
        [resource],
        [{"name": "runner-a", "status": "online", "busy": True, "labels": []}],
        [],
    )[0]
    assert enriched["capacity_state"] == "available"
    assert enriched["current_assignments"] == 0
    assert enriched["runner_busy"] is True
    assert enriched["research_slots_in_use"] == 1
    assert enriched["research_slots_free"] == 0


def test_planned_capacity_keeps_one_step_lookahead_while_resource_is_active():
    from automation.generate_resource_dashboard import planned_capacity_plan

    resources = [
        {"name":"Windows self-hosted A","capacity_state":"operating","current_assignments":1},
        {"name":"Windows self-hosted B","capacity_state":"available","current_assignments":0},
        {"name":"Windows self-hosted C","capacity_state":"available","current_assignments":0},
        {"name":"GitHub-hosted Ubuntu x64","capacity_state":"available","current_assignments":0},
        {"name":"GitHub-hosted ARM64","capacity_state":"available","current_assignments":0},
        {"name":"Free AI pool","capacity_state":"available","current_assignments":0},
    ]
    work = [{"candidate":"Q104:I19","task":"Q104 I19","job":"historical census","resource":"Windows self-hosted A","lane":"FORMAL READINESS"}]
    top4 = [{"code": c, "next_gate":"gate"} for c in ("Q218","Q219","Q220","Q221")]
    plan = planned_capacity_plan(resources, work, top4, {}, {})
    by_resource = {x["resource"]: x for x in plan}
    assert by_resource["Windows self-hosted A"]["current_assignments"] == 1
    assert by_resource["Windows self-hosted A"]["planned_count"] == 1
    assert by_resource["Windows self-hosted A"]["planned_assignments"][0]["scheduled"] is True


def test_planned_research_backlog_is_locked_to_three_focus_candidates():
    from automation.generate_resource_dashboard import planned_research_backlog
    board = [{"code": code, "lane":"FRONTIER DISCOVERY", "next_gate":"gate"} for code in ("Q104:I19","Q218","Q219","Q220","Q221","Q224","Q229")]
    queue = planned_research_backlog(board)
    assert len(queue) == 3
    assert [x["candidate"] for x in queue] == ["Q104:I19","Q220","Q221"]
    assert all(x["planned_status"] == "READY_NEXT_GATE" for x in queue)
    assert all(x["execution_workflow"] for x in queue)


def test_dashboard_filters_platform_work_from_research_capacity():
    from automation.generate_resource_dashboard import current_work_from_runs
    runs = [
        {"id": 1, "name": "Full Suite Verification", "status": "in_progress", "created_at": "2026-10-06T18:00:00Z"},
        {"id": 2, "name": "CI", "status": "in_progress", "created_at": "2026-10-06T18:01:00Z"},
    ]
    assert current_work_from_runs(runs) == []


def test_milestone_history_12h_filters_platform_housekeeping(monkeypatch):
    from automation.generate_resource_dashboard import _is_material_milestone_commit, _is_research_milestone_run

    assert _is_material_milestone_commit("RESEARCH: advance Q220 source gate") is True
    assert _is_material_milestone_commit("OPS: remove global top-4 workflow bottleneck") is True
    assert _is_material_milestone_commit("OPS: refresh resource dashboard snapshot") is False
    assert _is_material_milestone_commit("OPS: synchronize current operational status") is False

    assert _is_research_milestone_run({
        "status": "completed", "conclusion": "success",
        "name": "Q228 SEC Correspondence Source Gate",
        "display_title": "Q228 SEC Correspondence Source Gate",
    }) is True
    assert _is_research_milestone_run({
        "status": "completed", "conclusion": "success",
        "name": "Resource Dashboard Update",
        "display_title": "Resource Dashboard Update",
    }) is False
    assert _is_research_milestone_run({
        "status": "completed", "conclusion": "failure",
        "name": "Q228 SEC Correspondence Source Gate",
        "display_title": "Q228 SEC Correspondence Source Gate",
    }) is False


def test_dashboard_exposes_bounded_hosted_research_slots():
    root = Path(__file__).parents[1]
    generator = (root / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert '"research_capacity_slots": 2' in generator
    assert '"research_capacity_slots_total"' in generator
    assert '"research_capacity_slots_free"' in generator


def test_candidate_progress_percentages_are_deterministic():
    from automation.generate_resource_dashboard import candidate_overall_progress
    assert candidate_overall_progress("DESIGN_ONLY_ACTIVE")[0] == 17
    assert candidate_overall_progress("SOURCE_FEASIBILITY_AND_DOWNSTREAM_GATES_COMPLETED")[0] == 33
    assert candidate_overall_progress("PIT_COMPLETED_NO_PERFORMANCE")[0] == 67
    assert candidate_overall_progress("unknown_state")[0] == 0


def test_candidate_milestone_progress_is_zero_without_active_workflow():
    from automation.generate_resource_dashboard import candidate_milestone_progress
    progress, basis = candidate_milestone_progress("Q218", [])
    assert progress == 0
    assert "not started" in basis


def test_dashboard_pipeline_is_locked_to_focus_candidates():
    from automation.generate_resource_dashboard import candidate_pipeline
    top4 = [
        {"code":"Q104:I19","state":"SOURCE_FEASIBILITY_AND_DOWNSTREAM_GATES_COMPLETED"},
        {"code":"Q218","state":"DESIGN_ONLY_ACTIVE"},
        {"code":"Q220","state":"DESIGN_ONLY_ACTIVE"},
        {"code":"Q221","state":"DESIGN_ONLY_ACTIVE"},
        {"code":"Q219","state":"DESIGN_ONLY_ACTIVE"},
    ]
    rows = candidate_pipeline(top4, [], {}, {})
    assert [x["code"] for x in rows] == ["Q104:I19","Q220","Q221"]


def test_dashboard_generator_bootstraps_repo_root_for_file_execution():
    root = Path(__file__).parents[1]
    generator = (root / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert "import sys" in generator
    assert "if str(ROOT) not in sys.path:" in generator
    assert "sys.path.insert(0, str(ROOT))" in generator


def test_chat_handoff_snapshot_uses_persisted_next_chat_decisions_and_safety():
    from automation.generate_resource_dashboard import chat_handoff_snapshot
    import json
    from pathlib import Path

    root = Path(__file__).parents[1]
    evidence = json.loads((root / "research/evidence/current_operational_state.json").read_text(encoding="utf-8"))
    os_state = json.loads((root / "ops/trading_agent_os_state.json").read_text(encoding="utf-8"))
    handoff = chat_handoff_snapshot(evidence, os_state)

    assert handoff["record_type"] == "dashboard_chat_handoff"
    assert handoff["active_execution_focus"] == ["Q104:I19", "Q220", "Q221"]
    assert handoff["next_research_focus"]
    assert "Q104:I19" in handoff["next_research_focus"]
    assert handoff["safety"]["PAPER_ONLY"] is True
    assert handoff["safety"]["LIVE_TRADING_ENABLED"] is False
    assert handoff["safety"]["ORDERS_ENABLED"] is False
    assert handoff["safety"]["AUTOMATIC_PROMOTION"] is False


def test_dashboard_focused_backlog_is_three_candidates():
    from automation.generate_resource_dashboard import planned_research_backlog
    rows = planned_research_backlog([
        {"code":"Q104:I19","lane":"FORMAL READINESS","next_gate":"13F completeness"},
        {"code":"Q218","lane":"FRONTIER DISCOVERY","next_gate":"archived SEC source/PIT"},
        {"code":"Q220","lane":"FRONTIER DISCOVERY","next_gate":"historical as-filed XBRL PIT compiler"},
        {"code":"Q221","lane":"FRONTIER DISCOVERY","next_gate":"historical USAspending public clock + issuer mapping"},
        {"code":"Q219","lane":"FRONTIER DISCOVERY","next_gate":"options PIT"},
    ])
    assert [x["candidate"] for x in rows] == ["Q104:I19","Q220","Q221"]
    assert [x["planned_status"] for x in rows] == [
        "READY_NEXT_GATE",
        "READY_NEXT_GATE",
        "READY_NEXT_GATE",
    ]
    assert "historical USAspending" in rows[2]["next_gate"]


def test_dashboard_s10_support_is_non_authorizing():
    from automation.generate_resource_dashboard import s10_support_snapshot
    payload = s10_support_snapshot([], {})
    assert payload["resource_id"] == "S10"
    assert payload["scientific_evidence"] is False
    assert payload["performance_authorization"] is False

def test_q220_blocked_population_receipt_is_not_masked_by_active_route_probe(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    receipt = {
        "candidate_id": "Q220",
        "mode": "population",
        "status": "Q220_AS_FILED_XBRL_POPULATION_BLOCKED",
        "failure_count": 0,
        "record_count": 55,
        "row_count": 55,
        "receipt_fingerprint": "a" * 64,
        "per_issuer_minimum_originals_and_textblock_ready": 5,
        "issuer_summary": {
            "AMP": {"original_10k_count": 7, "textblock_ready_originals": 4},
            "NDAQ": {"original_10k_count": 7, "textblock_ready_originals": 5},
        },
    }
    monkeypatch.setattr(dashboard, "read_json_file", lambda _path: receipt)

    result = dashboard.q220_as_filed_population_status([
        {
            "name": "Q220 As-Filed SEC-XBRL Population Repair",
            "path": ".github/workflows/q220-as-filed-xbrl-population.yml",
            "status": "pending",
        }
    ])

    assert result["state"] == "blocked"
    assert result["progress_percent"] == 0
    assert "AMP: 4/5 TextBlock-ready original 10-Ks" in result["detail"]
    assert "route probe does not clear" in result["detail"]
    assert result["active_route_probe"] is True
    assert "preserve the frozen minimum" in result["next_gate"]


def test_q218_development_index_includes_blocked_cost_adjusted_oos_gate():
    from automation.generate_resource_dashboard import candidate_progress_snapshot

    snapshot = candidate_progress_snapshot([])
    q218 = snapshot["candidates"]["Q218"]
    oos = next(
        item for item in q218["milestones"]
        if item["label"] == "Cost-adjusted independent OOS assessment"
    )

    assert oos["status"] == "blocked"
    assert oos["progress"] == 0
    assert "separate explicit authorization" in oos["detail"]
    assert q218["overall_progress_percent"] < 100
    assert q218["current_milestone_status"] == "blocked"




def test_q104_census_status_prefers_running_census_over_newer_pending_retry(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    monkeypatch.setattr(dashboard, "read_json_file", lambda _path: {})
    def jobs_for_run(run_id):
        if run_id == 101:
            return [
                {"name": "census (2023, hosted)", "status": "completed", "conclusion": "success"},
                {"name": "census (2021-2022, hosted)", "status": "in_progress", "conclusion": None},
            ]
        return []
    monkeypatch.setattr(dashboard, "jobs_for_run", jobs_for_run)
    result = dashboard.q104_census_status([
        {
            "id": 101,
            "name": "Q104 I19 Historical 13F Identity Census",
            "status": "in_progress",
            "created_at": "2026-10-10T10:00:00Z",
        },
        {
            "id": 202,
            "name": "Q104 I19 Historical 13F Identity Census",
            "status": "pending",
            "created_at": "2026-10-10T14:53:00Z",
        },
    ])
    assert result["state"] == "running"
    assert "1/6 Shards" in result["detail"]
    assert "Census-Run 101" in result["detail"]
    assert "202" in result["detail"]
    assert "wait behind the active run" in result["detail"]


def test_dashboard_does_not_count_queued_q104_retry_as_parallel_work(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    def jobs_for_run(run_id):
        if run_id == 101:
            return [{
                "name": "census (2021-2022, [\"ubuntu-24.04\"], hosted, ubuntu-24.04, 1)",
                "status": "in_progress",
                "runner_name": "ubuntu-24.04",
            }]
        return []
    monkeypatch.setattr(dashboard, "jobs_for_run", jobs_for_run)
    runs = [
        {
            "id": 101, "name": "Q104 I19 Historical 13F Identity Census",
            "status": "in_progress", "created_at": "2026-10-10T10:00:00Z",
        },
        {
            "id": 202, "name": "Q104 I19 Historical 13F Identity Census",
            "status": "pending", "created_at": "2026-10-10T14:53:00Z",
        },
    ]
    work = dashboard.current_work_from_runs(runs)
    q104_items = [x for x in work if x.get("task") == "Q104 I19 Historical 13F Identity Census"]
    assert len(q104_items) == 1
    assert q104_items[0]["run_id"] == 101


def test_q221_public_clock_does_not_claim_historical_applicability_without_a_durable_receipt(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    monkeypatch.setattr(dashboard, "read_json_file", lambda _path: {})
    gate = dashboard.q221_public_clock_status()

    assert gate["state"] == "ready"
    assert gate["progress_percent"] == 0
    assert "No positive, fingerprinted historical USAspending" in gate["detail"]
    assert gate["next_gate"].startswith("historical USAspending public boundary")



def test_q221_dashboard_only_closes_historical_policy_vintage_gate_with_fingerprinted_archive_receipt(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    receipt = {
        "record_type": "q221_historical_source_vintage_gate",
        "candidate_id": "Q221",
        "status": "Q221_HISTORICAL_POLICY_VINTAGES_RECONSTRUCTED",
        "historical_policy_vintages_reconstructed": True,
        "all_target_windows_covered": True,
        "policy_markers_consistent_across_vintages": True,
        "historical_applicability_proven": False,
        "award_level_public_boundary_proven": False,
        "lookahead_used": False,
        "receipt_fingerprint": "a" * 64,
        "capture_rows": [
            {"target_window": target, "status": "CAPTURE_PARSED"}
            for target in ("2025-01-01", "2025-07-01", "2026-01-01", "2026-07-01", "2026-10-05")
        ],
    }
    current = {
        "record_type": "q221_usaspending_public_clock_gate",
        "candidate_id": "Q221",
        "source_clock_contract_ready": True,
    }
    monkeypatch.setattr(
        dashboard,
        "read_json_file",
        lambda path: receipt if "q221_historical_source_vintages_latest.json" in path else current,
    )

    result = dashboard.q221_public_clock_status()
    assert result["state"] == "complete"
    assert result["progress_percent"] == 100
    assert "award-level public observability" in result["detail"]
    assert "award-level public-observation boundary" in result["next_gate"]
    assert result["parsed_target_windows"] == 5


def test_q221_dashboard_does_not_treat_live_source_smoke_as_historical_clock_proof(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    current = {
        "record_type": "q221_usaspending_public_clock_gate",
        "candidate_id": "Q221",
        "source_clock_contract_ready": True,
    }
    monkeypatch.setattr(dashboard, "read_json_file", lambda path: current if "q221_usaspending_public_clock_gate_latest.json" in path else {})

    result = dashboard.q221_public_clock_status()
    assert result["state"] == "ready"
    assert result["progress_percent"] == 0
    assert "cannot establish what was publicly observable historically" in result["detail"]
    assert result["next_gate"].startswith("historical USAspending public boundary")



def test_capacity_planner_ignores_candidate_names_in_active_maintenance_run_titles():
    from automation import generate_resource_dashboard as dashboard

    resources = [
        {"name": "Windows self-hosted A", "capacity_state": "available", "current_assignments": 0},
        {"name": "Windows self-hosted B", "capacity_state": "available", "current_assignments": 0},
        {"name": "Windows self-hosted C", "capacity_state": "available", "current_assignments": 0},
        {"name": "GitHub-hosted Ubuntu x64", "capacity_state": "available", "current_assignments": 0},
        {"name": "GitHub-hosted ARM64", "capacity_state": "available", "current_assignments": 0},
        {"name": "Free AI pool", "capacity_state": "available", "current_assignments": 0},
    ]
    active_maintenance = [{
        "id": 12345,
        "status": "in_progress",
        "name": "Planned Capacity Fast Dispatch",
        "display_title": "OPS: dispatch fresh receipt-defined Q220/Q221 capacity after status sync",
        "path": ".github/workflows/planned-capacity-fast-dispatch.yml",
    }]
    focused = [
        {"code": "Q104:I19", "next_gate": "historical 13F census"},
        {"code": "Q220", "next_gate": "historical SEC/XBRL PIT compiler"},
        {"code": "Q221", "next_gate": "historical USAspending policy-vintage gate"},
    ]

    plan = dashboard.planned_capacity_plan(resources, [], focused, {}, {}, recent_runs=active_maintenance)
    planned = [
        assignment
        for row in plan
        for assignment in row["planned_assignments"]
        if assignment.get("scheduled") and assignment.get("dispatchable")
    ]
    q221 = [item for item in planned if item.get("candidate") == "Q221"]
    assert len(q221) == 1
    assert q221[0]["plan_id"] == "Q221-USASPENDING-PUBLIC-CLOCK"
    assert next(row for row in plan if row["resource"] == "Windows self-hosted C")["planned_count"] == 1
    assert all(item.get("candidate") not in {"Q218", "Q219"} for item in planned)


def test_q221_positive_vintage_receipt_closes_this_workpack_until_award_boundary_workpack_exists(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    monkeypatch.setattr(
        dashboard,
        "q221_public_clock_status",
        lambda: {"state": "complete", "next_gate": "award-level public-observation boundary"},
    )
    resources = [{
        "name": "Windows self-hosted C",
        "capacity_state": "available",
        "current_assignments": 0,
        "research_capacity_slots": 1,
        "research_slots_free": 1,
    }]
    top3 = [
        {"code": "Q104:I19", "next_gate": "historical 13F census"},
        {"code": "Q220", "next_gate": "historical XBRL PIT compiler"},
        {"code": "Q221", "next_gate": "award-level public-observation boundary"},
    ]
    plan = dashboard.planned_capacity_plan(resources, [], top3, {}, {})
    q221 = [
        item for row in plan for item in row["planned_assignments"]
        if item.get("plan_id") == "Q221-USASPENDING-PUBLIC-CLOCK"
    ]
    assert len(q221) == 1
    assert q221[0]["dispatchable"] is False
    assert q221[0]["readiness"] == "COMPLETE_POLICY_VINTAGES_NEXT_GATE_NEEDS_NEW_WORKPACK"


def test_q221_open_vintage_gate_can_use_free_slot_despite_old_successful_run(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    monkeypatch.setattr(
        dashboard,
        "q221_public_clock_status",
        lambda: {"state": "ready", "progress_percent": 0, "next_gate": "historical USAspending policy vintages"},
    )
    resources = [{
        "name": "Windows self-hosted C",
        "capacity_state": "available",
        "current_assignments": 0,
        "research_capacity_slots": 1,
        "research_slots_free": 1,
    }]
    prior_success = [{
        "id": 789,
        "name": "Top-4 Slot windows Q221 all",
        "display_title": "Top-4 Slot windows Q221 all",
        "path": ".github/workflows/top4-candidate-slot-research.yml",
        "status": "completed",
        "conclusion": "success",
        "head_sha": "older-workpack-before-policy-vintage-gate",
    }]
    top3 = [
        {"code": "Q104:I19", "next_gate": "historical 13F census"},
        {"code": "Q220", "next_gate": "historical prefix/representation-gap PIT compiler"},
        {"code": "Q221", "next_gate": "historical USAspending policy vintages"},
    ]
    plan = dashboard.planned_capacity_plan(resources, [], top3, {}, {}, recent_runs=prior_success)
    q221 = [
        (row, item)
        for row in plan
        for item in row["planned_assignments"]
        if item.get("plan_id") == "Q221-USASPENDING-PUBLIC-CLOCK"
    ]
    assert len(q221) == 1
    row, item = q221[0]
    assert row["resource"] == "Windows self-hosted C"
    assert item["scheduled"] is True
    assert item["dispatchable"] is True
    assert item["dispatch_state"] == "READY_FOR_FAST_DISPATCH"
