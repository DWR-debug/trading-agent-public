"""Fail-closed coverage preflight for a preregistered research trial.

This module only acquires and validates historical data coverage. It never evaluates
strategy performance, never selects parameters, never reads a holdout for selection,
and never places orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from data.yahoo_loader import load_yahoo_history
from research.asset_universes import get_universe, list_universes


ROOT = Path(__file__).resolve().parents[1]


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(payload: dict) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def run_preflight(
    preregistration: str | Path,
    *,
    output_root: str | Path = "research/runs/coverage_preflight",
) -> dict:
    prereg_path = Path(preregistration)
    if not prereg_path.is_absolute():
        prereg_path = ROOT / prereg_path

    spec = json.loads(prereg_path.read_text(encoding="utf-8"))
    trial_id = spec["trial_id"]
    universe_name = spec["universe"]
    symbols = tuple(spec["symbols"])
    interval = spec["interval"]
    requested = int(spec["requested_candles"])
    target = int(spec["target_candles"])

    if settings.PAPER_ONLY is not True:
        raise RuntimeError("Coverage preflight requires PAPER_ONLY=True.")
    if settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Coverage preflight requires LIVE_TRADING_ENABLED=False.")
    if len(symbols) != len(set(symbols)):
        raise RuntimeError("Preregistration contains duplicate symbols.")

    universe = get_universe(universe_name)
    if tuple(universe.symbols) != symbols:
        raise RuntimeError(
            f"Universe mismatch: {universe_name} does not exactly match preregistration."
        )
    if universe.interval != interval:
        raise RuntimeError("Universe interval does not match preregistration.")
    if universe.target_count != requested:
        raise RuntimeError("Universe target_count does not match requested coverage.")

    target_set = set(symbols)
    for other in list_universes():
        if other.name != universe_name and target_set.intersection(other.symbols):
            raise RuntimeError(
                f"Universe is not symbol-disjoint from {other.name}."
            )

    counts: dict[str, int] = {}
    quality: dict[str, dict[str, int]] = {}
    errors: dict[str, str] = {}
    histories = {}
    datasets = []

    for symbol in symbols:
        report: dict[str, int] = {}
        try:
            bars = load_yahoo_history(
                symbol,
                interval,
                requested,
                allow_partial=True,
                skip_invalid_ohlc=True,
                quality_report=report,
            )
        except ValueError as exc:
            errors[symbol] = str(exc)
            quality[symbol] = report
            continue

        counts[symbol] = len(bars)
        quality[symbol] = report
        histories[symbol] = {bar.timestamp for bar in bars}
        datasets.append(
            {
                "symbol": symbol,
                "count": len(bars),
                "start": bars[0].timestamp.isoformat() if bars else None,
                "end": bars[-1].timestamp.isoformat() if bars else None,
            }
        )

    common_count = (
        len(set.intersection(*histories.values()))
        if histories and len(histories) == len(symbols)
        else 0
    )

    insufficient = {
        symbol: count
        for symbol, count in counts.items()
        if count < requested
    }
    missing = [symbol for symbol in symbols if symbol not in histories]

    status = "coverage_passed"
    reasons: list[str] = []
    if missing:
        status = "DATA_INVALID"
        reasons.append("missing_or_unloadable_symbols")
    if insufficient:
        status = "DATA_INVALID"
        reasons.append("insufficient_per_symbol_history")
    if common_count < target:
        status = "DATA_INVALID"
        reasons.append("insufficient_common_calendar")

    payload = {
        "schema_version": "1.0",
        "trial_id": trial_id,
        "research_family": spec["research_family"],
        "universe": universe_name,
        "preregistration": str(prereg_path.relative_to(ROOT)),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "interval": interval,
        "requested_candles": requested,
        "target_common_calendar": target,
        "symbols": list(symbols),
        "datasets": datasets,
        "per_symbol_counts": counts,
        "insufficient_symbols": insufficient,
        "missing_symbols": missing,
        "common_calendar_count": common_count,
        "quality": quality,
        "errors": errors,
        "performance_evaluation": False,
        "oos_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "scientific_outcome": (
            "COVERAGE_PASSED_NO_PERFORMANCE_EVIDENCE"
            if status == "coverage_passed"
            else "NO_SCIENTIFIC_OUTCOME"
        ),
        "failure_reasons": reasons,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    payload["coverage_fingerprint"] = _fingerprint(payload)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(output_root)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir = out_dir / trial_id
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"coverage_preflight_{timestamp}.json"
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    try:
        payload["output"] = str(output.relative_to(ROOT))
    except ValueError:
        payload["output"] = str(output)

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", required=True)
    parser.add_argument(
        "--output-root",
        default="research/runs/coverage_preflight",
    )
    args = parser.parse_args()
    result = run_preflight(args.preregistration, output_root=args.output_root)
    print(f"COVERAGE_STATUS: {result['status']}")


if __name__ == "__main__":
    main()
