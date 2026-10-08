from automation.q218_explicit_performance_authorization import AUTH_ID, TRIAL_ID


def test_q218_authorization_contract_constants():
    assert TRIAL_ID == "T-2026-10-08-Q218-PERFORMANCE-01"
    assert AUTH_ID == "AUTH-Q218-2026-10-08-ONE-SHOT-01"


def test_q218_authorization_never_creates_execution_trigger():
    from pathlib import Path
    source = Path("automation/q218_explicit_performance_authorization.py").read_text(encoding="utf-8")
    assert '"execution_trigger_created": False' in source
