from automation.spine_next_gate_router import plan_dispatches

def test_fresh_success_is_skipped():
    runs=[{"workflow_path":".github/workflows/q224-edgar-modern-source-gate.yml","name":"Q224","status":"completed","conclusion":"success","created_at":"2026-10-06T10:00:00Z"}]
    out=plan_dispatches(runs, now=__import__("datetime").datetime.fromisoformat("2026-10-06T10:30:00+00:00"), max_dispatches=5)
    q=[x for x in out["decisions"] if x["label"]=="Q224"][0]
    assert not q["eligible"]

def test_active_run_is_skipped():
    runs=[{"workflow_path":".github/workflows/q231-sec-foia-source-gate.yml","name":"Q231","status":"in_progress","conclusion":None,"created_at":"2026-10-06T10:00:00Z"}]
    out=plan_dispatches(runs, now=__import__("datetime").datetime.fromisoformat("2026-10-06T10:30:00+00:00"), max_dispatches=5)
    q=[x for x in out["decisions"] if x["label"]=="Q231"][0]
    assert not q["eligible"]

def test_q228_is_an_allowed_target():
    out=plan_dispatches([])
    assert ".github/workflows/q228-sec-correspondence-source-gate.yml" in {x["workflow"] for x in out["decisions"]}

def test_missing_history_is_dispatchable():
    out=plan_dispatches([], now=__import__("datetime").datetime.fromisoformat("2026-10-06T10:30:00+00:00"), max_dispatches=2)
    assert len(out["dispatches"])==2
