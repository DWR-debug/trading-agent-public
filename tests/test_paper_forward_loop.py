import json

import pytest

from automation.paper_forward_loop import default_poll_seconds, run_loop, run_once
from automation.paper_forward_shadow import PaperForwardShadowError


def test_run_loop_stops_after_max_iterations(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "automation.paper_forward_loop._run_once_locked",
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
    assert calls[1] == 900


def test_default_poll_seconds():
    assert default_poll_seconds("1m") == 30
    assert default_poll_seconds("1h") == 900
    assert default_poll_seconds("1d") == 900


def test_missing_state_after_initialization_does_not_start_a_new_session(
    monkeypatch, tmp_path
):
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({
        "schema_version": 1,
        "frozen": True,
        "candidate_id": "missing-state-test",
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
    state = tmp_path / "state.json"
    starts = []
    monkeypatch.setattr(
        "automation.paper_forward_loop.start_from_binance",
        lambda value, path, **kwargs: starts.append(path) or {
            "run_id": "run-test",
            "candidate_fingerprint": "fingerprint-test",
        },
    )

    run_once(str(candidate), str(state))
    state.write_text("previous state existed")
    state.unlink()

    with pytest.raises(PaperForwardShadowError, match="state is missing"):
        run_once(str(candidate), str(state))
    assert starts == [state]

from pathlib import Path

def test_self_hosted_once_script_uses_user_profile_and_single_bounded_update():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "paper_forward_self_hosted_once.ps1"
    ).read_text(encoding="utf-8")

    assert '$env:LOCALAPPDATA "TradingAgent\\PaperForward"' in script
    assert "ops\\paper_forward\\operational_candidate.json" in script
    assert "--fetch-limit 100" in script
    assert "--max-iterations 1" in script
    assert "operations.jsonl" in script
    assert "PAPER_ONLY=True" not in script
    assert "LIVE_TRADING_ENABLED=True" not in script
    assert "ORDERS_ENABLED=True" not in script
    assert "automatic_promotion=True" not in script
    assert "--state $statePath" in script
    assert "--receipt $receiptPath" in script


def test_operational_canary_contract_is_frozen_and_simulation_only():
    candidate_path = (
        Path(__file__).resolve().parents[1]
        / "ops"
        / "paper_forward"
        / "operational_candidate.json"
    )
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))

    assert candidate["frozen"] is True
    assert candidate["candidate_id"] == "paper-forward-operational-canary-btcusdt-1h-v1"
    assert candidate["symbol"] == "BTCUSDT"
    assert candidate["interval"] == "1h"
    assert candidate["initial_capital_eur"] == 500.0
    assert candidate["leverage"] == 1.0
