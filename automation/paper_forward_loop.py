"""Autonomous paper-forward loop: market feed -> shadow state -> repeat."""
from __future__ import annotations

import argparse
import time
from typing import Any

from automation.paper_forward_market_feed import (
    load_candidate,
    start_from_binance,
    update_from_binance,
)
from automation.paper_forward_shadow import (
    PaperForwardShadowError,
    _assert_safety,
    _initialization_marker_path,
    _mark_initialized,
    _read_session,
    process_lock,
)


_INTERVAL_SECONDS = {
    "1m": 60,
    "5m": 5 * 60,
    "15m": 15 * 60,
    "30m": 30 * 60,
    "1h": 60 * 60,
    "4h": 4 * 60 * 60,
    "1d": 24 * 60 * 60,
}


def default_poll_seconds(interval: str) -> int:
    try:
        candle_seconds = _INTERVAL_SECONDS[interval]
    except KeyError as exc:
        raise PaperForwardShadowError(f"Unsupported interval: {interval}.") from exc
    return max(30, min(900, candle_seconds // 4))


def run_once(
    candidate_path: str,
    state_path: str,
    *,
    warmup_candles: int = 500,
    fetch_limit: int = 100,
    receipt_path: str | None = None,
) -> dict:
    _assert_safety()
    with process_lock(state_path, receipt_path):
        return _run_once_locked(
            candidate_path,
            state_path,
            warmup_candles=warmup_candles,
            fetch_limit=fetch_limit,
            receipt_path=receipt_path,
        )


def _run_once_locked(
    candidate_path: str,
    state_path: str,
    *,
    warmup_candles: int,
    fetch_limit: int,
    receipt_path: str | None,
) -> dict:
    from pathlib import Path

    state = Path(state_path)
    if not state.exists():
        if _initialization_marker_path(state).exists():
            raise PaperForwardShadowError(
                "Initialized paper-forward state is missing; restore it or choose a new state path."
            )
        candidate = load_candidate(candidate_path)
        started = start_from_binance(candidate, state, warmup_candles=warmup_candles)
        _mark_initialized(state, started)
        return started

    persisted, _, _, _ = _read_session(state)
    _mark_initialized(state, persisted)
    updated = update_from_binance(
        state, fetch_limit=fetch_limit, receipt_path=receipt_path
    )
    _mark_initialized(state, updated)
    return updated


def _candidate_for_polling(candidate_path: str, state_path: str) -> dict[str, Any]:
    from pathlib import Path

    state_path = Path(state_path)
    if state_path.exists():
        persisted, candidate, _, _ = _read_session(state_path)
        _mark_initialized(state_path, persisted)
        return candidate
    if _initialization_marker_path(state_path).exists():
        raise PaperForwardShadowError(
            "Initialized paper-forward state is missing; restore it or choose a new state path."
        )
    return load_candidate(candidate_path)


def run_loop(
    candidate_path: str,
    state_path: str,
    *,
    poll_seconds: int | None = None,
    warmup_candles: int = 500,
    fetch_limit: int = 100,
    receipt_path: str | None = None,
    max_iterations: int | None = None,
) -> None:
    _assert_safety()
    with process_lock(state_path, receipt_path):
        candidate = _candidate_for_polling(candidate_path, state_path)
        delay = (
            poll_seconds
            if poll_seconds is not None
            else default_poll_seconds(candidate["interval"])
        )
        if delay < 5:
            raise PaperForwardShadowError("poll_seconds must be at least 5.")
        if max_iterations is not None and max_iterations < 1:
            raise PaperForwardShadowError("max_iterations must be positive when supplied.")

        iterations = 0
        while True:
            _run_once_locked(
                candidate_path,
                state_path,
                warmup_candles=warmup_candles,
                fetch_limit=fetch_limit,
                receipt_path=receipt_path,
            )
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                return
            time.sleep(delay)


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--receipt")
    parser.add_argument("--poll-seconds", type=int)
    parser.add_argument("--warmup-candles", type=int, default=500)
    parser.add_argument("--fetch-limit", type=int, default=100)
    parser.add_argument("--max-iterations", type=int)
    args = parser.parse_args()
    run_loop(
        args.candidate,
        args.state,
        poll_seconds=args.poll_seconds,
        warmup_candles=args.warmup_candles,
        fetch_limit=args.fetch_limit,
        receipt_path=args.receipt,
        max_iterations=args.max_iterations,
    )


if __name__ == "__main__":
    _main()
