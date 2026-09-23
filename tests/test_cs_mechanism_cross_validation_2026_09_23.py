from automation.cs_mechanism_cross_validation_2026_09_23 import (
    _correlation,
    _period_return,
)


def test_period_return_compounds():
    assert abs(_period_return([0.10, -0.05]) - (1.10 * 0.95 - 1.0)) < 1e-15


def test_correlation_identical_series():
    assert abs(_correlation([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) - 1.0) < 1e-12
