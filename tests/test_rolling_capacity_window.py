from __future__ import annotations

import json
from datetime import datetime

def test_current_bounded_capacity_window_contract():
    p = json.loads(open("research/run_requests/rolling_capacity_window_2026-10-05.json", encoding="utf-8").read())
    start = datetime.fromisoformat(p["start_utc"].replace("Z","+00:00"))
    end = datetime.fromisoformat(p["end_utc"].replace("Z","+00:00"))
    assert (end-start).total_seconds() == 120 * 60
    assert p["cadence_minutes"] == 10
    assert p["recent_success_cooldown_minutes"] >= 60
    assert p["safety"]["PAPER_ONLY"] is True
    assert all(p["safety"][k] is False for k in ("performance","holdout_selection","ranking","tuning","promotion","live_execution"))

def test_wave_order():
    p = json.loads(open("research/run_requests/rolling_capacity_window_2026-10-05.json", encoding="utf-8").read())
    assert [x["start_after_minutes"] for x in p["phases"]] == [0,30,60,90]
    assert all(x["workflows"] for x in p["phases"])


def test_capacity_dispatcher_ignores_feature_branch_runs_for_master_research():
    workflow = open(".github/workflows/capacity-saturation-rolling-waves.yml", encoding="utf-8").read()
    assert '.head_branch == "master"' in workflow


def test_capacity_dispatcher_matches_runs_by_workflow_path():
    workflow = open(".github/workflows/capacity-saturation-rolling-waves.yml", encoding="utf-8").read()
    assert '.path == $workflow_path' in workflow


def test_capacity_dispatcher_does_not_use_legacy_workflow_url_match():
    workflow = open(".github/workflows/capacity-saturation-rolling-waves.yml", encoding="utf-8").read()
    assert '.workflow_url == $wf' not in workflow
