from automation.h06_formal_performance_coverage import (
    LOOKBACK,
    REQUESTED_CANDLES,
    RESEARCH_CANDLES,
    SECTOR_MAP,
    SKIP,
    TARGET_COMMON_CANDLES,
    UNIVERSE,
    STUDY_END,
    STUDY_START,
)
from research.asset_universes import get_universe


def test_h06_formal_universe_is_fixed_and_balanced():
    universe = get_universe(UNIVERSE)
    assert tuple(
        symbol for members in SECTOR_MAP.values() for symbol in members
    ) == universe.symbols
    assert len(SECTOR_MAP) == 5
    assert all(len(members) == 3 for members in SECTOR_MAP.values())
    assert len(set(universe.symbols)) == 15


def test_h06_formal_geometry_is_fixed():
    assert LOOKBACK == 252
    assert SKIP == 21
    assert REQUESTED_CANDLES == 4000
    assert TARGET_COMMON_CANDLES == 3500
    assert RESEARCH_CANDLES == 2798
    assert TARGET_COMMON_CANDLES - RESEARCH_CANDLES == 702
    assert STUDY_START.isoformat() == "2011-01-01"
    assert STUDY_END.isoformat() == "2025-09-24"


def test_h06_formal_coverage_stays_performance_blind():
    source = __import__(
        "automation.h06_formal_performance_coverage",
        fromlist=["run"],
    )
    assert source.UNIVERSE == "validation_2026_09_26_h06_formal_performance"
