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
        "automation.wide_search_h06_sector_neutral_residual_momentum_repair_coverage",
        fromlist=["run"],
    )
    assert source.UNIVERSE == "validation_2026_09_25_sector_neutral_residual_momentum_repair"


def test_h06_repair_run_delegates_snapshot_creation_to_canonical_layer(monkeypatch, tmp_path):
    module = __import__(
        "automation.wide_search_h06_sector_neutral_residual_momentum_repair_coverage",
        fromlist=["run"],
    )

    class Bar:
        def __init__(self, timestamp, close):
            self.timestamp = timestamp
            self.open = close
            self.high = close
            self.low = close
            self.close = close
            self.volume = 1.0

    from datetime import datetime, timedelta, timezone

    base = datetime(2011, 1, 1, tzinfo=timezone.utc)
    timestamps = [base + timedelta(days=i) for i in range(3500)]
    assets = {
        symbol: tuple(
            Bar(ts, 100.0 + i + symbol_index * 0.1)
            for i, ts in enumerate(timestamps)
        )
        for symbol_index, symbol in enumerate(
            module.get_universe(module.UNIVERSE).symbols
        )
    }

    called = {}

    def fake_build(spec):
        called["spec"] = spec
        return {
            "status": "COVERAGE_PASSED",
            "snapshot_fingerprint": "snapshot-fp",
            "selected_common_calendar_start": timestamps[0].isoformat(),
            "data_snapshot": {
                "format": "csv_ohlcv_common_calendar",
                "datasets": [],
            },
            "coverage": {
                "common_calendar_count": module.TARGET_COMMON_CANDLES,
            },
            "safety": {
                "paper_only": True,
                "live_trading_enabled": False,
                "orders_enabled": False,
                "automatic_promotion": False,
            },
        }

    monkeypatch.setattr(module, "build_frozen_snapshot", fake_build)
    monkeypatch.setattr(module, "load_frozen_snapshot", lambda _: assets)

    result = module.run(output_path=tmp_path / "result.json")

    assert result["coverage"]["status"] == "COVERAGE_READY"
    assert result["snapshot_fingerprint"] == "snapshot-fp"
    assert called["spec"].requested_candles == module.REQUESTED_CANDLES
    assert called["spec"].target_common_candles == module.TARGET_COMMON_CANDLES
    assert called["spec"].minimum_in_window_candles == module.TARGET_COMMON_CANDLES
    assert called["spec"].dataset_subdir == "."
    assert called["spec"].study_start == module.STUDY_START
    assert called["spec"].study_end == module.STUDY_END
