from pathlib import Path
import json

ROOT = Path(__file__).parents[1]


def test_fast_dispatch_uses_canonical_completion_monitor_and_five_minute_backstop():
    dispatcher = (ROOT / ".github/workflows/planned-capacity-fast-dispatch.yml").read_text(encoding="utf-8")
    monitor_a = (ROOT / ".github/workflows/research-completion-monitor-a.yml").read_text(encoding="utf-8")
    monitor_b = (ROOT / ".github/workflows/research-completion-monitor-b.yml").read_text(encoding="utf-8")
    assert 'cron: "*/5 * * * *"' in dispatcher
    assert "workflow_run:" not in dispatcher
    assert "cancel-in-progress: false" in dispatcher
    assert "workflow_run:" in monitor_a
    assert '      - "Q*"' in monitor_a
    assert '      - "Top-4*"' in monitor_a
    assert '      - "*PIT*"' in monitor_a
    assert '      - "*Source*"' in monitor_a
    assert '      - "Evidence Graph*"' in monitor_a
    assert "gh workflow run planned-capacity-fast-dispatch.yml" in monitor_a
    assert "workflow_run:" not in monitor_b


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
                    "execution_workflow_inputs": {"task_id": "AI-2026-10-06-Q218-TOP4-ADVERSARIAL"},
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
    assert plan2["dispatches"] == []


def test_fast_dispatch_allows_one_retry_after_failed_slot_but_blocks_second_failure():
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
    blocked = dispatch_candidates(snapshot, failed_twice, max_dispatches=4)
    assert blocked["dispatches"] == []


def test_top4_windows_slot_workflow_avoids_setup_python_action():
    text = (ROOT / ".github/workflows/top4-candidate-slot-research.yml").read_text(encoding="utf-8")
    windows = text.split("  windows:", 1)[1].split("  ubuntu_x64:", 1)[0]
    assert "actions/setup-python@v6" not in windows
    assert "python-3.13.15-nuget-top4-slot" in windows
