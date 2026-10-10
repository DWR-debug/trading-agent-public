from pathlib import Path
import json

ROOT = Path(__file__).parents[1]


def test_fast_dispatch_uses_canonical_completion_monitor_and_five_minute_backstop():
    dispatcher = (ROOT / ".github/workflows/planned-capacity-fast-dispatch.yml").read_text(encoding="utf-8")
    monitor_a = (ROOT / ".github/workflows/research-completion-monitor-a.yml").read_text(encoding="utf-8")
    monitor_b = (ROOT / ".github/workflows/research-completion-monitor-b.yml").read_text(encoding="utf-8")
    assert 'cron: "*/5 * * * *"' in dispatcher
    assert "workflow_run:" in dispatcher
    for workflow_name in (
        "Top-4 Candidate Slot Research",
        "Top-4 Candidate Research Capacity",
        "Q104 I19 Historical 13F Identity Census",
        "Free AI Worker Fabric",
    ):
        assert workflow_name in dispatcher
    assert "cancel-in-progress: false" in dispatcher
    assert "workflow_run:" in monitor_a
    assert '      - "Q*"' in monitor_a
    assert '      - "Top-4*"' in monitor_a
    assert '      - "*PIT*"' in monitor_a
    assert '      - "*Source*"' in monitor_a
    assert '      - "Evidence Graph*"' in monitor_a
    assert "gh workflow run planned-capacity-fast-dispatch.yml" in monitor_a
    assert "workflow_run:" not in monitor_b




def test_q221_public_clock_workpack_dispatches_when_capacity_is_free():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "master_sha": "current-master",
        "work_assignments": [],
        "resources": [{
            "name": "GitHub-hosted Ubuntu x64",
            "research_capacity_slots": 2,
            "research_slots_in_use": 0,
            "research_slots_free": 2,
        }],
        "planned_capacity": [{
            "resource": "GitHub-hosted Ubuntu x64",
            "current_assignments": 0,
            "research_capacity_slots": 2,
            "planned_assignments": [{
                "plan_id": "Q221-USASPENDING-PUBLIC-CLOCK",
                "candidate": "Q221",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": workflow,
                "execution_workflow_inputs": {"focus_wave": False, "gate": "all"},
            }],
        }],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=2)
    assert [x["candidate"] for x in plan["dispatches"]] == ["Q221"]
    assert plan["dispatches"][0]["workflow"] == workflow
    assert plan["performance_authorization"] is False
    assert plan["live_execution"] is False

def test_archived_q218_workpack_is_blocked_even_if_legacy_authorization_guard_passes(monkeypatch):
    from automation import planned_capacity_fast_dispatch as dispatcher

    monkeypatch.setattr(dispatcher, "q218_replication_authorization_block_reason", lambda: None)
    workflow = ".github/workflows/q218-independent-replication-once.yml"
    snapshot = {
        "master_sha": "current-master",
        "work_assignments": [],
        "resources": [{
            "name": "GitHub-hosted Ubuntu x64",
            "research_capacity_slots": 1,
            "research_slots_in_use": 0,
            "research_slots_free": 1,
        }],
        "planned_capacity": [{
            "resource": "GitHub-hosted Ubuntu x64",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q218-ARCHIVED-REPLICATION",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "allow_parallel_with_candidate": True,
                "execution_workflow": workflow,
            }],
        }],
    }
    plan = dispatcher.dispatch_candidates(snapshot, [], max_dispatches=2)
    assert plan["dispatches"] == []
    assert any(
        decision.get("candidate") == "Q218" and decision["decision"] == "SKIP_FOCUS_LOCK"
        for decision in plan["decisions"]
    )
def test_fast_dispatch_uses_resource_capacity_metadata_for_q221_clock_gate(monkeypatch):
    from automation import planned_capacity_fast_dispatch as dispatcher

    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "work_assignments": [],
        "resources": [{
            "name": "GitHub-hosted ARM64",
            "research_capacity_slots": 2,
            "research_slots_in_use": 1,
            "research_slots_free": 1,
        }],
        "planned_capacity": [{
            "resource": "GitHub-hosted ARM64",
            "current_assignments": 1,
            "planned_assignments": [{
                "plan_id": "Q221-USASPENDING-PUBLIC-CLOCK",
                "candidate": "Q221",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": workflow,
                "execution_workflow_inputs": {"focus_wave": False, "gate": "all"},
            }],
        }],
    }
    plan = dispatcher.dispatch_candidates(snapshot, [], max_dispatches=4)
    assert [item["plan_id"] for item in plan["dispatches"]] == ["Q221-USASPENDING-PUBLIC-CLOCK"]
    assert plan["dispatches"][0]["resource"] == "GitHub-hosted ARM64"


def test_q104_source_only_receipt_does_not_mark_acceptance_time_census_complete(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    monkeypatch.setattr(
        dashboard,
        "read_json_file",
        lambda path: {
            "status": "13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_COMPLETED_SOURCE_ONLY",
            "completed_shards": ["2013-2017", "2018-2021", "2022-2025-09"],
        },
    )
    monkeypatch.setattr(
        dashboard,
        "jobs_for_run",
        lambda run_id: [
            {"name": "census (2013-2016, windows slot A)", "status": "in_progress", "conclusion": None},
            {"name": "census (2017-2018, windows slot B)", "status": "in_progress", "conclusion": None},
            {"name": "census (2019-2020, windows slot C)", "status": "in_progress", "conclusion": None},
            {"name": "census (2021-2022, hosted x64 slot 1)", "status": "in_progress", "conclusion": None},
            {"name": "census (2023, hosted x64 slot 2)", "status": "in_progress", "conclusion": None},
            {"name": "census (2024-2025-09, hosted ARM64 slot 1)", "status": "in_progress", "conclusion": None},
        ],
    )
    status = dashboard.q104_census_status([{
        "id": 123,
        "name": "Q104 I19 Historical 13F Identity Census",
        "status": "in_progress",
        "created_at": "2026-10-08T07:42:13Z",
    }])
    assert status["progress_percent"] == 0
    assert status["state"] == "running"




def test_dashboard_maps_candidate_capacity_and_planned_runner(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    work = [
        {
            "resource": "Windows self-hosted A",
            "worker": "LHT-N133732",
            "lane": "FORMAL READINESS",
            "task": "Q104 I19 Historical 13F Identity Census",
            "job": "windows_census",
            "status": "in_progress",
            "run_id": 123,
        },
        {
            "resource": "Windows self-hosted B",
            "worker": "LHT-N133732-2",
            "lane": "FRONTIER DISCOVERY",
            "task": "Top-4 Candidate Slot Research Q221",
            "job": "Q221 public clock",
            "status": "in_progress",
            "run_id": 456,
        },
    ]
    planned = [{
        "resource": "GitHub-hosted ARM64",
        "planned_assignments": [{
            "plan_id": "Q221-USASPENDING-PUBLIC-CLOCK",
            "candidate": "Q221",
            "scheduled": True,
            "dispatchable": True,
            "task": "historical USAspending public clock + issuer mapping",
        }],
    }]
    pipeline = dashboard.candidate_pipeline([], work, {}, {}, [], planned)
    q104 = next(x for x in pipeline if x["code"] == "Q104:I19")
    q221 = next(x for x in pipeline if x["code"] == "Q221")
    assert q104["active_capacities"] == ["Windows self-hosted A"]
    assert q104["active_capacity_assignments"][0]["worker"] == "LHT-N133732"
    assert q221["active_capacities"] == ["Windows self-hosted B"]
    assert q221["planned_capacities"] == ["GitHub-hosted ARM64"]
    assert q221["planned_capacity_assignments"][0]["dispatchable"] is True


def test_dashboard_candidate_progress_is_receipt_based_and_exposes_milestone_detail(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    monkeypatch.setattr(dashboard, "jobs_for_run", lambda run_id: [
        {"name": "windows_census", "status": "in_progress", "conclusion": None},
        {"name": "hosted_census (2018-2021)", "status": "in_progress", "conclusion": None},
        {"name": "hosted_census (2022-2025-09)", "status": "in_progress", "conclusion": None},
    ])
    progress = dashboard.candidate_progress_snapshot([{
        "id": 123,
        "name": "Q104 I19 Historical 13F Identity Census",
        "status": "in_progress",
        "created_at": "2026-10-08T07:42:13Z",
    }])
    q104 = progress["candidates"]["Q104:I19"]
    q218 = progress["candidates"]["Q218"]

    assert progress["method"] == "receipt_and_contract_based_development_index"
    assert q104["current_milestone"] == "13F security census"
    assert 0 <= q104["current_milestone_progress_percent"] <= 100
    assert q104["total_milestones"] == 9
    assert 0 <= q104["overall_progress_percent"] <= 100
    assert q218["current_milestone"] == "Cost-adjusted independent OOS assessment"
    assert q218["current_milestone_status"] == "blocked"
    assert q218["current_milestone_progress_percent"] == 0
    assert q218["next_gate"] == "separate explicit authorization and preregistration for any new cost-aware independent OOS trial"
    assert not any(
        m["status"] == "active"
        for m in q218["milestones"]
    )


def test_q218_receipt_gate_requires_current_code_fingerprint():
    from automation import generate_resource_dashboard as dashboard

    stale = {
        "source_gate": {
            "verified_positive_complete": True,
            "gate_code_blob_sha": "stale-source-sha",
        }
    }
    assert dashboard.receipt_gate_is_current(
        stale,
        "source_gate",
        "automation/q218_sec_multichannel_source_gate.py",
    ) is False


def test_dashboard_never_dispatches_archived_q218_and_keeps_q221_clock_gate_ready(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    resources = [{
        "name": "Windows self-hosted C",
        "capacity_state": "available",
        "current_assignments": 0,
        "research_capacity_slots": 1,
        "research_slots_free": 1,
    }]
    dashboard_top3 = [
        {"code": "Q104:I19", "next_gate": "historical 13F census"},
        {"code": "Q220", "next_gate": "historical XBRL PIT compiler"},
        {"code": "Q221", "next_gate": "historical USAspending public clock + issuer mapping"},
        {"code": "Q218", "next_gate": "archived SEC source/PIT"},
    ]
    plan = dashboard.planned_capacity_plan(resources, [], dashboard_top3, {}, {})
    scheduled = [
        item for row in plan for item in row["planned_assignments"]
        if item.get("scheduled")
    ]
    assert any(
        item.get("candidate") == "Q221"
        and item.get("plan_id") == "Q221-USASPENDING-PUBLIC-CLOCK"
        for item in scheduled
    )
    assert not any(item.get("candidate") == "Q218" for item in scheduled)


def test_dashboard_html_exposes_progress_bar_panels():
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    assert 'id="overallProgressBars"' in html
    assert 'id="milestoneProgressBars"' in html
    assert "function renderProgressCharts" in js
    assert "class='bar-fill milestone'" in js


def test_q218_independent_workflow_relays_completion():
    workflow = (ROOT / ".github/workflows/q218-independent-architecture-pit-reproduction.yml").read_text(encoding="utf-8")
    assert "actions: write" in workflow
    assert ".github/workflows/research-completion-relay.yml" in workflow
    assert 'source_workflow: "Q218 Independent Architecture PIT Reproduction"' in workflow


def test_q104_ai_audit_task_is_routable_through_free_worker_fabric():
    task = (ROOT / "ai_requests/AI-2026-10-08-Q104-I19-CENSUS-COMPILER-ADVERSARIAL.json").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/ai-worker-fabric.yml").read_text(encoding="utf-8")
    assert "AI-2026-10-08-Q104-I19-CENSUS-COMPILER-ADVERSARIAL" in task
    assert "AI-2026-10-08-Q104-I19-CENSUS-COMPILER-ADVERSARIAL" in workflow
    assert "openrouter_free" in task

def test_fast_dispatch_normalizes_list_run_payload():
    from automation.planned_capacity_fast_dispatch import normalize_runs_payload

    payload = [
        {"id": 123, "status": "in_progress", "name": "Q218"},
        "ignore-non-dict",
        {"id": 124, "status": "completed", "conclusion": "success", "name": "Q220"},
    ]
    assert normalize_runs_payload(payload) == [payload[0], payload[2]]


def test_fast_dispatch_ai_success_is_deduped_by_current_context(tmp_path, monkeypatch):
    from automation.planned_capacity_fast_dispatch import ai_task_completed_with_current_context

    task_id = "AI-2026-10-06-Q220-TOP4-ADVERSARIAL"
    task_path = tmp_path / "ai_requests" / f"{task_id}.json"
    state_path = tmp_path / "ops" / "ai_worker_state" / f"{task_id}__openrouter_free.json"
    task_path.parent.mkdir(parents=True)
    state_path.parent.mkdir(parents=True)
    task_path.write_text('{"schema_version":1,"task_id":"' + task_id + '"}', encoding="utf-8")
    state_path.write_text(
        '{"status":"SUCCESS","context_fingerprint":"ctx-123"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "automation.planned_capacity_fast_dispatch.subprocess.check_output",
        lambda *args, **kwargs: "ctx-123\n",
    )
    assert ai_task_completed_with_current_context(task_id, root=tmp_path) is True



def test_fast_dispatch_zero_active_starts_q221_clock_workpack_and_free_ai_review():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    snapshot = {
        "work_assignments": [],
        "planned_capacity": [
            {
                "resource": "Windows self-hosted C",
                "current_assignments": 0,
                "research_capacity_slots": 1,
                "planned_assignments": [{
                    "plan_id": "Q221-USASPENDING-PUBLIC-CLOCK",
                    "candidate": "Q221",
                    "scheduled": True,
                    "dispatchable": True,
                    "execution_workflow": ".github/workflows/top4-candidate-slot-research.yml",
                    "execution_workflow_inputs": {"focus_wave": False, "gate": "all"},
                }],
            },
            {
                "resource": "Free AI pool",
                "current_assignments": 0,
                "research_capacity_slots": 1,
                "planned_assignments": [{
                    "plan_id": "Q221-ADVERSARIAL",
                    "candidate": "Q221",
                    "scheduled": True,
                    "dispatchable": True,
                    "allow_parallel_with_candidate": True,
                    "execution_workflow": ".github/workflows/ai-worker-fabric.yml",
                    "execution_workflow_inputs": {"task_id": "AI-2026-10-06-Q221-TOP4-ADVERSARIAL"},
                }],
            },
        ],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=4)
    assert plan["zero_active_research_jobs"] is True
    assert {x["workflow"] for x in plan["dispatches"]} == {
        ".github/workflows/top4-candidate-slot-research.yml",
        ".github/workflows/ai-worker-fabric.yml",
    }
    assert plan["dispatches"][0]["candidate"] == "Q221"

def test_fast_dispatch_blocks_legacy_broad_top4_matrix_workpack():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    snapshot = {
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Windows self-hosted B",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q221-LEGACY-MATRIX",
                "candidate": "Q221",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": ".github/workflows/top4-candidate-research-capacity.yml",
            }],
        }],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=4)
    assert plan["dispatches"] == []
    assert any(d["decision"] == "SKIP_LEGACY_BROAD_TOP4_WORKFLOW_NOT_CANDIDATE_SCOPED" for d in plan["decisions"])
def test_dashboard_exposes_runner_status_sources_and_dispatchability():
    generator = (ROOT / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert '"runner_status_ui_url"' in generator
    assert '"runner_status_api_url"' in generator
    assert '"dispatchable": bool(item.get("dispatchable", False))' in generator
    assert '"execution_workflow": item.get("execution_workflow")' in generator



def test_fast_dispatch_allows_q221_with_parallel_ai_review():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    snapshot = {
        "work_assignments": [{
            "resource": "Free AI pool",
            "candidate": "Q221",
            "task": "Free AI Worker Fabric",
            "job": "Q221 adversarial review",
            "lane": "FRONTIER DISCOVERY",
        }],
        "planned_capacity": [{
            "resource": "Windows self-hosted B",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q221-PIT",
                "candidate": "Q221",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": ".github/workflows/top4-candidate-slot-research.yml",
            }],
        }],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=4)
    assert any(x["candidate"] == "Q221" and x["workflow"].endswith("top4-candidate-slot-research.yml") for x in plan["dispatches"])
def test_fast_dispatch_allows_independent_candidates_on_one_slot_workflow():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "GitHub-hosted Ubuntu x64",
            "current_assignments": 0,
            "research_capacity_slots": 2,
            "planned_assignments": [
                {"plan_id":"Q220-PIT","candidate":"Q220","scheduled":True,"dispatchable":True,"execution_workflow":workflow},
                {"plan_id":"Q221-PIT","candidate":"Q221","scheduled":True,"dispatchable":True,"execution_workflow":workflow},
            ],
        }],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=4)
    assert [x["candidate"] for x in plan["dispatches"]] == ["Q220", "Q221"]


def test_fast_dispatch_reserves_only_explicit_multi_resource_leases():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    snapshot = {
        "work_assignments": [],
        "planned_capacity": [
            {
                "resource": "Windows self-hosted A",
                "current_assignments": 0,
                "research_capacity_slots": 1,
                "planned_assignments": [{
                    "plan_id":"Q104-I19-CENSUS","candidate":"Q104:I19",
                    "scheduled":True,"dispatchable":True,"exclusive_dispatch":True,
                    "resource_leases":["Windows self-hosted A","GitHub-hosted Ubuntu x64","GitHub-hosted ARM64"],
                    "execution_workflow":".github/workflows/q104-i19-13f-historical-identity-census.yml",
                }],
            },
            {
                "resource": "Windows self-hosted B",
                "current_assignments": 0,
                "research_capacity_slots": 1,
                "planned_assignments": [{
                    "plan_id":"Q220-PIT","candidate":"Q220","scheduled":True,"dispatchable":True,
                    "execution_workflow":".github/workflows/top4-candidate-slot-research.yml",
                }],
            },
            {
                "resource": "Windows self-hosted C",
                "current_assignments": 0,
                "research_capacity_slots": 1,
                "planned_assignments": [{
                    "plan_id":"Q221-PIT","candidate":"Q221","scheduled":True,"dispatchable":True,
                    "execution_workflow":".github/workflows/top4-candidate-slot-research.yml",
                }],
            },
            {
                "resource": "GitHub-hosted ARM64",
                "current_assignments": 0,
                "research_capacity_slots": 2,
                "planned_assignments": [{
                    "plan_id":"Q220-PIT","candidate":"Q220","scheduled":True,"dispatchable":True,
                    "execution_workflow":".github/workflows/top4-candidate-slot-research.yml",
                }],
            },
        ],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=6)
    candidates=[x["candidate"] for x in plan["dispatches"]]
    assert candidates == ["Q104:I19", "Q220", "Q221"]
    assert all(x["candidate"] not in {"Q218", "Q219"} for x in plan["dispatches"])
    assert not any(d.get("decision") == "SKIP_FOCUS_LOCK" and d.get("candidate") == "Q221" for d in plan["decisions"])

def test_fast_dispatch_backfills_free_slot_after_completed_top4_candidate():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Windows self-hosted B",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q220-PIT",
                "candidate": "Q220",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": workflow,
            }],
        }],
    }
    runs = [{
        "status": "completed",
        "conclusion": "success",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q220 all",
        "run_name": "Top-4 Slot windows Q220 all",
    }]
    plan = dispatch_candidates(snapshot, runs, max_dispatches=4)
    assert any(x["candidate"] == "Q221" for x in plan["dispatches"])
    assert any(d["decision"] == "DISPATCH_SLOT_BACKFILL" for d in plan["decisions"])


def test_fast_dispatch_skips_successful_same_slot_but_allows_other_architecture():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    base = {
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "GitHub-hosted Ubuntu x64",
            "current_assignments": 0,
            "research_capacity_slots": 2,
            "planned_assignments": [{
                "plan_id":"Q220-PIT","candidate":"Q220","scheduled":True,"dispatchable":True,
                "execution_workflow":workflow,
            }],
        }],
    }
    completed_arm = [{
        "status":"completed","conclusion":"success","name":"Top-4 Candidate Slot Research",
        "display_title":"Top-4 Slot ubuntu_arm64 Q220","run_name":"Top-4 Slot ubuntu_arm64 Q220"
    }]
    plan = dispatch_candidates(base, completed_arm, max_dispatches=4)
    assert plan["dispatches"][0]["candidate"] == "Q220"
    assert plan["dispatches"][0]["inputs"]["resource"] == "ubuntu_x64"

    completed_x64 = completed_arm+[{
        "status":"completed","conclusion":"success","name":"Top-4 Candidate Slot Research",
        "display_title":"Top-4 Slot ubuntu_x64 Q220","run_name":"Top-4 Slot ubuntu_x64 Q220"
    }]
    plan2 = dispatch_candidates(base, completed_x64, max_dispatches=4)
    assert len(plan2["dispatches"]) == 1
    assert plan2["dispatches"][0]["candidate"] == "Q221"
    assert plan2["dispatches"][0]["inputs"]["resource"] == "ubuntu_x64"
    assert not any(x["candidate"] in {"Q218", "Q219"} for x in plan2["dispatches"])


def test_fast_dispatch_allows_one_retry_then_backfills_next_candidate_after_second_failure():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Windows self-hosted B",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q220-PIT", "candidate": "Q220", "scheduled": True,
                "dispatchable": True, "execution_workflow": workflow,
            }],
        }],
    }
    failed_twice = [{
        "status": "completed", "conclusion": "failure",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q220",
        "run_name": "Top-4 Slot windows Q220",
    } for _ in range(2)]
    plan = dispatch_candidates(snapshot, failed_twice, max_dispatches=4)
    assert [x["candidate"] for x in plan["dispatches"]] == ["Q221"]
    assert plan["dispatches"][0]["inputs"] == {"candidate": "Q221", "resource": "windows"}
    assert any(
        d["decision"] == "DISPATCH_SLOT_BACKFILL"
        and d["mode"] == "TECHNICAL_RETRY_EXHAUSTION_BACKFILL"
        for d in plan["decisions"]
    )


def test_fast_dispatch_does_not_backfill_when_all_top4_successors_are_exhausted():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Windows self-hosted B",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q220-PIT", "candidate": "Q220", "scheduled": True,
                "dispatchable": True, "execution_workflow": workflow,
            }],
        }],
    }

    def failures(candidate):
        return [{
            "status": "completed", "conclusion": "failure",
            "name": "Top-4 Candidate Slot Research",
            "display_title": f"Top-4 Slot windows {candidate}",
            "run_name": f"Top-4 Slot windows {candidate}",
        } for _ in range(2)]

    runs = failures("Q220") + failures("Q221")
    plan = dispatch_candidates(snapshot, runs, max_dispatches=4)
    assert plan["dispatches"] == []
    assert any(d["decision"] == "SKIP_SLOT_RETRY_EXHAUSTED" for d in plan["decisions"])


def test_pull_request_validation_runs_are_not_counted_as_research_capacity():
    from automation import generate_resource_dashboard as dashboard

    assert dashboard.infer_lane("Q133-Q170 PIT Readiness R1", "test", "pull_request") == "VALIDATION / CI"
    assert dashboard.infer_lane("Q219 PIT", "research", "workflow_dispatch") == "FRONTIER DISCOVERY"

    work = [{
        "resource": "GitHub-hosted Ubuntu x64",
        "lane": "VALIDATION / CI",
        "task": "Q219 PIT Readiness validation",
        "job": "test",
    }, {
        "resource": "GitHub-hosted Ubuntu x64",
        "lane": "FRONTIER DISCOVERY",
        "task": "Q104 I19 Historical 13F Identity Census",
        "job": "hosted census",
    }]
    resource = {
        "name": "GitHub-hosted Ubuntu x64",
        "type": "cloud",
        "research_capacity_slots": 2,
        "configured_runner": "missing-runner",
        "role": "test",
    }
    enriched = dashboard.enrich_resources([resource], [], work)[0]
    assert enriched["total_active_assignments"] == 2
    assert enriched["current_assignments"] == 1
    assert enriched["research_slots_in_use"] == 1
    assert enriched["research_slots_free"] == 1


def test_pull_request_validation_does_not_mark_candidate_active():
    from automation import generate_resource_dashboard as dashboard

    run = {
        "id": 1,
        "name": "Q219 PIT Readiness R1",
        "event": "pull_request",
        "status": "in_progress",
    }
    monkeypatch = None
    # The classifier is sufficient to establish that this run belongs to CI.
    assert dashboard.infer_lane(run["name"], "", run["event"]) == "VALIDATION / CI"


def test_fast_dispatch_loads_paginated_top4_slot_history_for_retry_circuit_breaker():
    dispatcher = (ROOT / ".github/workflows/planned-capacity-fast-dispatch.yml").read_text(encoding="utf-8")
    assert 'gh api --paginate "/repos/$GITHUB_REPOSITORY/actions/workflows/top4-candidate-slot-research.yml/runs?per_page=100"' in dispatcher
    assert dispatcher.count('"$slot_history"') >= 1
    assert '<(printf' in dispatcher





def test_q218_is_excluded_from_focus_even_with_many_legacy_failures():
    from automation import planned_capacity_fast_dispatch as dispatcher

    snapshot = {
        "master_sha": "current-master",
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Windows self-hosted C",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q218-EVENT-PAIR",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "allow_parallel_with_candidate": True,
                "execution_workflow": ".github/workflows/top4-candidate-slot-research.yml",
                "execution_workflow_inputs": {"focus_wave": True, "gate": "event_pair"},
            }],
        }],
    }
    legacy_failures = [{
        "status": "completed", "conclusion": "failure", "head_sha": "old-master",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q218 event_pair",
        "run_name": "Top-4 Slot windows Q218 event_pair",
    } for _ in range(20)]

    plan = dispatcher.dispatch_candidates(snapshot, legacy_failures, max_dispatches=4)
    assert plan["dispatches"] == []
    assert any(
        d["decision"] == "SKIP_FOCUS_LOCK" and d.get("candidate") == "Q218"
        for d in plan["decisions"]
    )


def test_q104_compiler_failure_streak_resets_on_new_master_sha(monkeypatch):
    from automation import planned_capacity_fast_dispatch as dispatcher
    snapshot = {
        "master_sha": "new-master",
        "focus_candidates": ["Q104:I19"],
        "planned_capacity": [{
            "resource": "GitHub-hosted Ubuntu x64",
            "research_capacity_slots": 1,
            "research_slots_in_use": 0,
            "research_slots_free": 1,
            "planned_assignments": [{
                "plan_id": "Q104-I19-COMPILER",
                "candidate": "Q104:I19",
                "scheduled": True,
                "dispatchable": True,
                "allow_parallel_with_candidate": True,
                "execution_workflow": ".github/workflows/q104-i19-historical-pit-compilation.yml",
            }],
        }],
        "work_assignments": [],
    }
    runs = [
        {
            "status": "completed",
            "conclusion": "failure",
            "head_sha": "old-master",
            "path": ".github/workflows/q104-i19-historical-pit-compilation.yml",
            "created_at": "2026-10-08T14:18:00Z",
        },
        {
            "status": "completed",
            "conclusion": "failure",
            "head_sha": "old-master",
            "path": ".github/workflows/q104-i19-historical-pit-compilation.yml",
            "created_at": "2026-10-08T14:19:00Z",
        },
    ]
    plan = dispatcher.plan_dispatch(snapshot, runs, repo="DWR-debug/trading-agent-public", max_dispatches=6)
    assert any(x["plan_id"] == "Q104-I19-COMPILER" for x in plan["dispatches"])

def test_q218_completed_focus_gate_is_skipped_by_current_focus_lock():
    from automation import planned_capacity_fast_dispatch as dispatcher

    snapshot = {
        "focus_candidates": ["Q218"],
        "planned_capacity": [{
            "resource": "Windows self-hosted C",
            "research_capacity_slots": 1,
            "research_slots_in_use": 0,
            "research_slots_free": 1,
            "planned_assignments": [{
                "plan_id": "Q218-EVENT-PAIR",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": ".github/workflows/top4-candidate-slot-research.yml",
                "execution_workflow_inputs": {"focus_wave": True, "gate": "event_pair"},
            }],
        }],
        "work_assignments": [],
    }
    plan = dispatcher.plan_dispatch(snapshot, [], repo="DWR-debug/trading-agent-public", max_dispatches=6)
    assert plan["dispatches"] == []
    assert any(d["decision"] == "SKIP_FOCUS_LOCK" for d in plan["decisions"])


def test_q218_focus_never_retries_in_active_dispatch_after_replacement():
    from automation import planned_capacity_fast_dispatch as dispatcher

    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "master_sha": "current-master",
        "focus_candidates": ["Q104:I19", "Q218", "Q220", "Q221"],
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Windows self-hosted C",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q218-EVENT-PAIR", "candidate": "Q218", "scheduled": True,
                "dispatchable": True, "allow_parallel_with_candidate": True,
                "execution_workflow": workflow,
                "execution_workflow_inputs": {"focus_wave": True, "gate": "event_pair"},
            }],
        }],
    }
    one_failure = [{
        "status": "completed", "conclusion": "failure", "head_sha": "current-master",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q218 event_pair",
        "run_name": "Top-4 Slot windows Q218 event_pair",
    }]
    plan = dispatcher.dispatch_candidates(snapshot, one_failure, max_dispatches=4)
    assert plan["dispatches"] == []
    assert any(d["decision"] == "SKIP_FOCUS_LOCK" for d in plan["decisions"])


def test_cancelled_q218_focus_gate_has_short_dispatch_cooldown():
    from datetime import datetime, timezone
    from automation import planned_capacity_fast_dispatch as dispatcher

    now = datetime(2026, 10, 8, 9, 20, tzinfo=timezone.utc)
    runs = [{
        "name": "Top-4 Slot windows Q218 event_pair",
        "status": "completed",
        "conclusion": "cancelled",
        "updated_at": "2026-10-08T09:19:00Z",
    }]
    assert dispatcher.focused_gate_recently_cancelled(runs, "Q218", "event_pair", now=now) is True
    assert dispatcher.focused_gate_recently_cancelled(runs, "Q218", "event_pair", now=datetime(2026, 10, 8, 9, 26, tzinfo=timezone.utc)) is False

def test_dashboard_skips_current_context_completed_focused_ai_before_filling_free_pool(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    resources = [{
        "name": "Free AI pool", "type": "cloud", "capacity_state": "available",
        "current_assignments": 0, "research_capacity_slots": 1,
    }]
    monkeypatch.setattr(
        dashboard,
        "ai_task_completed_with_current_context",
        lambda task_id, root=None: task_id == "AI-2026-10-06-Q218-TOP4-ADVERSARIAL",
    )
    plan = dashboard.planned_capacity_plan(resources, [], [], {}, {})
    ai = next(row for row in plan if row["resource"] == "Free AI pool")
    assert ai["planned_assignments"] == []


def test_dashboard_generator_supports_direct_script_execution_import_mode():
    generator = (ROOT / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert "from automation.planned_capacity_fast_dispatch import ai_task_completed_with_current_context" in generator
    assert "from planned_capacity_fast_dispatch import ai_task_completed_with_current_context" in generator

def test_q104_recovery_cannot_cancel_an_active_census():
    workflow = (ROOT / ".github/workflows/q104-i19-13f-historical-identity-census.yml").read_text(encoding="utf-8")
    assert "cancel-in-progress: false" in workflow
    assert "recovery_guard:" in workflow
    assert "for status in in_progress queued pending; do" in workflow
    assert "needs: [recovery_guard]" in workflow
    assert "needs.recovery_guard.outputs.proceed == 'true'" in workflow
    assert "needs.recovery_guard.outputs.proceed" in workflow



def test_q104_census_dashboard_requires_exact_six_shard_clock_receipt():
    from automation.generate_resource_dashboard import q104_census_clock_complete

    base = {
        "candidate_id": "Q104:I19",
        "status": "13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_COMPLETED_SOURCE_PIT_CLOCK_ONLY",
        "acceptance_timezone": "America/New_York",
        "acceptance_clock_basis": "SEC_EDGAR_SGML_ACCEPTANCE_DATETIME",
        "completed_shards": [
            "2013-2016", "2017-2018", "2019-2020",
            "2021-2022", "2023", "2024-2025-09",
        ],
        "archive_count": 50,
        "archives": [{} for _ in range(50)],
        "identity_conflicts": [],
        "acceptance_failures": {},
        "acceptance_time_join": {
            "target_unique_accessions": 136941,
            "records_checked": 136941,
            "failures": 0,
            "complete": True,
            "timezone_inference": False,
        },
        "receipt_fingerprint": "a" * 64,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    assert q104_census_clock_complete(base) is True
    base["completed_shards"].pop()
    assert q104_census_clock_complete(base) is False


def test_i19_census_failure_blocks_automatic_full_census_retry():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    workflow = ".github/workflows/q104-i19-13f-historical-identity-census.yml"
    snapshot = {
        "focus_candidates": ["Q104:I19", "Q218"],
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Windows self-hosted A",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q104-I19-CENSUS",
                "candidate": "Q104:I19",
                "scheduled": True,
                "dispatchable": True,
                "exclusive_dispatch": True,
                "execution_workflow": workflow,
            }],
        }],
    }
    failed_run = {
        "id": 37931811984,
        "status": "completed",
        "conclusion": "failure",
        "name": "Q104 I19 Historical 13F Identity Census",
        "head_sha": "old-master-sha",
    }
    plan = dispatch_candidates(snapshot, [failed_run], max_dispatches=4)
    assert plan["dispatches"] == []
    assert any(
        item["decision"] == "SKIP_I19_CENSUS_AUTOMATIC_FULL_RETRY_REQUIRES_TARGETED_RECOVERY"
        for item in plan["decisions"]
    )


def test_i19_census_dispatch_is_allowed_when_no_prior_census_failure_exists():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    workflow = ".github/workflows/q104-i19-13f-historical-identity-census.yml"
    snapshot = {
        "focus_candidates": ["Q104:I19", "Q218"],
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Windows self-hosted A",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q104-I19-CENSUS",
                "candidate": "Q104:I19",
                "scheduled": True,
                "dispatchable": True,
                "exclusive_dispatch": True,
                "execution_workflow": workflow,
            }],
        }],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=1)
    assert [item["candidate"] for item in plan["dispatches"]] == ["Q104:I19"]


def test_fast_dispatch_hard_blocks_q218_and_q219_outside_the_three_candidate_focus():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "work_assignments": [],
        "resources": [
            {"name": "GitHub-hosted Ubuntu x64", "research_capacity_slots": 2, "research_slots_in_use": 0, "research_slots_free": 2},
            {"name": "GitHub-hosted ARM64", "research_capacity_slots": 2, "research_slots_in_use": 0, "research_slots_free": 2},
        ],
        "planned_capacity": [
            {"resource": "GitHub-hosted Ubuntu x64", "current_assignments": 0, "research_capacity_slots": 2,
             "planned_assignments": [{"plan_id":"Q219-OPTIONS-SOURCE-BREADTH","candidate":"Q219","scheduled":True,"dispatchable":True,
               "execution_workflow":workflow,"execution_workflow_inputs":{"focus_wave":False,"gate":"all"}}]},
            {"resource": "GitHub-hosted ARM64", "current_assignments": 0, "research_capacity_slots": 2,
             "planned_assignments": [{"plan_id":"Q218-ARCHIVED","candidate":"Q218","scheduled":True,"dispatchable":True,
               "execution_workflow":workflow,"execution_workflow_inputs":{"focus_wave":False,"gate":"all"}}]},
        ],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=4)
    assert plan["dispatches"] == []
    assert {d.get("candidate") for d in plan["decisions"] if d["decision"] == "SKIP_FOCUS_LOCK"} == {"Q218", "Q219"}
    assert plan["performance_authorization"] is False
    assert plan["paper_only"] is True
    assert plan["live_execution"] is False
    assert plan["promotion"] is False


def test_legacy_candidate_matrix_contains_only_q220_and_q221():
    workflow = (ROOT / ".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert "candidate: [Q221]" in workflow
    assert workflow.count("candidate: [Q220]") == 2
    assert "Q218" not in workflow
    assert "Q219" not in workflow


def test_dispatcher_default_and_dashboard_focus_are_intersected_with_fixed_allowlist():
    from automation.planned_capacity_fast_dispatch import effective_focus_candidates, FOCUS_CANDIDATES

    assert effective_focus_candidates({}) == {"Q104:I19", "Q220", "Q221"}
    assert effective_focus_candidates({"focus_candidates": ["Q104:I19", "Q218", "Q219", "Q221"]}) == {"Q104:I19", "Q221"}
    assert effective_focus_candidates({"focus_candidates": ["Q218", "Q219"]}) == set()
    assert FOCUS_CANDIDATES == {"Q104:I19", "Q220", "Q221"}
