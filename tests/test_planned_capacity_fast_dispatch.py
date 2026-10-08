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



def test_fast_dispatch_uses_resource_capacity_metadata_when_plan_row_omits_capacity(monkeypatch):
    import automation.planned_capacity_fast_dispatch as dispatcher

    workflow = ".github/workflows/q218-independent-architecture-pit-reproduction.yml"
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
                "plan_id": "Q218-INDEPENDENT-ARCH",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "allow_parallel_with_candidate": True,
                "execution_workflow": workflow,
            }],
        }],
    }
    monkeypatch.setattr(
        dispatcher,
        "completed_q218_gates_for_current_context",
        lambda runs: {"source", "event_pair"},
    )
    monkeypatch.setattr(
        dispatcher,
        "q218_independent_reproduction_current",
        lambda runs: False,
    )

    plan = dispatcher.dispatch_candidates(snapshot, [], max_dispatches=4)
    assert [item["plan_id"] for item in plan["dispatches"]] == ["Q218-INDEPENDENT-ARCH"]
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
            {"name": "windows_census", "status": "in_progress", "conclusion": None},
            {"name": "hosted_census (2018-2021)", "status": "in_progress", "conclusion": None},
            {"name": "hosted_census (2022-2025-09)", "status": "in_progress", "conclusion": None},
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
            "task": "Top-4 Candidate Slot Research Q218",
            "job": "Q218 source",
            "status": "in_progress",
            "run_id": 456,
        },
    ]
    planned = [{
        "resource": "GitHub-hosted ARM64",
        "planned_assignments": [{
            "plan_id": "Q218-INDEPENDENT-ARCH",
            "candidate": "Q218",
            "scheduled": True,
            "dispatchable": True,
            "task": "independent architecture PIT reproduction",
        }],
    }]
    pipeline = dashboard.candidate_pipeline([], work, {}, {}, [], planned)
    q104 = next(x for x in pipeline if x["code"] == "Q104:I19")
    q218 = next(x for x in pipeline if x["code"] == "Q218")
    assert q104["active_capacities"] == ["Windows self-hosted A"]
    assert q104["active_capacity_assignments"][0]["worker"] == "LHT-N133732"
    assert q218["active_capacities"] == ["Windows self-hosted B"]
    assert q218["planned_capacities"] == ["GitHub-hosted ARM64"]
    assert q218["planned_capacity_assignments"][0]["dispatchable"] is True

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
    assert q218["current_milestone"] == "Preregistration + authorization reconcile"
    assert q218["current_milestone_status"] == "completed"
    assert q218["current_milestone_progress_percent"] == 100
    assert any(m["label"] == "Preregistration + authorization reconcile" and m["status"] == "completed" for m in q218["milestones"])


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


def test_dashboard_q218_completed_source_event_pair_exposes_independent_arch_queue(monkeypatch):
    from automation import generate_resource_dashboard as dashboard
    resources = [{
        "name": "GitHub-hosted ARM64",
        "capacity_state": "available",
        "current_assignments": 0,
    }]
    dashboard_top4 = [{
        "code": "Q218",
        "next_gate": "independent architecture PIT reproduction",
    }]
    monkeypatch.setattr(dashboard, "q218_receipt_state", lambda: {
        "source_complete": True,
        "event_pair_complete": True,
        "independent_complete": False,
    })
    plan = dashboard.planned_capacity_plan(resources, [], dashboard_top4, {}, {})
    rows = [item for row in plan for item in row["planned_assignments"] if item.get("scheduled")]
    assert any(item["plan_id"] == "Q218-INDEPENDENT-ARCH" for item in rows)
    assert all(item["plan_id"] not in {"Q218-SOURCE", "Q218-EVENT-PAIR"} for item in rows)


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


def test_fast_dispatch_zero_active_starts_top4_once_and_ai_when_free():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    snapshot = {
        "work_assignments": [],
        "planned_capacity": [
            {
                "resource": "Windows self-hosted B",
                "current_assignments": 0,
                "research_capacity_slots": 1,
                "planned_assignments": [{
                    "plan_id": "Q218-PIT",
                    "candidate": "Q218",
                    "scheduled": True,
                    "dispatchable": True,
                    "execution_workflow": ".github/workflows/top4-candidate-research-capacity.yml",
                }],
            },
            {
                "resource": "Free AI pool",
                "current_assignments": 0,
                "research_capacity_slots": 1,
                "planned_assignments": [{
                    "plan_id": "Q218-ADVERSARIAL",
                    "candidate": "Q218",
                    "scheduled": True,
                    "dispatchable": True,
                    "allow_parallel_with_candidate": True,
                    "execution_workflow": ".github/workflows/ai-worker-fabric.yml",
                    "execution_workflow_inputs": {"task_id": "AI-TEST-Q218-TOP4-ADVERSARIAL-UNSEEN"},
                }],
            },
        ],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=4)
    assert plan["zero_active_research_jobs"] is True
    assert set(x["workflow"] for x in plan["dispatches"]) == {
        ".github/workflows/top4-candidate-research-capacity.yml",
        ".github/workflows/ai-worker-fabric.yml",
    }
    assert plan["dispatches"][0]["workflow"].endswith("top4-candidate-research-capacity.yml")


def test_fast_dispatch_does_not_duplicate_active_top4_candidate():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    snapshot = {
        "work_assignments": [{
            "candidate": "Q220",
            "task": "Top-4 Candidate Research Capacity",
            "job": "Windows Top-4 Q220",
            "lane": "FRONTIER DISCOVERY",
        }],
        "planned_capacity": [{
            "resource": "Windows self-hosted B",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q218-PIT",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": ".github/workflows/top4-candidate-research-capacity.yml",
            }],
        }],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=4)
    assert plan["dispatches"] == []


def test_dashboard_exposes_runner_status_sources_and_dispatchability():
    generator = (ROOT / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert '"runner_status_ui_url"' in generator
    assert '"runner_status_api_url"' in generator
    assert '"dispatchable": bool(item.get("dispatchable", False))' in generator
    assert '"execution_workflow": item.get("execution_workflow")' in generator


def test_fast_dispatch_allows_top4_with_parallel_ai_review():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    snapshot = {
        "work_assignments": [{
            "resource": "Free AI pool",
            "candidate": "Q218",
            "task": "Free AI Worker Fabric",
            "job": "Q218 adversarial review",
            "lane": "FRONTIER DISCOVERY",
        }],
        "planned_capacity": [{
            "resource": "Windows self-hosted B",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q218-PIT",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": ".github/workflows/top4-candidate-research-capacity.yml",
            }],
        }],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=4)
    assert plan["dispatches"][0]["workflow"].endswith("top4-candidate-research-capacity.yml")


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
                {"plan_id":"Q218-PIT","candidate":"Q218","scheduled":True,"dispatchable":True,"execution_workflow":workflow},
                {"plan_id":"Q219-PIT","candidate":"Q219","scheduled":True,"dispatchable":True,"execution_workflow":workflow},
            ],
        }],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=4)
    assert [x["candidate"] for x in plan["dispatches"]] == ["Q218", "Q219"]


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
                    "plan_id":"Q218-PIT","candidate":"Q218","scheduled":True,"dispatchable":True,
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
    assert candidates == ["Q104:I19", "Q218", "Q221"]
    assert all(x["candidate"] != "Q220" for x in plan["dispatches"])

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
                "plan_id": "Q218-PIT",
                "candidate": "Q218",
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
        "display_title": "Top-4 Slot windows Q218",
        "run_name": "Top-4 Slot windows Q218",
    }]
    plan = dispatch_candidates(snapshot, runs, max_dispatches=4)
    assert any(x["candidate"] == "Q219" for x in plan["dispatches"])
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
    assert [x["candidate"] for x in plan2["dispatches"]] == ["Q221"]
    assert plan2["dispatches"][0]["inputs"]["resource"] == "ubuntu_x64"
    assert any(d["decision"] == "DISPATCH_SLOT_BACKFILL" for d in plan2["decisions"])


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
                "plan_id": "Q218-PIT",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": workflow,
            }],
        }],
    }
    failed_once = [{
        "status": "completed",
        "conclusion": "failure",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q218",
        "run_name": "Top-4 Slot windows Q218",
    }]
    retry_plan = dispatch_candidates(snapshot, failed_once, max_dispatches=4)
    assert [x["candidate"] for x in retry_plan["dispatches"]] == ["Q218"]

    failed_twice = failed_once + [{
        "status": "completed",
        "conclusion": "failure",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q218",
        "run_name": "Top-4 Slot windows Q218",
    }]
    backfilled = dispatch_candidates(snapshot, failed_twice, max_dispatches=4)
    assert [x["candidate"] for x in backfilled["dispatches"]] == ["Q219"]
    assert any(d["decision"] == "DISPATCH_SLOT_BACKFILL" for d in backfilled["decisions"])


def test_q218_windows_focus_precheck_uses_available_windows_powershell_host():
    text = (ROOT / ".github/workflows/top4-candidate-slot-research.yml").read_text(encoding="utf-8")
    windows = text.split("  windows:", 1)[1].split("  ubuntu_x64:", 1)[0]
    assert "shell: bash" not in windows
    assert "shell: pwsh" not in windows
    assert "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" in windows
    assert "hash-object" not in windows


def test_top4_windows_slot_workflow_avoids_setup_python_action():
    text = (ROOT / ".github/workflows/top4-candidate-slot-research.yml").read_text(encoding="utf-8")
    windows = text.split("  windows:", 1)[1].split("  ubuntu_x64:", 1)[0]
    assert "actions/setup-python@v6" not in windows
    assert "python-3.13.15-nuget-top4-slot" in windows

def test_fast_dispatch_treats_startup_failure_as_one_retry_then_backfills():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Windows self-hosted B",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q218-PIT",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": workflow,
            }],
        }],
    }
    failed_once = [{
        "status": "completed",
        "conclusion": "startup_failure",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q218",
        "run_name": "Top-4 Slot windows Q218",
    }]
    retry_plan = dispatch_candidates(snapshot, failed_once, max_dispatches=4)
    assert [x["candidate"] for x in retry_plan["dispatches"]] == ["Q218"]

    failed_twice = failed_once + [{
        "status": "completed",
        "conclusion": "startup_failure",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q218",
        "run_name": "Top-4 Slot windows Q218",
    }]
    backfilled = dispatch_candidates(snapshot, failed_twice, max_dispatches=4)
    assert [x["candidate"] for x in backfilled["dispatches"]] == ["Q219"]
    assert any(d["decision"] == "DISPATCH_SLOT_BACKFILL" for d in backfilled["decisions"])


def test_fast_dispatch_has_non_slot_technical_failure_circuit_breaker():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    workflow = ".github/workflows/ai-worker-fabric.yml"
    snapshot = {
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Free AI pool",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q220-ADVERSARIAL",
                "candidate": "Q220",
                "scheduled": True,
                "dispatchable": True,
                "allow_parallel_with_candidate": True,
                "execution_workflow": workflow,
                "execution_workflow_inputs": {"task_id": "AI-TEST-Q220-TOP4-ADVERSARIAL-RETRY"},
            }],
        }],
    }
    failed = [{
        "status": "completed",
        "conclusion": "startup_failure",
        "path": workflow,
        "name": "Free AI Worker Fabric",
    }]
    retry = dispatch_candidates(snapshot, failed, max_dispatches=4)
    assert [x["candidate"] for x in retry["dispatches"]] == ["Q220"]

    failed_twice = failed + [{
        "status": "completed",
        "conclusion": "startup_failure",
        "path": workflow,
        "name": "Free AI Worker Fabric",
    }]
    blocked = dispatch_candidates(snapshot, failed_twice, max_dispatches=4)
    assert blocked["dispatches"] == []

def test_fast_dispatch_normalizes_candidate_identity_before_duplicate_guard():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    workflow = ".github/workflows/q104-i19-13f-historical-identity-census.yml"
    snapshot = {
        "work_assignments": [{
            "candidate": "Q104:I19",
            "task": "historical SEC 13F archive/security identity census",
            "job": "Q104 I19 Windows census",
            "lane": "FORMAL READINESS",
            "resource": "Windows self-hosted A",
        }],
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
    assert dispatch_candidates(snapshot, [], max_dispatches=4)["dispatches"] == []

def test_dashboard_planner_preserves_parallel_ai_dispatch_flag():
    generator = (ROOT / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert '"allow_parallel_with_candidate": bool(item.get("allow_parallel_with_candidate", False))' in generator


def test_fast_dispatch_backfills_next_top4_after_technical_retry_exhaustion():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "work_assignments": [],
        "planned_capacity": [{
            "resource": "Windows self-hosted B",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q218-PIT",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": workflow,
            }],
        }],
    }
    failed_twice = [
        {
            "status": "completed",
            "conclusion": "failure",
            "name": "Top-4 Candidate Slot Research",
            "display_title": "Top-4 Slot windows Q218",
            "run_name": "Top-4 Slot windows Q218",
        },
        {
            "status": "completed",
            "conclusion": "failure",
            "name": "Top-4 Candidate Slot Research",
            "display_title": "Top-4 Slot windows Q218",
            "run_name": "Top-4 Slot windows Q218",
        },
    ]
    plan = dispatch_candidates(snapshot, failed_twice, max_dispatches=4)
    assert [x["candidate"] for x in plan["dispatches"]] == ["Q219"]
    assert plan["dispatches"][0]["inputs"] == {"candidate": "Q219", "resource": "windows"}
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
                "plan_id": "Q218-PIT",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": workflow,
            }],
        }],
    }

    def failures(candidate):
        return [{
            "status": "completed",
            "conclusion": "failure",
            "name": "Top-4 Candidate Slot Research",
            "display_title": f"Top-4 Slot windows {candidate}",
            "run_name": f"Top-4 Slot windows {candidate}",
        } for _ in range(2)]

    runs = failures("Q218") + failures("Q219") + failures("Q220") + failures("Q221")
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





def test_q218_focused_gate_ignores_legacy_failures_from_older_master_context(monkeypatch):
    from automation import planned_capacity_fast_dispatch as dispatcher
    monkeypatch.setattr(dispatcher, "q218_positive_gate_index_current", lambda: set())
    dispatch_candidates = dispatcher.dispatch_candidates

    workflow = ".github/workflows/top4-candidate-slot-research.yml"
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
                "execution_workflow": workflow,
                "execution_workflow_inputs": {"focus_wave": True, "gate": "event_pair"},
            }],
        }],
    }
    legacy_failures = [{
        "status": "completed",
        "conclusion": "failure",
        "head_sha": "old-master",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q218 event_pair",
        "run_name": "Top-4 Slot windows Q218 event_pair",
    } for _ in range(20)]

    plan = dispatch_candidates(snapshot, legacy_failures, max_dispatches=4)
    assert [x["candidate"] for x in plan["dispatches"]] == ["Q218"]
    assert any(d["decision"] == "FOCUSED_GATE_TECHNICAL_RETRY_PERMITTED" for d in plan["decisions"]) is False

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

def test_q218_completed_focus_gate_is_not_redispatched(monkeypatch):
    from automation import planned_capacity_fast_dispatch as dispatcher
    monkeypatch.setattr(dispatcher, "completed_q218_gates_for_current_context", lambda runs: {"event_pair"})
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
    assert any(d["decision"] == "SKIP_FOCUSED_GATE_ALREADY_COMPLETED_CURRENT_CONTEXT" for d in plan["decisions"])


def test_q218_focused_gate_allows_one_technical_retry_then_stops(monkeypatch):
    from automation import planned_capacity_fast_dispatch as dispatcher
    monkeypatch.setattr(dispatcher, "q218_positive_gate_index_current", lambda: set())
    dispatch_candidates = dispatcher.dispatch_candidates

    workflow = ".github/workflows/top4-candidate-slot-research.yml"
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
                "execution_workflow": workflow,
                "execution_workflow_inputs": {"focus_wave": True, "gate": "event_pair"},
            }],
        }],
    }

    one_failure = [{
        "status": "completed",
        "conclusion": "failure",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q218 event_pair",
        "run_name": "Top-4 Slot windows Q218 event_pair",
        "head_sha": "current-master",
    }]
    retry = dispatch_candidates(snapshot, one_failure, max_dispatches=4)
    assert [x["candidate"] for x in retry["dispatches"]] == ["Q218"]
    assert any(d["decision"] == "FOCUSED_GATE_TECHNICAL_RETRY_PERMITTED" for d in retry["decisions"])

    two_failures = one_failure + [{
        "status": "completed",
        "conclusion": "failure",
        "name": "Top-4 Candidate Slot Research",
        "display_title": "Top-4 Slot windows Q218 event_pair",
        "run_name": "Top-4 Slot windows Q218 event_pair",
        "head_sha": "current-master",
    }]
    stopped = dispatch_candidates(snapshot, two_failures, max_dispatches=4)
    assert stopped["dispatches"] == []
    assert any(d["decision"] == "SKIP_FOCUSED_GATE_RETRY_EXHAUSTED" for d in stopped["decisions"])

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
        lambda task_id, root=None: task_id in {
            "AI-2026-10-06-Q218-TOP4-ADVERSARIAL",
            "AI-2026-10-08-Q104-I19-CENSUS-COMPILER-ADVERSARIAL",
        },
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


def test_q218_independent_replication_workflow_consumes_four_free_research_slots():
    from automation import generate_resource_dashboard as dashboard
    resources = [
        {"name": "Windows self-hosted B", "capacity_state": "available", "current_assignments": 0, "research_capacity_slots": 1},
        {"name": "Free AI pool", "capacity_state": "available", "current_assignments": 0, "research_capacity_slots": 1},
    ]
    monkeypatch = __import__("pytest").MonkeyPatch()
    try:
        monkeypatch.setattr(dashboard, "q218_receipt_state", lambda: {
            "source_complete": True,
            "event_pair_complete": True,
            "independent_complete": True,
        })
        monkeypatch.setattr(dashboard, "read_json_file", lambda path: (
            {"status": "Q218_INDEPENDENT_FRESH_SYMBOL_REPLICATION_COMPLETED"}
            if "q218_independent_replication_latest.json" in str(path)
            else {}
        ))
        monkeypatch.setattr(dashboard, "ai_task_completed_with_current_context", lambda task_id, root=None: task_id == "AI-2026-10-06-Q218-TOP4-ADVERSARIAL")
        plan = dashboard.planned_capacity_plan(resources, [], [{"code":"Q104:I19","next_gate":"13F census"},{"code":"Q218","next_gate":"replication"}], {}, {})
        assignments = [
            item
            for row in plan
            for item in row.get("planned_assignments", [])
            if item.get("scheduled")
        ]
        ids = {item["plan_id"] for item in assignments}
        assert "Q218-INDEPENDENT-REPLICATION" in ids
        assert "Q104-I19-CENSUS-ADVERSARIAL" in ids
        replication = next(x for x in assignments if x["plan_id"] == "Q218-INDEPENDENT-REPLICATION")
        assert set(replication["resource_leases"]) == {
            "Windows self-hosted B",
            "Windows self-hosted C",
            "GitHub-hosted Ubuntu x64",
            "GitHub-hosted ARM64",
        }
    finally:
        monkeypatch.undo()


def test_q218_independent_replication_workflow_is_registered_as_capacity_trigger():
    workflow = (ROOT / ".github/workflows/q218-independent-replication-once.yml").read_text(encoding="utf-8")
    dispatcher = (ROOT / ".github/workflows/planned-capacity-fast-dispatch.yml").read_text(encoding="utf-8")
    assert 'research/run_requests/q218_independent_replication.trigger' in workflow
    assert "Q218 Independent Fresh-Symbol Replication" in dispatcher
    assert "replicate_windows_a:" in workflow
    assert "replicate_windows_b:" in workflow
    assert "runs-on: [self-hosted, trading-agent-research]" in workflow
    assert "ubuntu-24.04-arm" in workflow


def test_q218_replication_contract_and_executor_are_fresh_symbol_disjoint():
    contract = json.loads((ROOT / "research/governance/q218_independent_replication_contract_2026_10_08.json").read_text(encoding="utf-8"))
    executor = (ROOT / "automation/q218_independent_replication.py").read_text(encoding="utf-8")
    assert contract["fresh_symbol_disjoint"] is True
    assert set(contract["issuers"]) == {"GOOGL","META","ORCL","PFE"}
    assert contract["replication_trial_id"] == "T-2026-10-08-Q218-REPLICATION-01"
    assert "q218_deterministic_performance_executor" not in executor
    assert "q218_sec_multichannel_source_gate" not in executor
    assert "q218_sec_event_pair_lineage_gate" not in executor


def test_fast_dispatch_fail_closed_for_unverified_physical_runner():
    import automation.planned_capacity_fast_dispatch as dispatcher
    snapshot = {
        "work_assignments": [],
        "resources": [{
            "name": "Windows self-hosted B",
            "type": "physical",
            "capacity_state": "unknown",
            "routable": False,
            "research_capacity_slots": 1,
            "research_slots_in_use": 0,
            "research_slots_free": 0,
        }],
        "planned_capacity": [{
            "resource": "Windows self-hosted B",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q218-INDEPENDENT-REPLICATION",
                "candidate": "Q218",
                "scheduled": True,
                "dispatchable": True,
                "allow_parallel_with_candidate": True,
                "execution_workflow": ".github/workflows/q218-independent-replication-once.yml",
                "resource_leases": [
                    "Windows self-hosted B",
                    "Windows self-hosted C",
                    "GitHub-hosted Ubuntu x64",
                    "GitHub-hosted ARM64",
                ],
            }],
        }],
    }
    plan = dispatcher.dispatch_candidates(snapshot, [], max_dispatches=4)
    assert plan["dispatches"] == []


def test_dashboard_physical_unverified_has_zero_routable_free():
    from automation import generate_resource_dashboard as dashboard
    configured = [{
        "name": "Windows self-hosted B",
        "type": "physical",
        "research_capacity_slots": 1,
        "configured_runner": "LHT-N133732-2",
    }]
    result = dashboard.enrich_resources(configured, [], [])
    row = result[0]
    assert row["capacity_state"] == "unknown"
    assert row["routable"] is False
    assert row["research_slots_free_nominal"] == 1
    assert row["research_slots_free"] == 0
    assert row["routable_slots_free"] == 0


def test_capacity_contract_requires_live_runner_verification_for_physical_slots():
    contract = json.loads((ROOT / "research/governance/persistent_research_acceleration_contract.json").read_text(encoding="utf-8"))
    windows = contract["parallelism_policy"]["self_hosted_windows"]
    assert windows["availability_policy"] == "LIVE_VERIFIED_ONLINE_REQUIRED_FOR_AUTOMATIC_DISPATCH"
    rules = contract["rolling_capacity_wave_control"]["slotwise_replenishment"]["rules"]
    assert "A physical self-hosted slot is automatically routable only when its exact runner is currently verified online; UNVERIFIED physical slots have zero routable free capacity." in rules


def test_q218_multi_resource_plan_requires_every_lease_to_be_routable():
    from automation import generate_resource_dashboard as dashboard
    resources = [
        {"name":"Windows self-hosted B","type":"physical","routable":False,"capacity_state":"unknown","research_capacity_slots":1,"current_assignments":0,"research_slots_free":0},
        {"name":"Windows self-hosted C","type":"physical","routable":True,"capacity_state":"available","research_capacity_slots":1,"current_assignments":0,"research_slots_free":1},
        {"name":"GitHub-hosted Ubuntu x64","type":"cloud","routable":True,"capacity_state":"available","research_capacity_slots":2,"current_assignments":0,"research_slots_free":1},
        {"name":"GitHub-hosted ARM64","type":"cloud","routable":True,"capacity_state":"available","research_capacity_slots":2,"current_assignments":0,"research_slots_free":1},
    ]
    plan = dashboard.planned_capacity_plan(resources, [], [{"code":"Q218"}], {}, {})
    rows=[p for r in plan for p in r.get("planned_assignments",[]) if p.get("plan_id")=="Q218-INDEPENDENT-REPLICATION"]
    assert rows == []


def test_fast_dispatch_requires_all_multi_resource_leases_to_be_routable():
    import automation.planned_capacity_fast_dispatch as dispatcher
    workflow = ".github/workflows/q218-independent-replication-once.yml"
    snapshot = {
        "work_assignments": [],
        "resources": [
            {"name":"Windows self-hosted B","type":"physical","routable":True,"capacity_state":"available","research_capacity_slots":1,"research_slots_in_use":0,"research_slots_free":1},
            {"name":"Windows self-hosted C","type":"physical","routable":False,"capacity_state":"unknown","research_capacity_slots":1,"research_slots_in_use":0,"research_slots_free":0},
            {"name":"GitHub-hosted Ubuntu x64","type":"cloud","routable":True,"capacity_state":"operating","research_capacity_slots":2,"research_slots_in_use":1,"research_slots_free":1},
            {"name":"GitHub-hosted ARM64","type":"cloud","routable":True,"capacity_state":"operating","research_capacity_slots":2,"research_slots_in_use":1,"research_slots_free":1},
        ],
        "planned_capacity": [{
            "resource":"Windows self-hosted B",
            "current_assignments":0,
            "research_capacity_slots":1,
            "research_slots_free":1,
            "planned_assignments":[{
                "plan_id":"Q218-INDEPENDENT-REPLICATION",
                "candidate":"Q218",
                "scheduled":True,
                "dispatchable":True,
                "allow_parallel_with_candidate":True,
                "execution_workflow":workflow,
                "resource_leases":["Windows self-hosted B","Windows self-hosted C","GitHub-hosted Ubuntu x64","GitHub-hosted ARM64"],
            }],
        }],
    }
    plan=dispatcher.dispatch_candidates(snapshot,[],max_dispatches=4)
    assert plan["dispatches"] == []
    assert any(d["decision"]=="SKIP_MULTI_RESOURCE_LEASE_NOT_SIMULTANEOUSLY_ROUTABLE" for d in plan["decisions"])
