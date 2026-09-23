from automation.risk_timing_control_63_vs_21 import (
    BASELINE_VOL_WINDOW,
    COUNTERFACTUAL_VOL_WINDOW,
    _vol,
)


def test_predeclared_windows_are_distinct():
    assert BASELINE_VOL_WINDOW == 63
    assert COUNTERFACTUAL_VOL_WINDOW == 21


def test_vol_uses_only_backward_observations():
    assert _vol([0.01] * 20, 21) is None
    value = _vol([0.01] * 20 + [0.02], 21)
    assert value is not None
    assert value > 0
