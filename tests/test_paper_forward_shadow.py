from datetime import datetime, timedelta, timezone
import json
import multiprocessing

import pytest

from automation.paper_forward_loop import run_loop, run_once
from automation.paper_forward_shadow import (
    PaperForwardShadowError,
    process_lock,
    start_session,
    stop_session,
    update_session,
)
from backtesting.models import Candle


def make_candidate():
    return {
        "schema_version": 1,
        "frozen": True,
        "candidate_id": "frozen-example-001",
        "freeze_ref": "preregistration-or-commit-reference",
        "symbol": "TEST",
        "interval": "1h",
        "initial_capital_eur": 1000.0,
        "risk_per_trade": 0.01,
        "leverage": 1.0,
        "fee_rate": 0.001,
        "slippage_rate": 0.0005,
        "parameters": {
            "momentum": {"lookback": 1},
            "mean_reversion": {"window": 2, "threshold": 0.5},
        },
    }


def make_candles(count, start=0):
    origin = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=origin + timedelta(hours=index),
            open=100.0 + index,
            high=100.0 + index,
            low=100.0 + index,
            close=100.0 + index,
            volume=1000.0,
        )
        for index in range(start, count)
    )


def _hold_process_lock(state_path, receipt_path, acquired, release):
    with process_lock(state_path, receipt_path):
        acquired.set()
        release.wait(timeout=15)


def test_start_and_update_are_reproducible_and_resume_from_saved_portfolio(tmp_path):
    initial = start_session(make_candidate(), make_candles(8), tmp_path / "one.json")
    same_run = start_session(make_candidate(), make_candles(8), tmp_path / "two.json")

    assert initial["run_id"] == same_run["run_id"]
    assert initial["input_fingerprint"] == same_run["input_fingerprint"]
    assert initial["signal_fingerprint"] == same_run["signal_fingerprint"]
    assert initial["safety"] == {
        "PAPER_ONLY": True,
        "LIVE_TRADING_ENABLED": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    assert initial["portfolio"]["initial_capital_eur"] == 1000.0
    assert initial["portfolio"]["maximum_trade_exposure_eur"] >= 0
    assert initial["portfolio"]["trade_count"] >= 0
    assert isinstance(initial["portfolio"]["realized_pnl_eur"], float)
    assert isinstance(initial["portfolio"]["gross_traded_notional_eur"], float)
    assert isinstance(initial["portfolio"]["maximum_realized_drawdown_percent"], float)
    assert initial["schema_version"] == 2
    assert initial["portfolio"]["current_position_exposure_eur"] >= 0.0
    assert len(initial["portfolio"]["ledger"]) == initial["candle_count"]

    state_path = tmp_path / "one.json"
    appended = update_session(state_path, make_candles(12, start=7))
    assert appended["run_id"] == initial["run_id"]
    assert appended["input_fingerprint"] != initial["input_fingerprint"]
    assert appended["schema_version"] == 2
    assert appended["candle_count"] == 12
    assert len(appended["portfolio"]["ledger"]) == appended["candle_count"]
    assert appended["updated_at_utc"] == make_candles(12)[-1].timestamp.isoformat()

    duplicate = update_session(state_path, make_candles(8))
    assert duplicate["input_fingerprint"] == appended["input_fingerprint"]
    stopped = stop_session(state_path)
    assert stopped["status"] == "STOPPED"
    assert stopped["stopped_at_utc"] == stopped["last_market_timestamp_utc"]
    with pytest.raises(PaperForwardShadowError, match="RUNNING"):
        update_session(state_path, make_candles(13, start=12))


def test_rejects_unfrozen_candidate_and_market_data_gaps(tmp_path):
    candidate = make_candidate()
    candidate["frozen"] = False
    with pytest.raises(PaperForwardShadowError, match="frozen=true"):
        start_session(candidate, make_candles(4), tmp_path / "state.json")

    gap = (make_candles(2)[0], make_candles(3)[2])
    with pytest.raises(PaperForwardShadowError, match="contiguous"):
        start_session(make_candidate(), gap, tmp_path / "gap.json")

    path = tmp_path / "append-gap.json"
    start_session(make_candidate(), make_candles(3), path)
    with pytest.raises(PaperForwardShadowError, match="contiguously"):
        update_session(path, make_candles(5, start=4))


def test_rejects_forward_cost_contract_drift(tmp_path):
    candidate = make_candidate()
    candidate["fee_rate"] = 0.0005
    with pytest.raises(PaperForwardShadowError, match="Execution-cost contract"):
        start_session(candidate, make_candles(3), tmp_path / "state.json")


def test_persists_feed_receipt_fingerprint_with_state_provenance(tmp_path):
    path = tmp_path / "state.json"
    start_session(make_candidate(), make_candles(3), path)
    updated = update_session(
        path,
        make_candles(4, start=2),
        feed_receipt_fingerprint="a" * 64,
        feed_candle_fingerprint="b" * 64,
        feed_fetch_fingerprint="c" * 64,
    )

    assert updated["feed_receipt_fingerprint"] == "a" * 64
    assert updated["feed_candle_fingerprint"] == "b" * 64
    assert updated["feed_fetch_fingerprint"] == "c" * 64
    assert json.loads(path.read_text(encoding="utf-8"))["input_fingerprint"] == updated[
        "input_fingerprint"
    ]

    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["feed_receipt_fingerprint"] = "d" * 64
    path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(PaperForwardShadowError, match="fingerprints"):
        update_session(path, make_candles(5, start=3))


def test_rejects_changes_to_already_observed_candles(tmp_path):
    path = tmp_path / "state.json"
    start_session(make_candidate(), make_candles(5), path)
    changed = list(make_candles(5))
    old = changed[2]
    changed[2] = Candle(
        timestamp=old.timestamp,
        open=old.open,
        high=old.high + 1,
        low=old.low,
        close=old.close,
        volume=old.volume,
    )
    with pytest.raises(PaperForwardShadowError, match="changed"):
        update_session(path, (*changed, *make_candles(6, start=5)))


@pytest.mark.parametrize(
    ("setting", "unsafe_value"),
    [
        ("PAPER_ONLY", False),
        ("LIVE_TRADING_ENABLED", True),
        ("ORDERS_ENABLED", True),
        ("AUTOMATIC_PROMOTION", True),
    ],
)
def test_requires_paper_only_safety_configuration(
    tmp_path, monkeypatch, setting, unsafe_value
):
    from config import settings

    monkeypatch.setattr(settings, setting, unsafe_value)
    with pytest.raises(PaperForwardShadowError, match="requires PAPER_ONLY=True"):
        start_session(make_candidate(), make_candles(3), tmp_path / "state.json")


def test_state_is_json_and_never_enables_orders_or_promotion(tmp_path):
    path = tmp_path / "state.json"
    state = start_session(make_candidate(), make_candles(5), path)
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["run_id"] == state["run_id"]
    assert persisted["safety"]["orders_enabled"] is False
    assert persisted["safety"]["automatic_promotion"] is False


def test_update_rejects_tampered_persisted_fingerprints(tmp_path):
    for tampered_field in ("signal_fingerprint", "portfolio"):
        path = tmp_path / f"{tampered_field}.json"
        start_session(make_candidate(), make_candles(5), path)
        state = json.loads(path.read_text(encoding="utf-8"))
        state[tampered_field] = "0" * 64
        path.write_text(json.dumps(state), encoding="utf-8")

        with pytest.raises(PaperForwardShadowError, match="fingerprints"):
            update_session(path, make_candles(6, start=5))


def test_resume_polling_uses_validated_state_without_candidate_file(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    state = start_session(make_candidate(), make_candles(3), state_path)
    sleeps = []
    monkeypatch.setattr(
        "automation.paper_forward_loop.update_from_binance",
        lambda *args, **kwargs: state,
    )
    monkeypatch.setattr(
        "automation.paper_forward_loop.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )

    run_loop(
        str(tmp_path / "missing-candidate.json"),
        str(state_path),
        max_iterations=2,
    )

    assert sleeps == [900]


@pytest.mark.parametrize(
    (
        "locked_state",
        "locked_receipt",
        "attempt_state",
        "attempt_receipt",
        "has_existing_state",
    ),
    [
        ("same-state.json", "receipt.json", "same-state.json", "receipt.json", False),
        (
            "other-state.json",
            "shared-receipt.json",
            "second-state.json",
            "shared-receipt.json",
            True,
        ),
    ],
)
def test_competing_process_cannot_start_or_update_locked_state_or_receipt(
    tmp_path,
    locked_state,
    locked_receipt,
    attempt_state,
    attempt_receipt,
    has_existing_state,
):
    attempted_state_path = tmp_path / attempt_state
    if has_existing_state:
        start_session(make_candidate(), make_candles(3), attempted_state_path)

    context = multiprocessing.get_context("spawn")
    acquired = context.Event()
    release = context.Event()
    process = context.Process(
        target=_hold_process_lock,
        args=(
            str(tmp_path / locked_state),
            str(tmp_path / locked_receipt),
            acquired,
            release,
        ),
    )
    process.start()
    try:
        assert acquired.wait(timeout=10)
        with pytest.raises(PaperForwardShadowError, match="Cannot acquire.*lock"):
            run_once(
                str(tmp_path / "candidate-does-not-need-to-exist.json"),
                str(attempted_state_path),
                receipt_path=str(tmp_path / attempt_receipt),
            )
    finally:
        release.set()
        process.join(timeout=10)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)

    assert process.exitcode == 0
    with process_lock(
        attempted_state_path, tmp_path / attempt_receipt
    ):
        pass
