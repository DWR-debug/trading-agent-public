import json

from automation.paper_forward_loop import default_poll_seconds, run_loop


def test_run_loop_stops_after_max_iterations(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "automation.paper_forward_loop.run_once",
        lambda *args, **kwargs: calls.append((args, kwargs)) or {"schema_version": 2},
    )
    monkeypatch.setattr("automation.paper_forward_loop.time.sleep", lambda seconds: calls.append(seconds))
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({
        "schema_version": 1,
        "frozen": True,
        "candidate_id": "loop-test",
        "freeze_ref": "test",
        "symbol": "TEST",
        "interval": "1h",
        "initial_capital_eur": 500.0,
        "risk_per_trade": 0.01,
        "leverage": 1.0,
        "fee_rate": 0.001,
        "slippage_rate": 0.0005,
        "parameters": {
            "momentum": {"lookback": 1},
            "mean_reversion": {"window": 2, "threshold": 0.5},
        },
    }))
    run_loop(str(candidate), str(tmp_path / "state.json"), max_iterations=2)
    assert len(calls) == 3
    assert calls[-1] == 900


def test_default_poll_seconds():
    assert default_poll_seconds("1m") == 30
    assert default_poll_seconds("1h") == 900
    assert default_poll_seconds("1d") == 900
