from datetime import datetime, timezone, timedelta

from automation.hosted_fallback_guard import decide_fallback


def _run(created_at: datetime, *, status="completed", conclusion="success"):
    return {"id": 1, "created_at": created_at.isoformat(), "status": status, "conclusion": conclusion}


def test_always_available_policy_never_triggers_automatic_fallback():
    now = datetime(2026, 10, 3, 14, 0, tzinfo=timezone.utc)
    for runs in (
        [_run(now - timedelta(hours=2), conclusion="success")],
        [_run(now - timedelta(minutes=30), status="queued", conclusion=None)],
        [],
    ):
        decision = decide_fallback(runs, now=now)
        assert decision["run_fallback"] is False
        assert decision["reason"] == "SELF_HOSTED_ASSUMED_ALWAYS_AVAILABLE"
