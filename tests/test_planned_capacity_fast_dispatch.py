from pathlib import Path
import json

ROOT = Path(__file__).parents[1]


def test_fast_dispatch_workflow_is_event_driven_with_five_minute_recovery():
    text = (ROOT / ".github/workflows/planned-capacity-fast-dispatch.yml").read_text(encoding="utf-8")
    assert 'cron: "*/5 * * * *"' in text
    assert "workflow_run:" in text
    assert "types: [completed]" in text
    assert "actions: write" in text
    assert "generate_resource_dashboard.py" in text
    assert "planned_capacity_fast_dispatch" in text


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


def test_fast_dispatch_skips_recent_success_on_same_master_sha():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates

    snapshot = {
        "master_sha": "abc123",
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
                "execution_workflow": ".github/workflows/top4-candidate-research-capacity.yml",
            }],
        }],
    }
    runs = [{
        "path": ".github/workflows/top4-candidate-research-capacity.yml",
        "status": "completed",
        "conclusion": "success",
        "head_sha": "abc123",
        "created_at": "2099-10-07T08:00:00Z",
    }]
    plan = dispatch_candidates(snapshot, runs, max_dispatches=4)
    assert plan["dispatches"] == []
    assert any(d["decision"] == "SKIP_RECENT_SUCCESS_SAME_SHA" for d in plan["decisions"])
