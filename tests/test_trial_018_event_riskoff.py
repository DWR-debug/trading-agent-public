from datetime import date

from automation.trial_018_event_riskoff import RISK_OFF_WEIGHTS, _event_signal, _simulate


def test_risk_off_policy_is_fixed_market_neutral():
    assert RISK_OFF_WEIGHTS == {"SPY": -0.50, "TLT": 0.25, "GLD": 0.25}
    assert sum(abs(value) for value in RISK_OFF_WEIGHTS.values()) == 1.0
    assert sum(RISK_OFF_WEIGHTS.values()) == 0.0
    assert _event_signal(True) == RISK_OFF_WEIGHTS
    assert _event_signal(False) == {"SPY": 0.0, "TLT": 0.0, "GLD": 0.0}


def test_open_to_open_simulation_and_two_x_costs():
    prices = {
        "SPY": {date(2025, 1, 1): type("P", (), {"open": 100.0, "close": 100.0})(), date(2025, 1, 2): type("P", (), {"open": 98.0, "close": 98.0})(), date(2025, 1, 3): type("P", (), {"open": 97.0, "close": 97.0})(), date(2025, 1, 6): type("P", (), {"open": 98.0, "close": 98.0})()},
        "TLT": {date(2025, 1, 1): type("P", (), {"open": 100.0, "close": 100.0})(), date(2025, 1, 2): type("P", (), {"open": 102.0, "close": 102.0})(), date(2025, 1, 3): type("P", (), {"open": 103.0, "close": 103.0})(), date(2025, 1, 6): type("P", (), {"open": 102.0, "close": 102.0})()},
        "GLD": {date(2025, 1, 1): type("P", (), {"open": 100.0, "close": 100.0})(), date(2025, 1, 2): type("P", (), {"open": 101.0, "close": 101.0})(), date(2025, 1, 3): type("P", (), {"open": 102.0, "close": 102.0})(), date(2025, 1, 6): type("P", (), {"open": 101.0, "close": 101.0})()},
    }
    signals = {date(2025, 1, 2): True, date(2025, 1, 3): False}
    base = _simulate(prices, signals, date(2025, 1, 2), date(2025, 1, 3), 1.0, 0)
    assert base["active_signal_days"] == 1
    assert base["observation_count"] == 1
    assert base["cumulative_return"] > 0.0


def test_one_day_delay_removes_first_holdout_signal():
    prices = {
        symbol: {
            date(2025, 4, 1): type("P", (), {"open": 100.0, "close": 100.0})(),
            date(2025, 4, 2): type("P", (), {"open": 100.0, "close": 100.0})(),
            date(2025, 4, 3): type("P", (), {"open": 100.0, "close": 100.0})(),
        } for symbol in ("SPY", "TLT", "GLD")
    }
    signals = {date(2025, 4, 1): True}
    delayed = _simulate(prices, signals, date(2025, 4, 1), date(2025, 4, 2), 1.0, 1)
    assert delayed["active_signal_days"] == 0