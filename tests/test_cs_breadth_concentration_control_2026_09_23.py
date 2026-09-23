from automation.cs_breadth_concentration_control_2026_09_23 import (
    BREADTHS,
    _max_drawdown,
    _period_return,
)


def test_breadth_ladder_is_preregistered():
    assert BREADTHS == (1, 2, 3, 4, 5)


def test_period_return_compounds():
    assert abs(_period_return([0.10, -0.05]) - (1.10 * 0.95 - 1.0)) < 1e-15


def test_max_drawdown_path():
    assert abs(_max_drawdown([0.10, -0.20, 0.05]) - (1.0 - 0.88 / 1.10)) < 1e-15
