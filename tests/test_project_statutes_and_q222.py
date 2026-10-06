import json
from pathlib import Path

ROOT=Path(__file__).parents[1]


def test_project_statutes_are_binding_and_referenced():
    statute=ROOT/"docs/TRADING_AGENT_PROJECT_STATUTES.md"
    mirror=ROOT/"research/governance/project_statutes.json"
    assert statute.is_file()
    d=json.loads(mirror.read_text(encoding="utf-8"))
    assert d["status"]=="BINDING_ACTIVE"
    assert "keine künstliche Arbeit" in d["useful_capacity_statute"]
    assert d["capacity_rule"]["immediate_replenishment"] is True
    assert d["capacity_rule"]["event_driven_completion_chaining"] is True
    for rel in [
        "docs/TRADING_AGENT_PROJECT_MEMORY.md","docs/PROJECT_CONTEXT.md","AGENTS.md",
        "PROJECT_STATUS.md","docs/GITHUB_FREE_RESOURCE_OPERATING_MODEL.md",
        "docs/DEVELOPMENT_ORCHESTRATION.md","docs/TRADING_AGENT_SUPERVISION_PROTOCOL.md",
        "docs/TRADING_AGENT_OS_ORCHESTRATION.md","docs/TRADING_AGENT_CHAT_ENTRYPOINT.md",
        "docs/DECISION_BASIS.md"
    ]:
        assert "TRADING_AGENT_PROJECT_STATUTES.md" in (ROOT/rel).read_text(encoding="utf-8")


def test_q222_is_design_only_and_merge_or_kill_protected():
    d=json.loads((ROOT/"research/candidates/orthogonal_candidate_specs_2026-10-05.json").read_text(encoding="utf-8"))
    c=next(x for x in d["candidates"] if x["id"]=="Q222")
    assert c["scientific_boundary"]=="discovery_contract_only"
    assert c["priority"]=="UNRANKED_DESIGN"
    assert "Q220" in c["non_overlap"]
    assert len(c["cheap_falsifiers"])>=3
    assert len(c["gates"])>=3
    assert d["shared_contract"]["performance_authorization"] is False
    assert d["shared_contract"]["promotion_authorization"] is False
    assert d["shared_contract"]["live_execution"] is False


def test_current_bounded_session_directive_is_bounded():
    d=json.loads((ROOT/"research/run_requests/rolling_capacity_window_2026-10-05.json").read_text(encoding="utf-8"))
    assert d["session_mode"]["status"] in {"ACTIVE", "ACTIVE_2H"}
    assert d["session_mode"]["duration_minutes"] == 120
    assert d["session_mode"]["no_artificial_work"] is True
    assert d["session_mode"]["no_duplicate_work"] is True
    assert d["session_mode"]["scientific_boundary_unchanged"] is True


def test_top4_operational_state_includes_q219_capacity():
    import json
    state=json.loads((ROOT/"ops/trading_agent_os_state.json").read_text(encoding="utf-8"))
    overlay=state["top_candidate_capacity_overlay"]["windows_B"]
    assert overlay["priority"] == ["Q218","Q219","Q220","Q221"]
    assert "Q219" in overlay["new_overlay"]
    assert "no Q219 top-4 capacity" not in overlay["new_overlay"]
