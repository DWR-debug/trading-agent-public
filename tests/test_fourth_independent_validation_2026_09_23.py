from automation.fourth_independent_validation_2026_09_23 import (
    CS_UNIVERSE,
    HOLDOUT_COUNT,
    RESEARCH_COUNT,
    TARGET_COUNT,
    TREND_UNIVERSE,
    _assert_global_disjoint,
)
from research.asset_universes import get_universe


def test_fourth_validation_universes_are_fully_disjoint():
    _assert_global_disjoint()


def test_fourth_validation_universes_have_fixed_shape():
    trend = get_universe(TREND_UNIVERSE)
    cs = get_universe(CS_UNIVERSE)
    assert len(trend.symbols) == 8
    assert len(cs.symbols) == 5
    assert TARGET_COUNT == 3500
    assert RESEARCH_COUNT == 2798
    assert HOLDOUT_COUNT == 700
    assert trend.target_count == TARGET_COUNT
    assert cs.target_count == TARGET_COUNT
    assert set(trend.symbols).isdisjoint(cs.symbols)


def test_fourth_validation_symbols_are_exactly_preregistered():
    assert get_universe(TREND_UNIVERSE).symbols == (
        "SCHB", "VO", "VB", "VXF", "VXUS", "VGK", "IAU", "AGG",
    )
    assert get_universe(CS_UNIVERSE).symbols == (
        "KBE", "KCE", "IYZ", "IHI", "XHB",
    )
