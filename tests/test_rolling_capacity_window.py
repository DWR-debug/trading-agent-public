from __future__ import annotations

import json
from datetime import datetime

def test_current_bounded_capacity_window_contract():
    p = json.loads(open("research/run_requests/rolling_capacity_window_2026-10-05.json", encoding="utf-8").read())
    start = datetime.fromisoformat(p["start_utc"].replace("Z","+00:00"))
    end = datetime.fromisoformat(p["end_utc"].replace("Z","+00:00"))
    assert (end-start).total_seconds() == 120 * 60
    assert p["cadence_minutes"] == 10
    assert p["safety"]["PAPER_ONLY"] is True
    assert all(p["safety"][k] is False for k in ("performance","holdout_selection","ranking","tuning","promotion","live_execution"))

def test_wave_order():
    p = json.loads(open("research/run_requests/rolling_capacity_window_2026-10-05.json", encoding="utf-8").read())
    assert [x["start_after_minutes"] for x in p["phases"]] == [0,30,60,90]
    assert all(x["workflows"] for x in p["phases"])
