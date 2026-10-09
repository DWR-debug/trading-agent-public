def test_fast_dispatch_uses_one_q219_reserve_only_when_a_windows_slot_is_free():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "master_sha": "current-master",
        "focus_candidates": ["Q104:I19", "Q218", "Q219"],
        "work_assignments": [
            {"candidate": "Q104:I19", "task": "historical SEC 13F census", "resource": "GitHub-hosted ARM64"},
            {"candidate": "Q218", "task": "Top-4 Slot windows Q218", "job": "event_pair", "resource": "Windows self-hosted B"},
        ],
        "planned_capacity": [{
            "resource": "Windows self-hosted A",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q219-OPTIONS-SOURCE-PIT",
                "candidate": "Q219",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": workflow,
                "execution_workflow_inputs": {"gate": "all"},
            }],
        }],
    }
    runs = [{
        "id": 999001,
        "status": "in_progress",
        "name": "Top-4 Slot windows Q218 event_pair",
        "display_title": "Top-4 Slot windows Q218 event_pair",
        "run_name": "Top-4 Slot windows Q218 event_pair",
    }]
    plan = dispatch_candidates(snapshot, runs, max_dispatches=4)
    assert [item["candidate"] for item in plan["dispatches"]] == ["Q219"]
    assert plan["dispatches"][0]["inputs"] == {"gate": "all", "candidate": "Q219", "resource": "windows"}
    assert plan["dispatches"][0]["workflow"] == workflow


def test_fast_dispatch_does_not_start_a_second_q219_capacity_fill():
    from automation.planned_capacity_fast_dispatch import dispatch_candidates
    workflow = ".github/workflows/top4-candidate-slot-research.yml"
    snapshot = {
        "master_sha": "current-master",
        "focus_candidates": ["Q104:I19", "Q218", "Q219"],
        "work_assignments": [
            {"candidate": "Q219", "task": "Top-4 Slot windows Q219", "resource": "Windows self-hosted A"},
        ],
        "planned_capacity": [{
            "resource": "Windows self-hosted C",
            "current_assignments": 0,
            "research_capacity_slots": 1,
            "planned_assignments": [{
                "plan_id": "Q219-OPTIONS-SOURCE-PIT",
                "candidate": "Q219",
                "scheduled": True,
                "dispatchable": True,
                "execution_workflow": workflow,
                "execution_workflow_inputs": {"gate": "all"},
            }],
        }],
    }
    plan = dispatch_candidates(snapshot, [], max_dispatches=4)
    assert plan["dispatches"] == []
