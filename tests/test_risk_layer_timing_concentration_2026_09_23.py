from automation.risk_layer_timing_concentration_2026_09_23 import _stats

def test_stats_empty_is_safe():
    result = _stats([], 0, 0)
    assert result["day_count"] == 0
    assert result["de_risk_fraction"] == 0.0
