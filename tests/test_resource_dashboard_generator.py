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
    assert capacity_state(physical, {"status":"online","busy":True}, []) == "operating"
    assert capacity_state(physical, {"status":"online","busy":False}, []) == "available"
    assert capacity_state(physical, None, []) == "unknown"
    assert capacity_state(cloud, None, []) == "available"


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


def test_dashboard_tracks_q219_in_top4_candidate_capacity():
    from automation.generate_resource_dashboard import candidate_pipeline
    top4 = [{"code": "Q219", "state": "DESIGN_ONLY_ACTIVE"}]
    rows = candidate_pipeline(top4, [], {}, {})
    assert [x["code"] for x in rows] == ["Q219"]


def test_dashboard_generator_bootstraps_repo_root_for_file_execution():
    root = Path(__file__).parents[1]
    generator = (root / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert "import sys" in generator
    assert "if str(ROOT) not in sys.path:" in generator
    assert "sys.path.insert(0, str(ROOT))" in generator
