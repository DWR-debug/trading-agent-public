"""Temporal Tug-of-War Alpha Feasibility (TTAF).

This module decomposes daily OHLCV into overnight and intraday components and
constructs one frozen 21-session temporal-wedge score. It is diagnostic/
feasibility-only: no P&L, future labels, holdout selection, optimization,
promotion, or live execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

WINDOW = 21
MECHANISM_ID = "TTAF_NIGHT_DAY_TUG_OF_WAR_21"


def _finite(value: Any, name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if out != out or out in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be finite")
    return out


def _fp(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def phase_returns(assets: Mapping[str, Sequence[Any]], index: int, *, symbol: str) -> tuple[float, float]:
    if symbol not in assets:
        raise ValueError(f"missing symbol: {symbol}")
    bars = assets[symbol]
    if index < 1 or index >= len(bars):
        raise ValueError("index out of range")
    previous_close = _finite(getattr(bars[index - 1], "close"), f"{symbol}.previous_close")
    open_value = _finite(getattr(bars[index], "open"), f"{symbol}.open")
    close_value = _finite(getattr(bars[index], "close"), f"{symbol}.close")
    if previous_close <= 0 or open_value <= 0 or close_value <= 0:
        raise ValueError(f"{symbol}: prices must be positive")
    overnight = open_value / previous_close - 1.0
    intraday = close_value / open_value - 1.0
    return overnight, intraday


def temporal_wedge(assets: Mapping[str, Sequence[Any]], index: int, *, symbol: str, window: int = WINDOW) -> dict[str, Any]:
    if window != WINDOW:
        raise ValueError("TTAF window is frozen at 21 sessions")
    if index < window:
        raise ValueError("insufficient history for TTAF")
    overnight = []
    intraday = []
    for i in range(index - window + 1, index + 1):
        night, day = phase_returns(assets, i, symbol=symbol)
        overnight.append(night)
        intraday.append(day)
    night_sum = sum(overnight)
    day_sum = sum(intraday)
    payload = {
        "schema_version": 1,
        "mechanism_id": MECHANISM_ID,
        "symbol": symbol,
        "index": index,
        "window": window,
        "overnight_return_sum": night_sum,
        "intraday_return_sum": day_sum,
        "temporal_wedge": night_sum - day_sum,
        "signal": -(night_sum - day_sum),
        "uses_future_bars": False,
        "uses_future_labels": False,
        "uses_holdout": False,
        "uses_optimizer": False,
        "performance_evaluation": False,
        "selection_used": False,
    }
    payload["provenance_fingerprint"] = _fp(payload)
    return payload


def cross_sectional_observation(
    assets: Mapping[str, Sequence[Any]], index: int, *, symbols: Sequence[str], window: int = WINDOW
) -> tuple[dict[str, Any], ...]:
    if not symbols or len(symbols) != len(set(symbols)):
        raise ValueError("symbols must be non-empty and unique")
    return tuple(
        temporal_wedge(assets, index, symbol=symbol, window=window)
        for symbol in symbols
    )


def future_mutation(assets: Mapping[str, Sequence[Any]], index: int, factor: float = 11.0) -> dict[str, tuple[Any, ...]]:
    if factor <= 0:
        raise ValueError("factor must be positive")
    return {
        symbol: tuple(
            bar if i <= index else type(bar)(
                timestamp=bar.timestamp,
                open=bar.open * factor,
                high=bar.high * factor,
                low=bar.low / factor,
                close=bar.close / factor,
                volume=bar.volume,
            )
            for i, bar in enumerate(bars)
        )
        for symbol, bars in assets.items()
    }


def run_frozen_snapshot(manifest: Path, output: Path, sample_indices: Sequence[int] = (400, 631, 862, 1093, 1324, 1555, 1786, 2017, 2248, 2479, 2710, 2941, 3172, 3403)) -> dict[str, Any]:
    from data.canonical_snapshot import load_frozen_snapshot

    parsed = json.loads(manifest.read_text(encoding="utf-8"))
    if parsed.get("status") != "COVERAGE_PASSED":
        raise RuntimeError("source snapshot is not coverage-passed")
    assets = load_frozen_snapshot(manifest)
    symbols = tuple(parsed["symbols"])
    observations = []
    for index in sample_indices:
        if index >= len(next(iter(assets.values()))):
            continue
        current = cross_sectional_observation(assets, index, symbols=symbols)
        mutated = future_mutation(assets, index)
        mutated_obs = cross_sectional_observation(mutated, index, symbols=symbols)
        if current != mutated_obs:
            raise AssertionError(f"future mutation changed TTAF at index {index}")
        observations.append({
            "index": index,
            "observations": list(current),
            "future_mutation_invariant": True,
        })
    result = {
        "schema_version": 1,
        "component": "TTAF_OBSERVATIONAL_FEASIBILITY",
        "mechanism_id": MECHANISM_ID,
        "source_trial_id": parsed.get("trial_id"),
        "source_snapshot_fingerprint": parsed.get("snapshot_fingerprint"),
        "symbols": list(symbols),
        "window": WINDOW,
        "sample_count": len(observations),
        "observations": observations,
        "governance": {
            "performance_evaluation": False,
            "holdout_used": False,
            "selection_used": False,
            "parameter_search": False,
            "threshold_search": False,
            "asset_search": False,
            "horizon_search": False,
            "variant_search": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "status": "OBSERVATIONAL_FEASIBILITY_PASSED",
    }
    result["fingerprint"] = _fp(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(
        0 if run_frozen_snapshot(args.manifest, args.output)["status"] == "OBSERVATIONAL_FEASIBILITY_PASSED" else 1
    )
