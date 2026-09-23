from automation.cs_rank_monotonicity_control_2026_09_23 import (
    _period_return,
    _pearson,
)

def test_period_return_compounds():
    assert abs(_period_return([0.10, -0.05]) - (1.10 * 0.95 - 1.0)) < 1e-15

def test_pearson_identical_series():
    assert abs(_pearson([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) - 1.0) < 1e-12

def test_pearson_constant_series_is_zero():
    assert _pearson([1.0, 1.0], [2.0, 3.0]) == 0.0