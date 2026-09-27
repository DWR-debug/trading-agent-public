from __future__ import annotations

from portfolio.q030_risk_mechanisms import (
    common_mode_exposure_scale,
    drawdown_throttle_scale,
    sleeve_volatility_scale,
)


def test_q035_risk_a_scale_is_bounded() -> None:
    assert 0.25 <= sleeve_volatility_scale([0.02 if i % 2 else -0.02 for i in range(63)]) <= 1.0


def test_q035_risk_b_thresholds_are_frozen() -> None:
    assert drawdown_throttle_scale([-0.06]) == 0.50
    assert drawdown_throttle_scale([-0.10]) == 0.25


def test_q035_risk_c_trigger_is_frozen() -> None:
    a=[0.01,-0.02,0.03,-0.01,0.02]*13
    b=list(a)
    assert common_mode_exposure_scale({"A":a,"B":b},{"A":0.5,"B":0.5},window=63,trigger=0.60,triggered_scale=0.50)==0.50
