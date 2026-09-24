from automation.research_orchestrator import _state_snapshot


def test_snapshot_is_safe_and_credit_free_by_default():
    snapshot = _state_snapshot(
        mode="observe",
        universe="benchmark",
        status="OBSERVATION_ONLY",
    )
    assert snapshot["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }
    assert snapshot["agent_usage"]["paid_api_budget_usd"] == 0.0
    assert snapshot["agent_usage"]["auto_paid_api_calls"] is False
