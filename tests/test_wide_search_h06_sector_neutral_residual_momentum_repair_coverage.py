from automation.wide_search_h06_sector_neutral_residual_momentum_repair_coverage import (
    LOOKBACK,
    RESEARCH_CANDLES,
    REQUESTED_CANDLES,
    SECTOR_MAP,
    SKIP,
    TARGET_COMMON_CANDLES,
    UNIVERSE,
    STUDY_END,
    STUDY_START,
)
from research.asset_universes import get_universe


def test_h06_sector_map_is_fixed_and_balanced():
    assert tuple(
        symbol for members in SECTOR_MAP.values() for symbol in members
    ) == get_universe(UNIVERSE).symbols
    assert len(SECTOR_MAP) == 5
    assert all(len(members) == 3 for members in SECTOR_MAP.values())
    assert len({
        symbol for members in SECTOR_MAP.values() for symbol in members
    }) == 15


def test_h06_research_geometry_is_fixed():
    assert LOOKBACK == 252
    assert SKIP == 21
    assert RESEARCH_CANDLES == 2798
    assert TARGET_COMMON_CANDLES == 3500
    assert REQUESTED_CANDLES == 4000
    assert TARGET_COMMON_CANDLES - RESEARCH_CANDLES == 702
    assert STUDY_START.isoformat() == "2011-01-01"
    assert STUDY_END.isoformat() == "2025-09-24"


def test_h06_preregistered_governance_is_coverage_only():
    source = __import__(
        "automation.wide_search_h06_sector_neutral_residual_momentum_coverage",
        fromlist=["run"],
    )
    assert source.UNIVERSE == "validation_2026_09_25_sector_neutral_residual_momentum_repair"
