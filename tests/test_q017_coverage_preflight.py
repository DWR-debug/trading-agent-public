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
    assert universe.symbols == ("SMH", "SOXX", "IGE", "DBO", "UNG", "PPLT", "CIBR", "LIT")
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
        "observation_date,CPIAUCSL_20200102\n"
        "2010-12-01,100.0\n"
        "2011-01-01,101.0\n"
        "2025-09-01,120.0\n"
        "2025-10-01,121.0\n"
    )
    values, header = _parse_alfred_rows(csv_text, "CPIAUCSL")
    assert header == "CPIAUCSL_20200102"
    assert list(values) == [date(2011, 1, 1), date(2025, 9, 1)]


def test_q017_cftc_market_matching_is_deterministic():
    market = _canonical_market("CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE")
    assert all(token in market for token in CFTC_TARGETS["DBO"])
    market = _canonical_market("PLATINUM - NEW YORK MERCANTILE EXCHANGE")
    assert all(token in market for token in CFTC_TARGETS["PPLT"])


def test_q017_date_parser_is_strict_to_fixed_window():
    assert _date_in_window("2011-01-04") == date(2011, 1, 4)
    assert _date_in_window("09/23/2025") == date(2025, 9, 23)
    assert _date_in_window("2010-12-31") is None
    assert _date_in_window("2025-09-25") is None

def test_q017_alfred_vintage_date_regex_accepts_iso_dates():
    import re

    html = '<option value="2025-09-24">2025-09-24</option><option value="2011-01-04">2011-01-04</option>'
    dates = sorted(set(re.findall(r'<option[^>]+value=[\"\'](20\d{2}-\d{2}-\d{2})[\"\']', html)))
    assert dates == ["2011-01-04", "2025-09-24"]


def test_q017_yahoo_coverage_delegates_to_canonical_snapshot(tmp_path, monkeypatch):
    import automation.q017_coverage_preflight as coverage
    from data.canonical_snapshot import SnapshotSpec

    calls = {}

    def build_snapshot(spec: SnapshotSpec):
        calls["spec"] = spec
        return {
            "status": "DATA_INVALID",
            "coverage": {
                "common_calendar_count": 2571,
                "per_symbol": {
                    symbol: {"status": "COVERAGE_VALID", "in_window_count": 3520}
                    for symbol in get_universe("q017_coverage_first").symbols
                },
            },
            "snapshot_fingerprint": "canonical-q017-fingerprint",
        }

    monkeypatch.setattr(coverage, "build_frozen_snapshot", build_snapshot)
    result = coverage._yahoo_coverage("q017_coverage_first", tmp_path)

    spec = calls["spec"]
    assert spec.universe == "q017_coverage_first"
    assert spec.symbols == get_universe("q017_coverage_first").symbols
    assert spec.interval == "1d"
    assert spec.requested_candles == 3520
    assert spec.target_common_candles == 3500
    assert spec.minimum_in_window_candles == 3500
    assert spec.study_start == STUDY_START
    assert spec.study_end == STUDY_END
    assert spec.dataset_subdir == "."
    assert result["status"] == "DATA_INVALID"
    assert result["common_calendar_count"] == 2571
    assert result["canonical_data_layer"] == "data/canonical_snapshot.py"
    assert result["snapshot_fingerprint"] == "canonical-q017-fingerprint"
    assert result["performance_evaluation"] is False
    assert result["selection_used"] is False
