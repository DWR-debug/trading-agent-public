from portfolio.risk_overlay import correlation_matrix, drawdown_profile, exposure_concentration, joint_loss_rate, lagged_volatility_scale

def test_volatility_overlay_is_fail_safe():
    decision = lagged_volatility_scale((0.01, -0.005))
    assert decision.scale == 1.0
    assert decision.reason == "INSUFFICIENT_HISTORY"

def test_concentration_and_correlation():
    assert exposure_concentration({"a": 1.0, "b": 1.0}) == 0.5
    assert correlation_matrix({"a": (1, 2, 3), "b": (1, 2, 3)})["a"]["b"] == 1.0

def test_drawdown_and_joint_loss():
    assert drawdown_profile((0.1, -0.2, 0.1))["max_drawdown_percent"] > 0
    assert joint_loss_rate({"a": (-0.01, 0.02), "b": (-0.02, 0.01)}) == 0.5
