from datetime import datetime, timezone, timedelta

from automation.hosted_fallback_guard import decide_fallback


def _run(created_at: datetime, *, status='completed', conclusion='success'):
    return {'id': 1, 'created_at': created_at.isoformat(), 'status': status, 'conclusion': conclusion}


def test_recent_success_does_not_trigger_fallback():
    now = datetime(2026, 9, 30, 18, 0, tzinfo=timezone.utc)
    decision = decide_fallback([_run(now - timedelta(minutes=10))], now=now)
    assert decision['run_fallback'] is False
    assert decision['reason'] == 'SELF_HOSTED_HEARTBEAT_FRESH'


def test_pending_stale_triggers_fallback():
    now = datetime(2026, 9, 30, 18, 0, tzinfo=timezone.utc)
    decision = decide_fallback([_run(now - timedelta(minutes=30), status='queued', conclusion=None)], now=now)
    assert decision['run_fallback'] is True
    assert decision['reason'] == 'SELF_HOSTED_RUN_STALE_PENDING'


def test_active_recent_run_does_not_trigger_fallback():
    now = datetime(2026, 9, 30, 18, 0, tzinfo=timezone.utc)
    decision = decide_fallback([_run(now - timedelta(minutes=10), status='in_progress', conclusion=None)], now=now)
    assert decision['run_fallback'] is False
    assert decision['reason'] == 'SELF_HOSTED_RUN_ACTIVE'


def test_no_heartbeat_triggers_fallback():
    now = datetime(2026, 9, 30, 18, 0, tzinfo=timezone.utc)
    decision = decide_fallback([], now=now)
    assert decision['run_fallback'] is True
    assert decision['reason'] == 'NO_SELF_HOSTED_HEARTBEAT'


def test_stale_completed_run_triggers_fallback():
    now = datetime(2026, 9, 30, 18, 0, tzinfo=timezone.utc)
    decision = decide_fallback([_run(now - timedelta(minutes=60), conclusion='success')], now=now)
    assert decision['run_fallback'] is True
    assert decision['reason'] == 'SELF_HOSTED_HEARTBEAT_STALE'