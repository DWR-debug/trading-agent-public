from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import automation.h06_mechanism_replication_coverage as coverage
from automation.h06_mechanism_replication_coverage import (
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
    assert coverage.UNIVERSE == "validation_2026_09_26_h06_mechanism_replication"


def test_h06_coverage_uses_canonical_snapshot_and_only_research_candles(
    tmp_path, monkeypatch
):
    base = datetime(2010, 1, 1, tzinfo=timezone.utc)

    class ResearchBoundedCandles(list):
        def __getitem__(self, index):
            if isinstance(index, slice):
                assert index.stop <= RESEARCH_CANDLES
            else:
                assert index < RESEARCH_CANDLES
            return super().__getitem__(index)

    candles = {}
    for symbol_index, symbol in enumerate(
        symbol for sector in SECTOR_MAP.values() for symbol in sector
    ):
        candles[symbol] = ResearchBoundedCandles(
            SimpleNamespace(
                timestamp=base + timedelta(days=index),
                close=100.0 + index * (1 + symbol_index / 10) + index % 31,
            )
            for index in range(TARGET_COMMON_CANDLES)
        )

    calls = {}

    def build_snapshot(spec):
        calls["spec"] = spec
        return {
            "status": "COVERAGE_PASSED",
            "coverage": {"common_calendar_count": TARGET_COMMON_CANDLES},
            "selected_common_calendar_start": base.isoformat(),
            "snapshot_fingerprint": "snapshot-fingerprint",
            "data_snapshot": {"format": "csv_ohlcv_common_calendar"},
            "safety": {
                "paper_only": True,
                "live_trading_enabled": False,
                "orders_enabled": False,
                "automatic_promotion": False,
            },
        }

    def load_snapshot(manifest_path):
        calls["manifest_path"] = manifest_path
        return candles

    monkeypatch.setattr(coverage, "build_frozen_snapshot", build_snapshot)
    monkeypatch.setattr(coverage, "load_frozen_snapshot", load_snapshot)

    result = coverage.run(output_path=tmp_path / "coverage.json")

    spec = calls["spec"]
    assert spec.universe == UNIVERSE
    assert spec.symbols == get_universe(UNIVERSE).symbols
    assert spec.interval == "1d"
    assert spec.requested_candles == REQUESTED_CANDLES
    assert spec.target_common_candles == TARGET_COMMON_CANDLES
    assert spec.minimum_in_window_candles == TARGET_COMMON_CANDLES
    assert spec.study_start == STUDY_START
    assert spec.study_end == STUDY_END
    assert spec.dataset_subdir == "."
    assert calls["manifest_path"] == (
        tmp_path / "h06_replication_datasets" / "snapshot_manifest.json"
    )
    assert result["canonical_data_layer"] == "data/canonical_snapshot.py"
    assert result["coverage"]["complete_decision_dates"] == (
        RESEARCH_CANDLES - LOOKBACK
    )
    assert result["governance"]["performance_evaluation"] is False
    assert result["governance"]["holdout_evaluation"] is False
    assert result["governance"]["holdout_used_for_selection"] is False


def test_h06_coverage_stops_when_canonical_snapshot_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(
        coverage,
        "build_frozen_snapshot",
        lambda spec: {
            "status": "DATA_INVALID",
            "coverage": {"failure_reason": "insufficient_common_calendar"},
        },
    )
    monkeypatch.setattr(
        coverage,
        "load_frozen_snapshot",
        lambda manifest_path: (_ for _ in ()).throw(AssertionError("snapshot loaded")),
    )

    try:
        coverage.run(output_path=tmp_path / "coverage.json")
    except RuntimeError as exc:
        assert "H06 canonical coverage failed" in str(exc)
    else:
        raise AssertionError("canonical coverage failure must stop the preflight")

    assert not (tmp_path / "coverage.json").exists()
