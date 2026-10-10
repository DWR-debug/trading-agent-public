"""Tests for the broad candidate portfolio assessment shown on the research dashboard."""
from pathlib import Path

from automation.candidate_portfolio_assessment import (
    A,
    PORTFOLIO_METHODOLOGY,
    build_candidate_portfolio,
)

ROOT = Path(__file__).parents[1]


def test_portfolio_covers_frozen_prospects_plus_i19():
    from json import loads

    specs = loads((ROOT / "research/candidates/orthogonal_candidate_specs_2026-10-05.json").read_text())
    frozen_ids = {x["id"] for x in specs["candidates"]}
    entries = build_candidate_portfolio(ROOT, {}, [])
    ids = {x["code"] for x in entries}
    assert frozen_ids.issubset(ids)
    assert "Q104:I19" in ids
    assert len(ids) == len(frozen_ids) + 1
    assert len(entries) == 25


def test_rank_is_deterministic_and_foia_duplicates_are_consolidated():
    entries = build_candidate_portfolio(ROOT, {}, [])
    ordered = [x["code"] for x in entries]
    assert ordered[:5] == ["Q104:I19", "Q220", "Q218", "Q221", "Q219"]
    by_code = {x["code"]: x for x in entries}
    assert by_code["Q227"]["rank"] == by_code["Q231"]["rank"]
    assert by_code["Q227"]["family"] == by_code["Q231"]["family"] == "SEC_FOIA_ACQUISITION"
    assert by_code["Q231"]["separate_workpack_allowed"] is False
    assert by_code["Q217"]["portfolio_action"] == "ORTHOGONALITY_FIRST"


def test_success_probabilities_are_not_fabricated_and_ranges_are_labeled():
    entries = build_candidate_portfolio(ROOT, {}, [])
    assert all(x["strategy_success_probability"] is None for x in entries)
    assert all(x["strategy_success_probability_status"] == "NOT_ESTIMABLE" for x in entries)
    assert all(x["duration_estimate_confidence"] == "LOW_PLANNING_RANGE" for x in entries)
    assert "not empirical completion-time forecasts" in PORTFOLIO_METHODOLOGY["duration_basis"]
    assert "Not estimable" in PORTFOLIO_METHODOLOGY["success_probability"]


def test_current_trial_state_overrides_design_only_status_for_q218():
    evidence = {
        "active_research_registry": {
            "active_design_families": [{"code": "Q218", "state": "DESIGN_ONLY_ACTIVE"}],
            "active_trials": [{
                "code": "Q218",
                "state": "PERFORMANCE_EXECUTED_PENDING_CURRENT_CONTEXT_REVALIDATION",
                "next_gate": "current context revalidation",
            }],
        }
    }
    by_code = {x["code"]: x for x in build_candidate_portfolio(ROOT, evidence, [])}
    assert by_code["Q218"]["current_state"] == "PERFORMANCE_EXECUTED_PENDING_CURRENT_CONTEXT_REVALIDATION"


def test_focus_progress_is_reflected_without_claiming_success_probability():
    progress = [{
        "code": "Q104:I19",
        "current_milestone": "13F security census",
        "current_milestone_status": "RUNNING",
    }]
    by_code = {x["code"]: x for x in build_candidate_portfolio(ROOT, {}, progress)}
    assert by_code["Q104:I19"]["next_gate"] == "13F security census"
    assert by_code["Q104:I19"]["strategy_success_probability"] is None


def test_dashboard_generator_exposes_portfolio_and_uses_dynamic_refresh():
    generator = (ROOT / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    dashboard_js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    assert "build_candidate_portfolio(ROOT, evidence, candidate_progress)" in generator
    assert '"candidate_portfolio": candidate_portfolio' in generator
    assert 'id="candidatePortfolio"' in html
    assert "renderCandidatePortfolio(data)" in dashboard_js


def test_dashboard_generator_has_direct_script_import_fallback():
    generator = (ROOT / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert "from automation.candidate_portfolio_assessment import build_candidate_portfolio, PORTFOLIO_METHODOLOGY" in generator
    assert "from candidate_portfolio_assessment import build_candidate_portfolio, PORTFOLIO_METHODOLOGY" in generator

def test_dashboard_top_three_focus_includes_q104_q220_q218_everywhere():
    dashboard_js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")

    assert 'var FOCUS=["Q104:I19","Q220","Q218"]' in dashboard_js
    assert 'slice(0,3)' in dashboard_js
    assert 'Q104:I19 · Q220 · Q218' in dashboard_js
    assert "DATEN-GATE BLOCKIERT" in dashboard_js
    assert "FOLGEGATE GESPERRT" in dashboard_js
    assert "Top-3-Kandidatensteuerung" in html
    assert 'data-candidate=' in dashboard_js
    assert "Next-Gate-Backlog · Top 3" in html
    for candidate in ("Q104:I19", "Q220", "Q218"):
        assert f">{candidate}</span>" in html

