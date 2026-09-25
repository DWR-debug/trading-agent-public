from automation.wide_search_h06_sector_neutral_residual_momentum_coverage import (
    LOOKBACK,
    RESEARCH_CANDLES,
    SECTOR_MAP,
)


def test_h06_sector_map_is_fixed_and_balanced():
    assert all(len(members) == 3 for members in SECTOR_MAP.values())
    assert len({
        symbol for members in SECTOR_MAP.values() for symbol in members
    }) == 15


def test_h06_research_geometry_is_fixed():
    assert LOOKBACK == 252
    assert RESEARCH_CANDLES == 2798
