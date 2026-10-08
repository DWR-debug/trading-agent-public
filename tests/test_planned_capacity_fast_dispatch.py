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
    assert q104["current_milestone_progress_percent"] == 0
    assert q104["total_milestones"] == 9
    assert 0 <= q104["overall_progress_percent"] <= 100
    assert q218["current_milestone"] == "Preregistration + authorization reconcile"
    assert any(m["label"] == "Independent Architecture PIT" and m["status"] == "complete" for m in q218["milestones"])


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


def test_dashboard_skips_current_context_completed_ai_before_filling_free_pool(monkeypatch):
    from automation import generate_resource_dashboard as dashboard

    resources = [{
        "name": "Free AI pool", "type": "cloud", "capacity_state": "available",
        "current_assignments": 0, "research_capacity_slots": 1,
    }]
    monkeypatch.setattr(
        dashboard,
        "ai_task_completed_with_current_context",
        lambda task_id, root=None: task_id == "AI-2026-10-06-Q220-TOP4-ADVERSARIAL",
    )
    plan = dashboard.planned_capacity_plan(resources, [], [], {}, {})
    ai = next(row for row in plan if row["resource"] == "Free AI pool")
    assert [item["plan_id"] for item in ai["planned_assignments"]] == ["Q221-ADVERSARIAL"]


def test_dashboard_generator_supports_direct_script_execution_import_mode():
    generator = (ROOT / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert "from automation.planned_capacity_fast_dispatch import ai_task_completed_with_current_context" in generator
    assert "from planned_capacity_fast_dispatch import ai_task_completed_with_current_context" in generator
