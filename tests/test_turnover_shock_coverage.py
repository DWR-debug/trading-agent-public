import json
from datetime import date, datetime, timedelta, timezone

import pytest

from automation import turnover_shock_coverage as module


def _preregistration():
    return json.loads(
        (module.ROOT / module.PREREGISTRATION).read_text(encoding="utf-8")
    )


def test_preregistration_freezes_the_complete_candidate_contract():
    spec = _preregistration()
    module._validate_preregistration(spec)
    assert tuple(spec["fixed_universe"]["symbols"]) == module.SYMBOLS
    assert spec["signal"]["reference"].endswith("previous_20_completed_daily_bars")
    assert spec["signal"]["shock_rule"] == "turnover_proxy / reference >= 2.0"
    assert spec["signal"]["direction"] == "long"
    assert spec["signal"]["holding_sessions"] == 1
    assert spec["signal"]["gross_exposure"] == 1.0


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("fixed_universe", "symbols"), ["AFL"]),
        (("signal", "shock_rule"), "turnover_proxy / reference >= 3.0"),
        (("signal", "direction"), "short"),
        (("signal", "holding_sessions"), 2),
        (("governance", "performance_evaluation"), True),
        (("safety", "orders_enabled"), True),
    ],
)
def test_preregistration_rejects_contract_or_governance_drift(path, value):
    spec = _preregistration()
    target = spec
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError):
        module._validate_preregistration(spec)


def _weekday_sessions(start, end):
    result = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            result.append(current)
        current += timedelta(days=1)
    return tuple(result)


def _synthetic_xnys_candles(count=24):
    sessions = _weekday_sessions(date(2025, 1, 2), date(2025, 3, 1))[:count]
    return tuple(
        type(
            "Bar",
            (),
            {
                "timestamp": datetime(
                    session.year, session.month, session.day, 21, tzinfo=timezone.utc
                ),
                "open": 10.0,
                "high": 11.0,
                "low": 9.0,
                "close": 10.0,
                "volume": 100.0,
            },
        )()
        for session in sessions
    )


def test_snapshot_pit_audit_checks_alignment_and_next_xnys_session(monkeypatch):
    bars = _synthetic_xnys_candles()
    monkeypatch.setattr(module, "TARGET_COMMON_CANDLES", len(bars))
    monkeypatch.setattr(module, "_xnys_sessions", _weekday_sessions)
    result = module._audit_frozen_snapshot(
        {symbol: bars for symbol in module.SYMBOLS}
    )
    assert result["common_bar_count"] == len(bars)
    assert result["eligible_signal_day_count_after_20_bar_warmup"] == 4
    assert result["mapped_session_count"] == len(bars)
    assert result["session_mapping_first"]["first_following_xnys_session"] > (
        result["session_mapping_first"]["signal_day"]
    )


def test_snapshot_pit_audit_rejects_missing_xnys_session(monkeypatch):
    bars = _synthetic_xnys_candles(count=25)
    monkeypatch.setattr(module, "TARGET_COMMON_CANDLES", len(bars) - 1)
    monkeypatch.setattr(module, "_xnys_sessions", _weekday_sessions)
    incomplete = bars[:10] + bars[11:]
    with pytest.raises(ValueError, match="missing or non-XNYS"):
        module._audit_frozen_snapshot(
            {symbol: incomplete for symbol in module.SYMBOLS}
        )


def test_snapshot_pit_audit_rejects_zero_volume(monkeypatch):
    bars = list(_synthetic_xnys_candles())
    monkeypatch.setattr(module, "TARGET_COMMON_CANDLES", len(bars))
    monkeypatch.setattr(module, "_xnys_sessions", _weekday_sessions)
    bars[0] = type(
        "Bar",
        (),
        {
            "timestamp": bars[0].timestamp,
            "open": 10.0,
            "high": 11.0,
            "low": 9.0,
            "close": 10.0,
            "volume": 0.0,
        },
    )()
    with pytest.raises(ValueError, match="invalid close or volume"):
        module._audit_frozen_snapshot({symbol: tuple(bars) for symbol in module.SYMBOLS})


def test_coverage_runner_does_not_claim_coverage_when_snapshot_is_insufficient(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        module,
        "build_frozen_snapshot",
        lambda *args, **kwargs: {
            "status": "DATA_INVALID",
            "coverage": {
                "errors": {"AFL": "missing history"},
                "per_symbol": {},
            },
            "snapshot_fingerprint": None,
            "data_snapshot": None,
        },
    )
    result = module.run_coverage(output_root=tmp_path)
    assert result["status"] == "DATA_INSUFFICIENT"
    assert result["pit_audit"] is None
    assert result["data_snapshot"] is None
    assert result["governance"]["signal_calculated"] is False
    assert result["governance"]["performance_evaluation"] is False
    assert json.loads(
        (tmp_path / module.TRIAL_ID / "turnover_shock_coverage.json").read_text()
    )["coverage_fingerprint"] == result["coverage_fingerprint"]


def test_coverage_is_insufficient_without_historical_source_vintages(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        module,
        "build_frozen_snapshot",
        lambda *args, **kwargs: {
            "status": "COVERAGE_PASSED",
            "coverage": {"errors": {}},
            "snapshot_fingerprint": "snapshot-fingerprint",
            "data_snapshot": {"datasets": []},
        },
    )
    monkeypatch.setattr(module, "load_frozen_snapshot", lambda *args: {})
    monkeypatch.setattr(
        module,
        "_audit_frozen_snapshot",
        lambda *args: {"common_bar_count": module.TARGET_COMMON_CANDLES},
    )
    result = module.run_coverage(output_root=tmp_path)
    assert result["status"] == "DATA_INSUFFICIENT"
    assert result["pit_audit"] is not None
    assert result["data_snapshot"] == {"datasets": []}
    assert result["source_vintage_guarantee"] is False
    assert any("source-vintage" in error for error in result["errors"])


def test_coverage_runner_fails_closed_when_safety_settings_change(monkeypatch):
    monkeypatch.setattr(module.settings, "ORDERS_ENABLED", True)
    monkeypatch.setattr(
        module,
        "build_frozen_snapshot",
        lambda *args, **kwargs: pytest.fail("snapshot must not be built"),
    )
    with pytest.raises(RuntimeError, match="paper-only safety"):
        module.run_coverage()
