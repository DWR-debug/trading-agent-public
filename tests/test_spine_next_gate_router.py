from automation.spine_next_gate_router import plan_dispatches

def test_focused_wave_has_no_automatic_spine_targets():
    out=plan_dispatches([])
    assert out["dispatches"] == []
    assert out["decisions"] == []

def test_focused_wave_is_fail_closed_with_run_history():
    runs=[{"workflow_path":".github/workflows/q224-edgar-modern-source-gate.yml","name":"Q224","status":"completed","conclusion":"success","created_at":"2026-10-06T10:00:00Z"}]
    out=plan_dispatches(runs, now=__import__("datetime").datetime.fromisoformat("2026-10-06T10:30:00+00:00"), max_dispatches=5)
    assert out["dispatches"] == []
    assert out["decisions"] == []
