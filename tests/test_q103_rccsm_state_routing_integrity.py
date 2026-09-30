from automation.q103_rccsm_state_routing_integrity import build_receipt


def test_q103_is_synthetic_only_and_passes() -> None:
    receipt = build_receipt()
    assert receipt["status"] == "RCCSM_STATE_ROUTING_STRUCTURAL_INTEGRITY_PASS"
    assert receipt["method"]["synthetic_only"] is True
    assert receipt["method"]["new_market_data"] is False
    assert receipt["method"]["new_backtest"] is False
    assert receipt["method"]["new_performance_trial"] is False
    assert receipt["method"]["uses_returns"] is False
    assert receipt["method"]["uses_holdout"] is False
    assert receipt["method"]["performance_authorization"] is False
    assert receipt["safety"]["paper_only"] is True
    assert receipt["safety"]["live_trading_enabled"] is False
    assert receipt["safety"]["orders_enabled"] is False
    assert receipt["safety"]["automatic_promotion"] is False


def test_q103_receipt_is_deterministic() -> None:
    assert build_receipt() == build_receipt()
