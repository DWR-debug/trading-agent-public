"""Closed-candle public Binance feed for the paper-forward shadow harness."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation.paper_forward_shadow import (
    PaperForwardShadowError,
    _assert_safety,
    _candle_record,
    _fingerprint,
    _validate_candidate,
    start_session,
    update_session,
)
from backtesting.models import Candle
from data.binance_loader import BASE_URL, load_binance_candles, load_binance_history
from data.time_utils import is_candle_closed


@dataclass(frozen=True)
class FeedReceipt:
    schema_version: int
    source: str
    endpoint: str
    candidate_id: str
    candidate_fingerprint: str
    symbol: str
    interval: str
    requested_candles: int
    closed_candles_returned: int
    latest_market_timestamp_utc: str
    fetched_at_utc: str
    candle_fingerprint: str
    fetch_fingerprint: str
    receipt_fingerprint: str
    state_input_fingerprint: str


def _receipt_fingerprint(
    *,
    source: str,
    endpoint: str,
    candidate_id: str,
    candidate_fingerprint: str,
    symbol: str,
    interval: str,
    requested_candles: int,
    closed_candles_returned: int,
    latest_market_timestamp_utc: str,
    candle_fingerprint: str,
) -> str:
    return _fingerprint(
        {
            "source": source,
            "endpoint": endpoint,
            "candidate_id": candidate_id,
            "candidate_fingerprint": candidate_fingerprint,
            "symbol": symbol,
            "interval": interval,
            "requested_candles": requested_candles,
            "closed_candles_returned": closed_candles_returned,
            "latest_market_timestamp_utc": latest_market_timestamp_utc,
            "candle_fingerprint": candle_fingerprint,
        }
    )


def load_candidate(path: str | Path) -> dict[str, Any]:
    try:
        candidate = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PaperForwardShadowError(f"Cannot read frozen candidate: {exc}") from exc
    normalized, _ = _validate_candidate(candidate)
    return normalized


def fetch_closed_candles(symbol: str, interval: str, *, limit: int = 1000) -> list[Candle]:
    _assert_safety()
    if not 1 <= limit <= 1000:
        raise PaperForwardShadowError("limit must be between 1 and 1000.")
    now = datetime.now(timezone.utc)
    raw = load_binance_candles(symbol, interval, limit=limit)
    closed = [candle for candle in raw if is_candle_closed(candle.timestamp, interval, now=now)]
    if not closed:
        raise PaperForwardShadowError(
            f"Binance returned no closed candles for {symbol} {interval}."
        )
    return sorted(closed, key=lambda candle: candle.timestamp)


def start_from_binance(
    candidate: dict[str, Any],
    state_path: str | Path,
    *,
    warmup_candles: int = 500,
) -> dict[str, Any]:
    _assert_safety()
    normalized, _ = _validate_candidate(candidate)
    if warmup_candles < 2:
        raise PaperForwardShadowError("warmup_candles must be at least 2.")
    required = max(
        int(normalized["parameters"]["momentum"]["lookback"]) + 1,
        int(normalized["parameters"]["mean_reversion"]["window"]),
    )
    if warmup_candles < required:
        raise PaperForwardShadowError(
            f"warmup_candles={warmup_candles} is below minimum required lookback {required}."
        )
    candles = load_binance_history(normalized["symbol"], normalized["interval"], warmup_candles)
    return start_session(normalized, candles, state_path)


def update_from_binance(
    state_path: str | Path,
    *,
    fetch_limit: int = 100,
    receipt_path: str | Path | None = None,
) -> dict[str, Any]:
    _assert_safety()
    path = Path(state_path)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        normalized, _ = _validate_candidate(state.get("candidate"))
    except (OSError, json.JSONDecodeError, KeyError, TypeError, PaperForwardShadowError) as exc:
        raise PaperForwardShadowError(f"Cannot read running shadow state: {exc}") from exc

    closed = fetch_closed_candles(normalized["symbol"], normalized["interval"], limit=fetch_limit)
    candle_fingerprint = _fingerprint([_candle_record(c) for c in closed])
    fetch_fingerprint = _receipt_fingerprint(
        source="binance_public_market_data",
        endpoint=BASE_URL,
        candidate_id=normalized["candidate_id"],
        candidate_fingerprint=_fingerprint(normalized),
        symbol=normalized["symbol"],
        interval=normalized["interval"],
        requested_candles=fetch_limit,
        closed_candles_returned=len(closed),
        latest_market_timestamp_utc=_candle_record(closed[-1])["timestamp"],
        candle_fingerprint=candle_fingerprint,
    )
    receipt_fingerprint = _fingerprint(
        {"fetch_fingerprint": fetch_fingerprint, "candle_fingerprint": candle_fingerprint}
    )
    updated = update_session(
        path,
        closed,
        feed_receipt_fingerprint=receipt_fingerprint,
        feed_candle_fingerprint=candle_fingerprint,
        feed_fetch_fingerprint=fetch_fingerprint,
    )
    receipt = FeedReceipt(
        schema_version=1,
        source="binance_public_market_data",
        endpoint=BASE_URL,
        candidate_id=normalized["candidate_id"],
        candidate_fingerprint=_fingerprint(normalized),
        symbol=normalized["symbol"],
        interval=normalized["interval"],
        requested_candles=fetch_limit,
        closed_candles_returned=len(closed),
        latest_market_timestamp_utc=_candle_record(closed[-1])["timestamp"],
        fetched_at_utc=datetime.now(timezone.utc).isoformat(),
        candle_fingerprint=candle_fingerprint,
        fetch_fingerprint=fetch_fingerprint,
        receipt_fingerprint=receipt_fingerprint,
        state_input_fingerprint=updated["input_fingerprint"],
    )
    if receipt_path is not None:
        _atomic_write_json(Path(receipt_path), asdict(receipt))
    return updated


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
