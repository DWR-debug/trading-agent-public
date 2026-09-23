from automation.risk_layer_attribution_2026_09_23 import _pf


def test_profit_factor_conversion():
    assert _pf("inf") == float("inf")
    assert _pf(1.25) == 1.25
