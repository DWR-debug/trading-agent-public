"""Incremental paper-only shadow simulation for one already-frozen candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

from risk.risk_engine import calculate_position
from backtesting.models import Candle
from config import settings
from config.parameters import (
    MeanReversionParameters,
    MomentumParameters,
    StrategyParameters,
)
from execution.cost_contract import (
    ExecutionCostCompatibilityError,
    validate_research_cost_compatibility,
)
from strategies.signals import SignalType
from strategies.strategy_engine import StrategyEngine

_INTERVALS = {
    "1m": timedelta(minutes=1),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}


class PaperForwardShadowError(ValueError):
    """Raised when the shadow-run input or persisted state is invalid."""


def _canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _assert_safety() -> None:
    if (
        settings.PAPER_ONLY is not True
        or settings.LIVE_TRADING_ENABLED is not False
        or settings.ORDERS_ENABLED is not False
        or settings.AUTOMATIC_PROMOTION is not False
    ):
        raise PaperForwardShadowError(
            "Shadow simulation requires PAPER_ONLY=True, "
            "LIVE_TRADING_ENABLED=False, ORDERS_ENABLED=False, "
            "and AUTOMATIC_PROMOTION=False."
        )


def _object(value: Any, required: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != required:
        raise PaperForwardShadowError(
            f"{label} must contain exactly these fields: {sorted(required)}."
        )
    return value


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PaperForwardShadowError(f"{label} must be a non-empty string.")
    return value.strip()


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise PaperForwardShadowError(f"{label} must have a timezone.")
    return value.astimezone(timezone.utc)


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise PaperForwardShadowError("Candle timestamp must be an ISO string.")
    try:
        return _timestamp(datetime.fromisoformat(value.replace("Z", "+00:00")), "timestamp")
    except ValueError as exc:
        raise PaperForwardShadowError(f"Invalid candle timestamp: {value!r}.") from exc


def _validate_candidate(
    candidate: Any,
) -> tuple[dict[str, Any], StrategyParameters]:
    fields = {
        "schema_version",
        "frozen",
        "candidate_id",
        "freeze_ref",
        "symbol",
        "interval",
        "initial_capital_eur",
        "risk_per_trade",
        "leverage",
        "fee_rate",
        "slippage_rate",
        "parameters",
    }
    value = _object(candidate, fields, "Frozen candidate")
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or value["frozen"] is not True
    ):
        raise PaperForwardShadowError(
            "Candidate must use schema_version=1 and frozen=true."
        )
    _nonempty_string(value["candidate_id"], "candidate_id")
    _nonempty_string(value["freeze_ref"], "freeze_ref")
    _nonempty_string(value["symbol"], "symbol")
    interval = _nonempty_string(value["interval"], "interval")
    if interval not in _INTERVALS:
        raise PaperForwardShadowError(f"Unsupported candle interval: {interval}.")
    for key in ("initial_capital_eur", "risk_per_trade", "leverage", "fee_rate", "slippage_rate"):
        number = value[key]
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            raise PaperForwardShadowError(f"{key} must be a finite number.")
    if (
        value["initial_capital_eur"] <= 0
        or not 0 < value["risk_per_trade"] <= settings.RISK_PER_TRADE
        or not 1.0 <= value["leverage"] <= settings.MAX_LEVERAGE
        or value["fee_rate"] < 0
        or value["slippage_rate"] < 0
    ):
        raise PaperForwardShadowError(
            "Capital, risk, leverage, fees, or slippage violate configured limits."
        )
    try:
        validate_research_cost_compatibility(
            fee_rate=float(value["fee_rate"]),
            slippage_rate=float(value["slippage_rate"]),
        )
    except ExecutionCostCompatibilityError as exc:
        raise PaperForwardShadowError(
            f"Execution-cost contract is not research-compatible: {exc}"
        ) from exc

    parameter_fields = {"momentum", "mean_reversion"}
    params = _object(value["parameters"], parameter_fields, "parameters")
    momentum = _object(params["momentum"], {"lookback"}, "parameters.momentum")
    reversion = _object(
        params["mean_reversion"], {"window", "threshold"}, "parameters.mean_reversion"
    )
    if type(momentum["lookback"]) is not int or type(reversion["window"]) is not int:
        raise PaperForwardShadowError("Strategy lookback/window values must be integers.")
    threshold = reversion["threshold"]
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not math.isfinite(threshold)
        or threshold <= 0
    ):
        raise PaperForwardShadowError("Mean-reversion threshold must be finite and positive.")
    parameters = StrategyParameters(
        momentum=MomentumParameters(lookback=momentum["lookback"]),
        mean_reversion=MeanReversionParameters(
            window=reversion["window"], threshold=reversion["threshold"]
        ),
    )
    candidate_value = dict(value)
    candidate_value["candidate_id"] = candidate_value["candidate_id"].strip()
    candidate_value["freeze_ref"] = candidate_value["freeze_ref"].strip()
    candidate_value["symbol"] = candidate_value["symbol"].strip()
    return candidate_value, parameters


def _candle_record(candle: Candle) -> dict[str, Any]:
    return {
        "timestamp": _timestamp(candle.timestamp, "timestamp").isoformat(),
        "open": candle.open,
        "high": candle.high,
        "low": candle.low,
        "close": candle.close,
        "volume": candle.volume,
    }


def _parse_candle(value: Any) -> Candle:
    fields = {"timestamp", "open", "high", "low", "close", "volume"}
    item = _object(value, fields, "Candle")
    values: dict[str, float] = {}
    for key in ("open", "high", "low", "close", "volume"):
        raw = item[key]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            raise PaperForwardShadowError(f"Candle {key} must be a finite number.")
        values[key] = float(raw)
    try:
        return Candle(timestamp=_parse_timestamp(item["timestamp"]), **values)
    except ValueError as exc:
        raise PaperForwardShadowError(f"Invalid candle: {exc}") from exc


def load_candles(path: str | Path) -> tuple[Candle, ...]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PaperForwardShadowError(f"Cannot read candle input: {exc}") from exc
    if not isinstance(payload, list) or not payload:
        raise PaperForwardShadowError("Candle input must be a non-empty JSON array.")
    return tuple(_parse_candle(item) for item in payload)


def _validate_candles(candles: Sequence[Candle], interval: str) -> tuple[Candle, ...]:
    if not candles:
        raise PaperForwardShadowError("At least one market candle is required.")
    ordered = tuple(candles)
    previous: datetime | None = None
    for candle in ordered:
        timestamp = _timestamp(candle.timestamp, "timestamp")
        if not all(
            math.isfinite(value)
            for value in (candle.open, candle.high, candle.low, candle.close, candle.volume)
        ):
            raise PaperForwardShadowError("Candle values must be finite.")
        if previous is not None and timestamp - previous != _INTERVALS[interval]:
            raise PaperForwardShadowError(
                "Candles must be strictly ordered and contiguous; duplicates and data gaps are rejected."
            )
        previous = timestamp
    return ordered


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


@contextmanager
def process_lock(
    state_path: str | Path, receipt_path: str | Path | None = None
) -> Iterator[None]:
    targets = [state_path]
    if receipt_path is not None:
        targets.append(receipt_path)
    paths = {
        os.path.normcase(str(path)): path
        for path in (Path(target).resolve() for target in targets)
    }
    lock_paths = sorted(
        (path.with_name(path.name + ".lock") for path in paths.values()),
        key=lambda path: os.path.normcase(str(path)),
    )
    open_files = []
    locked_files = []
    try:
        for lock_path in lock_paths:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            stream = lock_path.open("a+b")
            open_files.append(stream)
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise PaperForwardShadowError(
                    "Cannot acquire paper-forward state or receipt lock "
                    f"(another process may hold it): {lock_path}."
                ) from exc
            locked_files.append(stream)
        yield
    finally:
        try:
            for stream in reversed(locked_files):
                if os.name == "nt":
                    import msvcrt

                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            for stream in reversed(open_files):
                stream.close()


def _initialization_marker_path(state_path: str | Path) -> Path:
    path = Path(state_path)
    return path.with_name(path.name + ".initialized.json")


def _mark_initialized(state_path: str | Path, state: dict[str, Any]) -> None:
    marker = _initialization_marker_path(state_path)
    payload = {
        "schema_version": 1,
        "run_id": state["run_id"],
        "candidate_fingerprint": state["candidate_fingerprint"],
    }
    if marker.exists():
        try:
            persisted = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PaperForwardShadowError(
                f"Cannot read paper-forward initialization marker: {exc}"
            ) from exc
        if persisted != payload:
            raise PaperForwardShadowError(
                "Paper-forward initialization marker does not match the session state."
            )
        return
    _atomic_write(marker, payload)


def _signal_stream(
    candidate: dict[str, Any], parameters: StrategyParameters, candles: Sequence[Candle]
) -> tuple[list[Any], str]:
    engine = StrategyEngine(parameters=parameters)
    prices: list[float] = []
    signals = []
    fingerprint_rows = []
    for candle in candles:
        prices.append(candle.close)
        try:
            signal = engine.generate_signal(candidate["symbol"], prices)
        except ValueError:
            signal = None
        signals.append(signal)
        fingerprint_rows.append(
            {
                "timestamp": _candle_record(candle)["timestamp"],
                "signal": signal.signal.value if signal else None,
                "confidence": signal.confidence if signal else None,
                "reason": signal.reason if signal else None,
            }
        )
    return signals, _fingerprint(fingerprint_rows)


def _snapshot(
    candidate: dict[str, Any],
    parameters: StrategyParameters,
    candles: Sequence[Candle],
    run_id: str,
    candidate_fingerprint: str,
    started_at: str,
    status: str,
    stopped_at: str | None = None,
    feed_receipt_fingerprint: str | None = None,
    feed_candle_fingerprint: str | None = None,
    feed_fetch_fingerprint: str | None = None,
) -> dict[str, Any]:
    signal_values, signal_fingerprint = _signal_stream(candidate, parameters, candles)
    cash = float(candidate["initial_capital_eur"])
    realized_pnl = 0.0
    cumulative_fees = 0.0
    gross_traded_notional = 0.0
    maximum_trade_exposure = 0.0
    realized_peak = cash
    mtm_peak = cash
    maximum_realized_drawdown = 0.0
    maximum_mtm_drawdown = 0.0
    open_position: dict[str, Any] | None = None
    trades: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []

    for candle, signal in zip(candles, signal_values):
        action = "HOLD"

        if open_position is None:
            if signal is not None and signal.signal != SignalType.HOLD:
                entry_price = candle.close
                stop_distance = entry_price * 0.02
                stop_price = (
                    entry_price - stop_distance
                    if signal.signal == SignalType.BUY
                    else entry_price + stop_distance
                )
                position = calculate_position(
                    capital_eur=cash,
                    entry_price=entry_price,
                    stop_price=stop_price,
                    leverage=float(candidate["leverage"]),
                )
                risk_scale = float(candidate["risk_per_trade"]) / settings.RISK_PER_TRADE
                quantity = position["quantity"] * risk_scale
                execution_entry = (
                    entry_price * (1.0 + float(candidate["slippage_rate"]))
                    if signal.signal == SignalType.BUY
                    else entry_price * (1.0 - float(candidate["slippage_rate"]))
                )
                entry_notional = execution_entry * quantity
                entry_fee = entry_notional * float(candidate["fee_rate"])
                cash -= entry_fee
                cumulative_fees += entry_fee
                gross_traded_notional += entry_notional
                maximum_trade_exposure = max(maximum_trade_exposure, entry_notional)
                open_position = {
                    "side": signal.signal.value,
                    "entry_price": execution_entry,
                    "stop_price": stop_price,
                    "quantity": quantity,
                    "entry_timestamp_utc": candle.timestamp.astimezone(timezone.utc).isoformat(),
                    "entry_fee_eur": entry_fee,
                }
                action = "OPEN_" + signal.signal.value
        else:
            side = open_position["side"]
            exit_price: float | None = None
            exit_reason: str | None = None
            if side == "BUY":
                if candle.low <= open_position["stop_price"]:
                    exit_price = open_position["stop_price"]
                    exit_reason = "STOP_LOSS"
                elif signal is not None and signal.signal == SignalType.SELL:
                    exit_price = candle.close
                    exit_reason = "SIGNAL"
            else:
                if candle.high >= open_position["stop_price"]:
                    exit_price = open_position["stop_price"]
                    exit_reason = "STOP_LOSS"
                elif signal is not None and signal.signal == SignalType.BUY:
                    exit_price = candle.close
                    exit_reason = "SIGNAL"

            if exit_price is not None:
                execution_exit = (
                    exit_price * (1.0 - float(candidate["slippage_rate"]))
                    if side == "BUY"
                    else exit_price * (1.0 + float(candidate["slippage_rate"]))
                )
                quantity = float(open_position["quantity"])
                entry_execution = float(open_position["entry_price"])
                gross_pnl = (
                    (execution_exit - entry_execution) * quantity
                    if side == "BUY"
                    else (entry_execution - execution_exit) * quantity
                )
                exit_notional = execution_exit * quantity
                exit_fee = exit_notional * float(candidate["fee_rate"])
                net_pnl = gross_pnl - float(open_position["entry_fee_eur"]) - exit_fee
                cash += gross_pnl - exit_fee
                realized_pnl += net_pnl
                cumulative_fees += exit_fee
                gross_traded_notional += exit_notional
                maximum_trade_exposure = max(maximum_trade_exposure, entry_execution * quantity)
                trades.append({
                    "side": side,
                    "entry_timestamp_utc": open_position["entry_timestamp_utc"],
                    "exit_timestamp_utc": candle.timestamp.astimezone(timezone.utc).isoformat(),
                    "entry_price": entry_execution,
                    "exit_price": execution_exit,
                    "quantity": quantity,
                    "entry_notional_eur": entry_execution * quantity,
                    "exit_notional_eur": exit_notional,
                    "pnl_eur": net_pnl,
                    "gross_pnl_eur": gross_pnl,
                    "fees_eur": float(open_position["entry_fee_eur"]) + exit_fee,
                    "exit_reason": exit_reason,
                })
                action = "CLOSE_" + side + "_" + str(exit_reason)
                open_position = None

        if open_position is None:
            unrealized_pnl = 0.0
            exposure = 0.0
            position_side = None
            position_quantity = 0.0
            position_entry_price = None
            position_entry_timestamp = None
            equity = cash
        else:
            quantity = float(open_position["quantity"])
            entry_execution = float(open_position["entry_price"])
            side = open_position["side"]
            unrealized_pnl = (
                (candle.close - entry_execution) * quantity
                if side == "BUY"
                else (entry_execution - candle.close) * quantity
            )
            exposure = candle.close * quantity
            position_side = side
            position_quantity = quantity
            position_entry_price = entry_execution
            position_entry_timestamp = open_position["entry_timestamp_utc"]
            equity = cash + unrealized_pnl

        realized_equity = float(candidate["initial_capital_eur"]) + realized_pnl
        realized_peak = max(realized_peak, realized_equity)
        mtm_peak = max(mtm_peak, equity)
        realized_dd = (1.0 - realized_equity / realized_peak) * 100.0 if realized_peak > 0 else 0.0
        mtm_dd = (1.0 - equity / mtm_peak) * 100.0 if mtm_peak > 0 else 0.0
        maximum_realized_drawdown = max(maximum_realized_drawdown, realized_dd)
        maximum_mtm_drawdown = max(maximum_mtm_drawdown, mtm_dd)

        signal_record = None if signal is None else {
            "signal": signal.signal.value,
            "confidence": signal.confidence,
            "reason": signal.reason,
        }
        ledger.append({
            "market_timestamp_utc": candle.timestamp.astimezone(timezone.utc).isoformat(),
            "close_price": candle.close,
            "signal": signal_record,
            "action": action,
            "cash_eur": cash,
            "realized_pnl_eur": realized_pnl,
            "unrealized_pnl_eur": unrealized_pnl,
            "equity_eur": equity,
            "position_side": position_side,
            "position_quantity": position_quantity,
            "position_entry_price": position_entry_price,
            "position_entry_timestamp_utc": position_entry_timestamp,
            "position_exposure_eur": exposure,
            "cumulative_fees_eur": cumulative_fees,
            "gross_traded_notional_eur": gross_traded_notional,
            "realized_drawdown_percent": realized_dd,
            "mtm_drawdown_percent": mtm_dd,
        })

    records = [_candle_record(candle) for candle in candles]
    input_fingerprint = _fingerprint(
        {
            "candidate_fingerprint": candidate_fingerprint,
            "candles": records,
            "feed_receipt_fingerprint": feed_receipt_fingerprint,
            "feed_candle_fingerprint": feed_candle_fingerprint,
            "feed_fetch_fingerprint": feed_fetch_fingerprint,
        }
    )
    last_timestamp = records[-1]["timestamp"]
    final_equity = ledger[-1]["equity_eur"]
    latest = ledger[-1]
    portfolio = {
        "initial_capital_eur": float(candidate["initial_capital_eur"]),
        "cash_eur": cash,
        "final_equity_eur": final_equity,
        "realized_pnl_eur": realized_pnl,
        "unrealized_pnl_eur": latest["unrealized_pnl_eur"],
        "total_pnl_eur": final_equity - float(candidate["initial_capital_eur"]),
        "trade_count": len(trades),
        "gross_traded_notional_eur": gross_traded_notional,
        "maximum_trade_exposure_eur": maximum_trade_exposure,
        "maximum_realized_drawdown_percent": maximum_realized_drawdown,
        "maximum_mtm_drawdown_percent": maximum_mtm_drawdown,
        "current_position_exposure_eur": latest["position_exposure_eur"],
        "current_position_unrealized_pnl_eur": latest["unrealized_pnl_eur"],
        "current_position_side": latest["position_side"],
        "current_position_quantity": latest["position_quantity"],
        "current_position_entry_price": latest["position_entry_price"],
        "current_position_entry_timestamp_utc": latest["position_entry_timestamp_utc"],
        "fees_paid_eur": cumulative_fees,
        "trades": trades,
        "ledger": ledger,
    }

    return {
        "schema_version": 2,
        "mode": "PAPER_FORWARD_SHADOW",
        "status": status,
        "safety": {
            "PAPER_ONLY": True,
            "LIVE_TRADING_ENABLED": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "run_id": run_id,
        "candidate_id": candidate["candidate_id"],
        "freeze_ref": candidate["freeze_ref"],
        "candidate_fingerprint": candidate_fingerprint,
        "input_fingerprint": input_fingerprint,
        "signal_fingerprint": signal_fingerprint,
        "feed_receipt_fingerprint": feed_receipt_fingerprint,
        "feed_candle_fingerprint": feed_candle_fingerprint,
        "feed_fetch_fingerprint": feed_fetch_fingerprint,
        "started_at_utc": started_at,
        "updated_at_utc": last_timestamp,
        "stopped_at_utc": stopped_at,
        "symbol": candidate["symbol"],
        "interval": candidate["interval"],
        "last_market_timestamp_utc": last_timestamp,
        "candle_count": len(candles),
        "candles": records,
        "portfolio": portfolio,
    }
def _read_session(
    path: Path,
) -> tuple[dict[str, Any], dict[str, Any], StrategyParameters, tuple[Candle, ...]]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PaperForwardShadowError(f"Cannot read session state: {exc}") from exc
    if not isinstance(state, dict):
        raise PaperForwardShadowError("Session state must be a JSON object.")
    safety = {
        "PAPER_ONLY": True,
        "LIVE_TRADING_ENABLED": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    if state.get("safety") != safety:
        raise PaperForwardShadowError("Persisted session safety invariants were changed.")
    candidate, parameters = _validate_candidate(state.get("candidate"))
    candidate_fingerprint = _fingerprint(candidate)
    if state.get("candidate_fingerprint") != candidate_fingerprint:
        raise PaperForwardShadowError("Persisted frozen candidate fingerprint does not match.")
    try:
        candles = _validate_candles(
            tuple(_parse_candle(item) for item in state["candles"]), candidate["interval"]
        )
        started_at = _timestamp(datetime.fromisoformat(state["started_at_utc"]), "started_at_utc")
        expected_run_id = _fingerprint(
            {
                "candidate_fingerprint": candidate_fingerprint,
                "started_at_utc": started_at.isoformat(),
            }
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PaperForwardShadowError(f"Persisted session state is invalid: {exc}") from exc
    expected_input_fingerprint = _fingerprint(
        {
            "candidate_fingerprint": candidate_fingerprint,
            "candles": [_candle_record(candle) for candle in candles],
            "feed_receipt_fingerprint": state.get("feed_receipt_fingerprint"),
            "feed_candle_fingerprint": state.get("feed_candle_fingerprint"),
            "feed_fetch_fingerprint": state.get("feed_fetch_fingerprint"),
        }
    )
    expected_snapshot = _snapshot(
        candidate,
        parameters,
        candles,
        expected_run_id,
        candidate_fingerprint,
        started_at.isoformat(),
        state.get("status"),
        state.get("stopped_at_utc"),
        state.get("feed_receipt_fingerprint"),
        state.get("feed_candle_fingerprint"),
        state.get("feed_fetch_fingerprint"),
    )
    latest_timestamp = _candle_record(candles[-1])["timestamp"]
    expected_stopped_at = None if state.get("status") == "RUNNING" else latest_timestamp
    if (
        state.get("schema_version") != 2 or state.get("status") not in {"RUNNING", "STOPPED"}
        or state.get("stopped_at_utc") != expected_stopped_at
        or state.get("run_id") != expected_run_id
        or state.get("input_fingerprint") != expected_input_fingerprint
        or state.get("signal_fingerprint") != expected_snapshot["signal_fingerprint"]
        or started_at != _timestamp(candles[0].timestamp, "first candle timestamp")
        or state.get("last_market_timestamp_utc") != latest_timestamp
        or state.get("updated_at_utc") != latest_timestamp
        or state.get("portfolio") != expected_snapshot["portfolio"]
    ):
        raise PaperForwardShadowError(
            "Persisted session fingerprints, timestamps, or portfolio do not match."
        )
    return state, candidate, parameters, candles


def start_session(
    candidate: dict[str, Any], candles: Sequence[Candle], state_path: str | Path
) -> dict[str, Any]:
    _assert_safety()
    candidate, parameters = _validate_candidate(candidate)
    ordered = _validate_candles(candles, candidate["interval"])
    path = Path(state_path)
    if path.exists():
        raise PaperForwardShadowError(f"Session state already exists: {path}.")
    candidate_fingerprint = _fingerprint(candidate)
    started_at = _candle_record(ordered[0])["timestamp"]
    run_id = _fingerprint(
        {
            "candidate_fingerprint": candidate_fingerprint,
            "started_at_utc": started_at,
        }
    )
    state = _snapshot(
        candidate, parameters, ordered, run_id, candidate_fingerprint, started_at, "RUNNING"
    )
    state["candidate"] = candidate
    _atomic_write(path, state)
    return state


def update_session(
    state_path: str | Path,
    candles: Sequence[Candle],
    *,
    feed_receipt_fingerprint: str | None = None,
    feed_candle_fingerprint: str | None = None,
    feed_fetch_fingerprint: str | None = None,
) -> dict[str, Any]:
    _assert_safety()
    path = Path(state_path)
    state, candidate, parameters, existing = _read_session(path)
    if state.get("status") != "RUNNING":
        raise PaperForwardShadowError("Only a RUNNING session can be updated.")
    incoming = _validate_candles(candles, candidate["interval"])
    existing_records = [_candle_record(candle) for candle in existing]
    incoming_records = [_candle_record(candle) for candle in incoming]
    existing_by_timestamp = {record["timestamp"]: record for record in existing_records}

    new_candles: list[Candle] = []
    existing_first = _timestamp(existing[0].timestamp, "timestamp")
    existing_last = _timestamp(existing[-1].timestamp, "timestamp")
    interval = _INTERVALS[candidate["interval"]]

    for candle, record in zip(incoming, incoming_records):
        timestamp = _timestamp(candle.timestamp, "timestamp")
        if record["timestamp"] in existing_by_timestamp:
            if existing_by_timestamp[record["timestamp"]] != record:
                raise PaperForwardShadowError(
                    "Previously observed candle changed; historical input cannot be rewritten."
                )
            continue

        # The public market endpoint returns a window larger than our persisted
        # state. Candles strictly before the retained window are historical
        # context and cannot be appended to the state again.
        if timestamp <= existing_last:
            if timestamp < existing_first:
                continue
            raise PaperForwardShadowError(
                "Incoming candle falls inside the retained state but is missing from persisted history."
            )

        new_candles.append(candle)

    if new_candles:
        new_candles.sort(key=lambda item: item.timestamp)
        if _timestamp(new_candles[0].timestamp, "timestamp") - existing_last != interval:
            raise PaperForwardShadowError(
                "New data must append contiguously after the last candle."
            )
        _validate_candles((*existing[-1:], *new_candles), candidate["interval"])
        combined = (*existing, *new_candles)
    else:
        combined = existing

    updated = _snapshot(
        candidate,
        parameters,
        combined,
        state["run_id"],
        state["candidate_fingerprint"],
        state["started_at_utc"],
        "RUNNING",
        feed_receipt_fingerprint=(
            feed_receipt_fingerprint
            if feed_receipt_fingerprint is not None
            else state.get("feed_receipt_fingerprint")
        ),
        feed_candle_fingerprint=(
            feed_candle_fingerprint
            if feed_candle_fingerprint is not None
            else state.get("feed_candle_fingerprint")
        ),
        feed_fetch_fingerprint=(
            feed_fetch_fingerprint
            if feed_fetch_fingerprint is not None
            else state.get("feed_fetch_fingerprint")
        ),
    )
    updated["candidate"] = candidate
    _atomic_write(path, updated)
    return updated


def stop_session(state_path: str | Path) -> dict[str, Any]:
    _assert_safety()
    path = Path(state_path)
    state, _, _, _ = _read_session(path)
    if state.get("status") != "RUNNING":
        raise PaperForwardShadowError("Only a RUNNING session can be stopped.")
    state["status"] = "STOPPED"
    state["stopped_at_utc"] = state["last_market_timestamp_utc"]
    _atomic_write(path, state)
    return state


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--candidate", required=True)
    start.add_argument("--candles", required=True)
    start.add_argument("--state", required=True)
    update = commands.add_parser("update")
    update.add_argument("--candles", required=True)
    update.add_argument("--state", required=True)
    stop = commands.add_parser("stop")
    stop.add_argument("--state", required=True)
    args = parser.parse_args()
    with process_lock(args.state):
        if args.command == "start":
            candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
            result = start_session(candidate, load_candles(args.candles), args.state)
            _mark_initialized(args.state, result)
        elif args.command == "update":
            result = update_session(args.state, load_candles(args.candles))
            _mark_initialized(args.state, result)
        else:
            result = stop_session(args.state)
            _mark_initialized(args.state, result)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    _main()
