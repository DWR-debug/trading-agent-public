"""Fail-closed Yahoo OHLCV coverage preflight.

All market-data snapshot geometry is delegated to the canonical data layer.
This runner retains trial-specific preregistration and symbol-disjointness
governance, but does not implement a second calendar/snapshot algorithm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from config import settings
from data.canonical_snapshot import SnapshotSpec, build_frozen_snapshot
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


def _parse_optional_date(spec: dict, key: str) -> date | None:
    value = spec.get(key)
    if value is None:
        value = spec.get("study_window", {}).get(key)
    if value is None:
        value = spec.get("data_contract", {}).get(key)
    if value is None and not key.startswith("study_"):
        value = spec.get("data_contract", {}).get(f"study_{key}")
    return date.fromisoformat(value) if value else None


def _validate_disjointness(spec: dict, universe_name: str, symbols: tuple[str, ...], trial_id: str) -> None:
    target_set = set(symbols)
    allowed_overlap = set(spec.get("disjointness", {}).get("allowed_overlap_universes", []))
    if allowed_overlap:
        if spec.get("trial_type") != "repair_successor":
            raise RuntimeError(
                "Symbol overlap is only permitted for an explicit repair successor."
            )
        if not spec.get("parent_trial_id"):
            raise RuntimeError(
                "Repair successor with symbol overlap requires parent_trial_id."
            )

    repair_successors = set()
    preregistration_dir = ROOT / "research" / "preregistrations"
    for candidate in preregistration_dir.glob("trial_*.json"):
        try:
            successor = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            successor.get("trial_type") == "repair_successor"
            and successor.get("parent_trial_id") == trial_id
            and successor.get("disjointness", {}).get("allowed_overlap_universes", []) == [universe_name]
        ):
            repair_successors.add(successor.get("universe"))

    for other in list_universes():
        if other.name == universe_name or other.name in allowed_overlap or other.name in repair_successors:
            continue
        overlap = sorted(target_set.intersection(other.symbols))
        if overlap:
            raise RuntimeError(
                f"Universe is not symbol-disjoint from {other.name}: {overlap}"
            )


def run_preflight(
    preregistration: str | Path,
    *,
    output_root: str | Path = "research/runs/coverage_preflight",
) -> dict:
    prereg_path = Path(preregistration)
    if not prereg_path.is_absolute():
        prereg_path = ROOT / prereg_path

    spec = json.loads(prereg_path.read_text(encoding="utf-8"))
    trial_id = str(spec["trial_id"])
    universe_name = str(spec["universe"])
    symbols = tuple(spec["symbols"])
    interval = str(spec["interval"])
    requested = int(spec["requested_candles"])
    target = int(spec["target_candles"])

    if settings.PAPER_ONLY is not True:
        raise RuntimeError("Coverage preflight requires PAPER_ONLY=True.")
    if settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Coverage preflight requires LIVE_TRADING_ENABLED=False.")
    if settings.ORDERS_ENABLED is not False:
        raise RuntimeError("Coverage preflight requires ORDERS_ENABLED=False.")
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

    _validate_disjointness(spec, universe_name, symbols, trial_id)

    study_start = _parse_optional_date(spec, "start")
    study_end = _parse_optional_date(spec, "end")
    output_dir = Path(output_root) / trial_id

    canonical = build_frozen_snapshot(
        SnapshotSpec(
            universe=universe_name,
            symbols=symbols,
            interval=interval,
            requested_candles=requested,
            target_common_candles=target,
            minimum_in_window_candles=requested,
            output_dir=output_dir,
            study_start=study_start,
            study_end=study_end,
        ),
        loader=load_yahoo_history,
    )

    status = "coverage_passed" if canonical["status"] == "COVERAGE_PASSED" else "DATA_INVALID"
    per_symbol = canonical["coverage"]["per_symbol"]
    counts = {
        symbol: meta["in_window_count"]
        for symbol, meta in per_symbol.items()
    }
    insufficient = {
        symbol: count
        for symbol, count in counts.items()
        if count < requested
    }
    missing = [
        symbol
        for symbol in symbols
        if per_symbol.get(symbol, {}).get("status") != "COVERAGE_VALID"
    ]

    reasons = []
    failure_reason = canonical["coverage"].get("failure_reason")
    if failure_reason:
        reasons.append(failure_reason)

    payload = {
        "schema_version": "1.1",
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
        "datasets": [
            {
                "symbol": symbol,
                "count": per_symbol[symbol].get("in_window_count", 0),
                "start": per_symbol[symbol].get("start"),
                "end": per_symbol[symbol].get("end"),
            }
            for symbol in symbols
            if symbol in per_symbol
        ],
        "per_symbol_counts": counts,
        "insufficient_symbols": insufficient,
        "missing_symbols": missing,
        "common_calendar_count": canonical["coverage"]["common_calendar_count"],
        "quality": {
            symbol: per_symbol[symbol].get("quality", {})
            for symbol in per_symbol
        },
        "errors": canonical["coverage"]["errors"],
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
        "data_snapshot": canonical.get("data_snapshot"),
        "snapshot_fingerprint": canonical.get("snapshot_fingerprint"),
        "selected_common_calendar_start": canonical.get("selected_common_calendar_start"),
        "selected_common_calendar_end": canonical.get("selected_common_calendar_end"),
        "canonical_data_layer": "data/canonical_snapshot.py",
        "safety": canonical["safety"],
    }

    payload["coverage_fingerprint"] = _fingerprint(payload)

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = output_dir / f"coverage_preflight_{timestamp}.json"
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    payload["output"] = str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output)

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", required=True)
    parser.add_argument("--output-root", default="research/runs/coverage_preflight")
    args = parser.parse_args()
    result = run_preflight(args.preregistration, output_root=args.output_root)
    print(f"COVERAGE_STATUS: {result['status']}")


if __name__ == "__main__":
    main()
