from datetime import datetime, timedelta, timezone
import json

from automation.paper_forward_shadow import PaperForwardShadowError, start_session, update_session
from backtesting.models import Candle


def make_trade_candidate():
    return {
        "schema_version": 1,
        "frozen": True,
        "candidate_id": "mtm-test-001",
        "freeze_ref": "test-freeze",
        "symbol": "TEST",
        "interval": "1h",
        "initial_capital_eur": 500.0,
        "risk_per_trade": 0.01,
        "leverage": 1.0,
        "fee_rate": 0.001,
        "slippage_rate": 0.0005,
        "parameters": {
            "momentum": {"lookback": 1},
            "mean_reversion": {"window": 2, "threshold": 0.001},
        },
    }


def make_rising_candles(count=6):
    origin = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=origin + timedelta(hours=i),
            open=100.0 + i,
            high=100.0 + i,
            low=100.0 + i,
            close=100.0 + i,
            volume=1000.0,
        )
        for i in range(count)
    )


def test_shadow_keeps_open_position_and_persists_mtm_ledger(tmp_path):
    path = tmp_path / "shadow.json"
    state = start_session(make_trade_candidate(), make_rising_candles(), path)
    portfolio = state["portfolio"]

    assert state["schema_version"] == 2
    assert len(portfolio["ledger"]) == state["candle_count"]
    assert portfolio["ledger"][-1]["market_timestamp_utc"] == state["last_market_timestamp_utc"]
    assert portfolio["current_position_side"] == "SELL"
    assert portfolio["current_position_exposure_eur"] > 0
    assert portfolio["unrealized_pnl_eur"] < 0
    assert portfolio["realized_pnl_eur"] == 0.0
    assert portfolio["trade_count"] == 0
    assert portfolio["final_equity_eur"] < 500.0
    assert portfolio["fees_paid_eur"] > 0
    assert portfolio["maximum_mtm_drawdown_percent"] >= 0


def test_tampered_mtm_ledger_is_rejected(tmp_path):
    path = tmp_path / "shadow.json"
    start_session(make_trade_candidate(), make_rising_candles(), path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["portfolio"]["ledger"][1]["equity_eur"] += 1.0
    path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        update_session(path, make_rising_candles(7))
    except PaperForwardShadowError as exc:
        assert "fingerprints" in str(exc)
    else:
        raise AssertionError("tampered MTM ledger was accepted")
