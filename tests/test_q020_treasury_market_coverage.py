from datetime import date

import automation.q020_treasury_market_coverage as module


def test_fixed_geometry_and_safety_contract():
    assert module.UNIVERSE == "q018_official_event_source_validation"
    assert module.REQUESTED_CANDLES == 3520
    assert module.TARGET_COMMON_CANDLES == 3500
    assert module.STUDY_START == date(2011, 1, 1)
    assert module.STUDY_END == date(2025, 9, 24)


def test_coverage_status_is_based_only_on_canonical_geometry(monkeypatch, tmp_path):
    class U:
        name = module.UNIVERSE
        symbols = module.get_universe(module.UNIVERSE).symbols

    seen = {}

    def fake_build(spec):
        seen["spec"] = spec
        return {
            "status": "COVERAGE_PASSED",
            "coverage": {
                "common_calendar_count": 3500,
                "per_symbol": {
                    symbol: {"status": "COVERAGE_VALID"}
                    for symbol in U.symbols
                },
            },
            "snapshot_fingerprint": "q020-test-snapshot",
        }

    monkeypatch.setattr(module, "build_frozen_snapshot", fake_build)
    result = module.run(output_path=tmp_path / "coverage.json")

    assert result["status"] == "COVERAGE_VALIDATED"
    assert seen["spec"].requested_candles == 3520
    assert seen["spec"].target_common_candles == 3500
    assert seen["spec"].minimum_in_window_candles == 3500
    assert result["governance"]["performance_evaluation"] is False
    assert result["governance"]["holdout_used"] is False
    assert result["governance"]["performance_trial_authorized"] is False


def test_insufficient_common_calendar_is_not_rescued(monkeypatch, tmp_path):
    def fake_build(spec):
        return {
            "status": "COVERAGE_INSUFFICIENT",
            "coverage": {
                "common_calendar_count": 3269,
                "per_symbol": {},
            },
            "snapshot_fingerprint": "q020-insufficient",
        }

    monkeypatch.setattr(module, "build_frozen_snapshot", fake_build)
    result = module.run(output_path=tmp_path / "coverage.json")
    assert result["status"] == "DATA_INSUFFICIENT"
    assert result["required_common_calendar"] == 3500
