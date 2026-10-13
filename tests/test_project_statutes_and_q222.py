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
    # The lease may be ACTIVE while its UTC window is scheduled/current, or remain
    # explicitly EXPIRED after a completed window; both states must remain bounded.
    assert d["status"] in {"ACTIVE", "EXPIRED"}
    assert d["session_mode"]["status"] in {"ACTIVE", "EXPIRED"}
    start = __import__("datetime").datetime.fromisoformat(d["start_utc"].replace("Z", "+00:00"))
    end = __import__("datetime").datetime.fromisoformat(d["end_utc"].replace("Z", "+00:00"))
    assert (end - start).total_seconds() == 7200
    assert d["session_mode"]["duration_minutes"] == 120
    assert d["session_mode"]["no_artificial_work"] is True
    assert d["session_mode"]["no_duplicate_work"] is True
    assert d["session_mode"]["scientific_boundary_unchanged"] is True
    assert d["safety"]["PAPER_ONLY"] is True
    assert all(d["safety"][key] is False for key in ("LIVE_TRADING_ENABLED", "performance", "holdout_selection", "ranking", "tuning", "promotion", "live_execution"))


def test_focused_operational_state_locks_automatic_candidate_dispatch():
    import json
    state=json.loads((ROOT/"ops/trading_agent_os_state.json").read_text(encoding="utf-8"))
    overlay=state["top_candidate_capacity_overlay"]["windows_B"]
    assert overlay["priority"] == ["Q220", "Q221"]
    assert "Q104:I19" in overlay["new_overlay"] or "Q104:I19" in state["current_research_focus"]["active_next"]
    assert state["top_candidate_capacity_overlay"].get("discovery_reserve") == ["Q218", "Q219"]
    assert state["top_candidate_capacity_overlay"].get("paused_candidates") == ["Q218","Q219"]
    assert "Q219" not in overlay["priority"]
    assert "Q220" in overlay["priority"]
    assert "Q221" in overlay["priority"]
    assert "Q218" not in overlay["priority"]
