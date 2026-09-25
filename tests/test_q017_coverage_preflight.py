from __future__ import annotations

from datetime import date

from automation.q017_coverage_preflight import (
    CFTC_TARGETS,
    STUDY_END,
    STUDY_START,
    TARGET_COMMON_CANDLES,
    _canonical_market,
    _date_in_window,
    _parse_alfred_rows,
)
from research.asset_universes import get_universe, list_universes


def test_q017_universe_is_fixed_and_symbol_disjoint():
    universe = get_universe("q017_coverage_first")
    assert universe.symbols == ("SMH", "SOXX", "IGE", "GDX", "DBO", "UNG", "FXB", "PPLT")
    used_elsewhere = {
        symbol
        for item in list_universes()
        if item.name != universe.name
        for symbol in item.symbols
    }
    assert not (set(universe.symbols) & used_elsewhere)
    assert universe.target_count == 3520
    assert TARGET_COMMON_CANDLES == 3500


def test_q017_study_window_is_fixed():
    assert STUDY_START == date(2011, 1, 1)
    assert STUDY_END == date(2025, 9, 24)


def test_q017_alfred_parser_enforces_vintage_column_and_filters_window():
    csv_text = (
        "observation_date,CPIAUCSL_20200102\\n"
        "2010-12-01,100.0\\n"
        "2011-01-01,101.0\\n"
        "2025-09-01,120.0\\n"
        "2025-10-01,121.0\\n"
    )
    values, header = _parse_alfred_rows(csv_text, "CPIAUCSL")
    assert header == "CPIAUCSL_20200102"
    assert list(values) == [date(2011, 1, 1), date(2025, 9, 1)]


def test_q017_cftc_market_matching_is_deterministic():
    market = _canonical_market("GOLD - COMMODITY EXCHANGE INC.")
    assert "GOLD" in market
    assert all(token in market for token in CFTC_TARGETS["GDX"])
    market = _canonical_market("BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE")
    assert all(token in market for token in CFTC_TARGETS["FXB"])


def test_q017_date_parser_is_strict_to_fixed_window():
    assert _date_in_window("2011-01-04") == date(2011, 1, 4)
    assert _date_in_window("09/23/2025") == date(2025, 9, 23)
    assert _date_in_window("2010-12-31") is None
    assert _date_in_window("2025-09-25") is None
