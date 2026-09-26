from datetime import date
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from automation.q020_treasury_auction_performance import (
    TRIAL_ID,
    _fp,
    _gates,
    _positions,
    _signal_events,
    _stats,
)


def test_signal_event_sequence_is_deterministic():
    rows = [
        {"record_date": "2011-01-10", "security_type": "Note", "security_term": "10-Year", "auction_date": "2011-01-06", "cusip": "A", "bid_to_cover_ratio": "2.00"},
        {"record_date": "2011-02-10", "security_type": "Note", "security_term": "10-Year", "auction_date": "2011-02-06", "cusip": "B", "bid_to_cover_ratio": "2.10"},
        {"record_date": "2011-03-10", "security_type": "Note", "security_term": "10-Year", "auction_date": "2011-03-06", "cusip": "C", "bid_to_cover_ratio": "2.05"},
    ]
    events, fp = _signal_events(rows, [date(2011, 1, 11), date(2011, 2, 11), date(2011, 3, 11)])
    assert [x["signal"] for x in events] == [None, 1, -1]
    assert [x["next_eligible_common_trading_date"] for x in events] == ["2011-01-11", "2011-02-11", "2011-03-11"]
    assert fp == _fp(events)


def test_positions_aggregate_multiple_events_per_session():
    events = [
        {"signal": 1, "next_eligible_common_trading_date": "2025-01-02"},
        {"signal": -1, "next_eligible_common_trading_date": "2025-01-02"},
        {"signal": 1, "next_eligible_common_trading_date": "2025-01-03"},
    ]
    assert _positions(events) == {date(2025, 1, 2): 0, date(2025, 1, 3): 1}


def test_period_metrics_compounds_and_calculates_drawdown():
    rows = [{"net_return": 0.10, "scale": 1.0}, {"net_return": -0.05, "scale": 1.0}]
    result = _stats(rows, 0, len(rows))
    assert result["period_return"] == pytest.approx(0.045)
    assert result["max_drawdown_percent"] == pytest.approx(5.0)


def test_gate_bundle_rejects_when_research_return_is_negative():
    base = {
        "research": {"period_return": -0.01, "max_drawdown_percent": 0, "profit_factor": 0.0},
        "holdout": {"period_return": 0.01, "max_drawdown_percent": 0, "profit_factor": 2.0},
        "rolling": {"overall_profit_factor": 2.0, "profitable_window_ratio": 1.0, "average_drawdown_percent": 0},
        "total_return_sensitivity_holdout": {"period_return": 0.01},
    }
    scenarios = {
        "base": base,
        "stress_1_5x": {"holdout": base["holdout"]},
        "stress_2x": {"holdout": base["holdout"]},
    }
    gates = _gates(scenarios)
    assert gates["all_absolute_passed"] is False
    assert gates["absolute"]["research_return_positive"] is False


def test_preregistration_is_fixed_and_not_authorized():
    spec = json.loads(
        (
            ROOT
            / "research"
            / "preregistrations"
            / "q020_treasury_auction_performance_repair_2026_09_26.json"
        ).read_text(encoding="utf-8")
    )
    assert spec["trial_id"] == TRIAL_ID
    assert spec["status"] == "PREREGISTERED_DESIGN_ONLY"
    assert spec["coverage_basis"]["snapshot_fingerprint"] == (
        "70cff5df1b92f4f7db2ea09bdc9999abff93dd4230ad4ea5df6e5da204076ef8"
    )
    assert spec["signal_contract"]["source_contract_fingerprint"] == (
        "13072dbed7d60684f4a4fb8a3de69555cae83c66f3cfdfb603b9ed2a4b1c225b"
    )
    assert spec["signal_contract"]["signals_fingerprint"] == (
        "8af45e4eb7267266da10eb28cf5287eea1ff3572f38736382f1b004abf86c208"
    )
    assert spec["execution_model"]["entry"].startswith("market open")
    assert spec["execution_model"]["exit"].startswith("same-session market close")
    assert spec["evaluation_geometry"] == {
        "frozen_candles": 3500,
        "evaluation_return_periods": 3498,
        "excluded_initial_return_periods": 1,
        "research_periods": 2798,
        "holdout_periods": 700,
        "rolling_research_windows": 5,
        "rolling_method": "five contiguous research windows; final window absorbs remainder",
    }
    assert spec["authorization"]["performance_execution_authorized"] is False
    assert spec["safety"]["paper_only"] is True
    assert spec["safety"]["live_trading_enabled"] is False
    assert spec["safety"]["orders_enabled"] is False
    assert spec["safety"]["automatic_promotion"] is False
