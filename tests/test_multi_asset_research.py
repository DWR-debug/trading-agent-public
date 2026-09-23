from datetime import datetime, timezone

from research.asset_universes import get_universe, list_universes


def test_asset_universe_priority_is_unique_and_ordered():
    universes = list_universes()
    priorities = [item.priority for item in universes]

    assert priorities == sorted(priorities)
    assert len(priorities) == len(set(priorities))


def test_small_cap_universe_is_first_research_tier():
    universe = get_universe("small_cap_high_volatility")

    assert universe.priority == 1
    assert universe.interval == "1d"
    assert universe.target_count == 2500
    assert universe.symbols


def test_penny_universe_is_separate():
    universe = get_universe("penny_stock")

    assert universe.priority == 3
    assert all(symbol for symbol in universe.symbols)
