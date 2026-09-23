from automation.risk_layer_sleeve_timing_2026_09_23 import _corr

def test_corr_zero_variance_safe():
    assert _corr([1.0, 1.0], [1.0, 2.0]) == 0.0
