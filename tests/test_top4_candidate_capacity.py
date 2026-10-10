from pathlib import Path
from automation import top4_candidate_capacity as worker

ROOT = Path(__file__).parents[1]

def test_focused_capacity_has_only_three_candidate_workpacks_and_no_authority():
    assert list(worker.LANES) == ["Q104:I19", "Q218", "Q220"]
    for candidate, commands in worker.LANES.items():
        assert commands
        flattened=" ".join(" ".join(str(x) for x in cmd) for cmd in commands)
        assert "performance_authorization" not in flattened
        assert "holdout_selection" not in flattened
        assert "ranking" not in flattened
        assert "tuning" not in flattened
        assert "live_execution" not in flattened

def test_focused_workpacks_are_mechanistically_separate():
    q104=" ".join(" ".join(map(str,c)) for c in worker.LANES["Q104:I19"])
    q218=" ".join(" ".join(map(str,c)) for c in worker.LANES["Q218"])
    q220=" ".join(" ".join(map(str,c)) for c in worker.LANES["Q220"])
    assert "q104_i19_xbrl_pit_compiler" in q104
    assert "q104_i19_13f_historical_identity_census" in q104
    assert "q104_i19_xbrl_concept_freeze" in q104
    assert "q218_sec_multichannel_source_gate" in q218
    assert "q218_sec_event_pair_lineage_gate" in q218
    assert "test_q220_as_filed_xbrl_population_gate.py" in q220
    assert "q104_xbrl_concept_freeze_audit.py" in q220
    assert "q104_i19_xbrl_pit_compiler.py" in q220
    assert set(worker.LANES) == {"Q104:I19", "Q218", "Q220"}

def test_top4_workflow_uses_three_windows_and_hosted_x64_arm64():
    text=(ROOT/".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert "max-parallel: 3" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "runs-on: ubuntu-24.04" in text
    assert "runs-on: ubuntu-24.04-arm" in text
    assert "candidate: [Q218]" in text
    assert text.count("candidate: [Q220]") == 2
    assert "Q219" not in text
    assert "Q221" not in text
    assert "candidate: [Q104:I19" not in text
    assert "\n  schedule:" not in text
    assert "\n  push:" not in text
    assert "workflow_dispatch:" in text

def test_legacy_research_loops_are_manual_only():
    for path in (
        ".github/workflows/permanent-pc-research-loop.yml",
        ".github/workflows/hosted-deterministic-frontier.yml",
        ".github/workflows/windows-runner-c-long-research.yml",
    ):
        text=(ROOT/path).read_text(encoding="utf-8")
        assert "workflow_dispatch:" in text
        assert "\n  schedule:" not in text
        assert "\n  push:" not in text


def test_top4_balances_hosted_capacity_slots():
    text=(ROOT/".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert 'candidate: [Q218]' in text
    assert text.count('candidate: [Q220]') == 2
    assert 'candidate: [Q219]' not in text
    assert 'candidate: [Q221]' not in text
    hosted = text.split("  hosted_x64:", 1)[1]
    assert "Q219" not in hosted
    assert "trading-agent-research-hosted-ubuntu-24.04" in hosted
    assert "trading-agent-research-hosted-ubuntu-24.04-arm" in hosted



def test_top4_has_no_global_wave_lock():
    text=(ROOT/".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert "\nconcurrency:\n  group: trading-agent-top4-capacity" not in text
    assert "trading-agent-research-hosted-ubuntu-24.04" in text
    assert "trading-agent-research-hosted-ubuntu-24.04-arm" in text


def test_hosted_slots_are_explicitly_leased():
    text=(ROOT/".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    q104=(ROOT/".github/workflows/q104-i19-13f-historical-identity-census.yml").read_text(encoding="utf-8")
    assert "trading-agent-research-hosted-ubuntu-24.04-slot-2" in text
    assert "trading-agent-research-hosted-ubuntu-24.04-arm-slot-2" in text
    assert "format('trading-agent-research-hosted-{0}-slot-{1}', matrix.runner, matrix.slot)" in q104
    assert "format('trading-agent-research-windows-slot-{0}', matrix.slot)" in q104
    assert 'runner: "ubuntu-24.04"' in q104
    assert 'runner: "ubuntu-24.04-arm"' in q104
    assert 'slot: "1"' in q104


def test_top4_workflow_triggers_only_on_focused_candidate_gates():
    slot=(ROOT/".github/workflows/top4-candidate-slot-research.yml").read_text(encoding="utf-8")
    capacity=(ROOT/"automation/top4_candidate_capacity.py").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in slot
    candidate_options = slot.split("      candidate:", 1)[1].split("      resource:", 1)[0]
    assert "Q218" in candidate_options and "Q220" in candidate_options
    assert "Q219" not in candidate_options and "Q221" not in candidate_options
    assert '"Q219":[' not in capacity and '"Q221":[' not in capacity
    assert "automation/q220_as_filed_xbrl_population_gate.py" in capacity

def test_dashboard_routes_top4_candidates_to_slot_scoped_workflow_and_i19_to_census():
    text=(ROOT/"automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert '.github/workflows/top4-candidate-slot-research.yml' in text
    assert '.github/workflows/q104-i19-13f-historical-identity-census.yml' in text
    assert '"plan_id": "Q104-I19-CENSUS"' in text
    assert '"exclusive_dispatch": True' in text


def test_focused_q218_slot_mode_is_explicit_and_non_authorizing():
    text=(ROOT/".github/workflows/top4-candidate-slot-research.yml").read_text(encoding="utf-8")
    assert "focus_wave:" in text
    assert "type: boolean" in text
    assert "gate:" in text
    assert "event_pair" in text
    assert "automation/q218_sec_multichannel_source_gate" in text
    assert "automation/q218_sec_event_pair_lineage_gate" in text
    assert "SLOT_RESEARCH_BOUNDARY=PAPER_ONLY_NO_PERFORMANCE_NO_HOLDOUT_NO_RANKING_NO_TUNING_NO_PROMOTION_NO_LIVE_EXECUTION" in text


def test_dashboard_capacity_plan_includes_only_focused_receipt_defined_candidate_work():
    from automation import generate_resource_dashboard as dashboard

    resources = [
        {"name": "Windows self-hosted A", "current_assignments": 1, "capacity_state": "operating"},
        {"name": "Windows self-hosted B", "current_assignments": 0, "capacity_state": "available"},
        {"name": "Windows self-hosted C", "current_assignments": 0, "capacity_state": "available"},
        {"name": "GitHub-hosted Ubuntu x64", "current_assignments": 1, "capacity_state": "operating"},
        {"name": "GitHub-hosted ARM64", "current_assignments": 1, "capacity_state": "operating"},
        {"name": "Free AI pool", "current_assignments": 0, "capacity_state": "available"},
    ]
    board = [
        {"code": "Q104:I19", "next_gate": "historical 13F census"},
        {"code": "Q218", "next_gate": "current-context provenance"},
        {"code": "Q219", "next_gate": "options source breadth"},
        {"code": "Q220", "next_gate": "as-filed mapping"},
        {"code": "Q221", "next_gate": "historical public clock"},
    ]
    plan = dashboard.planned_capacity_plan(resources, [], board, {}, {})
    scheduled = {
        item["candidate"]: item
        for row in plan for item in row["planned_assignments"]
        if item.get("scheduled")
    }
    assert {"Q104:I19", "Q220"}.issubset(scheduled)
    assert "Q219" not in scheduled and "Q221" not in scheduled
    assert scheduled["Q220"]["execution_workflow"] == ".github/workflows/top4-candidate-slot-research.yml"
    assert scheduled["Q220"]["dispatchable"] is True
    assert scheduled["Q220"]["execution_workflow_inputs"]["gate"] == "all"

def test_dashboard_capacity_plan_hides_active_or_failed_full_i19_census():
    from automation import generate_resource_dashboard as dashboard

    resources = [
        {"name": "Windows self-hosted A", "current_assignments": 0, "research_capacity_slots": 1, "research_slots_free": 1},
        {"name": "Windows self-hosted B", "current_assignments": 0, "research_capacity_slots": 1, "research_slots_free": 1},
        {"name": "Windows self-hosted C", "current_assignments": 0, "research_capacity_slots": 1, "research_slots_free": 1},
        {"name": "GitHub-hosted Ubuntu x64", "current_assignments": 0, "research_capacity_slots": 2, "research_slots_free": 2},
        {"name": "GitHub-hosted ARM64", "current_assignments": 0, "research_capacity_slots": 2, "research_slots_free": 2},
        {"name": "Free AI pool", "current_assignments": 0, "research_capacity_slots": 1, "research_slots_free": 1},
    ]
    active_census = [{
        "name": "Q104 I19 Historical 13F Identity Census",
        "status": "in_progress",
        "head_sha": "old-census-sha",
        "id": 37976018426,
    }]
    plan = dashboard.planned_capacity_plan(resources, [], [], {}, {}, recent_runs=active_census)
    scheduled_ids = {
        item["plan_id"]
        for row in plan for item in row["planned_assignments"]
        if item.get("scheduled")
    }
    assert "Q104-I19-CENSUS" not in scheduled_ids
    assert not any(
        item.get("plan_id") == "Q104-I19-INDEPENDENT-REPRO" and item.get("scheduled")
        for row in plan for item in row["planned_assignments"]
    )

    failed_census = [{
        "name": "Q104 I19 Historical 13F Identity Census",
        "status": "completed",
        "conclusion": "failure",
        "head_sha": "old-census-sha",
        "id": 123,
    }]
    plan_after_failure = dashboard.planned_capacity_plan(resources, [], [], {}, {}, recent_runs=failed_census)
    after_failure_ids = {
        item["plan_id"]
        for row in plan_after_failure for item in row["planned_assignments"]
        if item.get("scheduled")
    }
    assert "Q104-I19-CENSUS" not in after_failure_ids


def test_dashboard_does_not_backfill_out_of_focus_candidates_when_q220_active():
    from automation import generate_resource_dashboard as dashboard

    resources = [
        {"name": "Windows self-hosted A", "current_assignments": 0, "research_capacity_slots": 1, "research_slots_free": 1},
        {"name": "Windows self-hosted B", "current_assignments": 0, "research_capacity_slots": 1, "research_slots_free": 1},
        {"name": "Windows self-hosted C", "current_assignments": 0, "research_capacity_slots": 1, "research_slots_free": 1},
        {"name": "GitHub-hosted Ubuntu x64", "current_assignments": 2, "research_capacity_slots": 2, "research_slots_free": 0},
        {"name": "GitHub-hosted ARM64", "current_assignments": 1, "research_capacity_slots": 2, "research_slots_free": 1},
        {"name": "Free AI pool", "current_assignments": 0, "research_capacity_slots": 1, "research_slots_free": 1},
    ]
    board = [
        {"code": "Q219", "next_gate": "options source breadth"},
        {"code": "Q220", "next_gate": "as-filed mapping"},
        {"code": "Q221", "next_gate": "historical public clock"},
    ]
    runs = [
        {"name": "Q104 I19 Historical 13F Identity Census", "path": ".github/workflows/q104-i19-13f-historical-identity-census.yml", "status": "completed", "conclusion": "failure"},
        {"name": "Top-4 Slot ubuntu_arm64 Q221 all", "status": "completed", "conclusion": "success"},
        {"name": "Q220 As-Filed SEC-XBRL Population Repair", "status": "in_progress"},
    ]
    plan = dashboard.planned_capacity_plan(resources, [], board, {}, {}, recent_runs=runs)
    scheduled = {
        item["candidate"]: (row["resource"], item)
        for row in plan for item in row["planned_assignments"]
        if item.get("scheduled")
    }
    assert "Q220" not in scheduled
    assert "Q219" not in scheduled
    assert "Q221" not in scheduled
    assert all(candidate in {"Q104:I19", "Q218", "Q220"} for candidate in scheduled)
