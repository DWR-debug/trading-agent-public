from automation.cs_mechanism_diagnosis_2026_09_23 import (
    _correlation,
    _period_return,
)


def test_period_return_compounds_path():
    result = _period_return([0.10, -0.05, 0.02])
    assert abs(result - (1.10 * 0.95 * 1.02 - 1.0)) < 1e-15


def test_correlation_is_one_for_identical_series():
    assert abs(_correlation([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) - 1.0) < 1e-12


def test_correlation_is_zero_for_constant_series():
    assert _correlation([1.0, 1.0], [2.0, 3.0]) == 0.0
