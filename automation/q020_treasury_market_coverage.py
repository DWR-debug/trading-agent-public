"""Q020 canonical market-coverage gate for the fixed Q018 universe.

Coverage-only. No returns, P&L, holdout use, selection, tuning, or promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from config import settings
from data.canonical_snapshot import SnapshotSpec, build_frozen_snapshot
from research.asset_universes import get_universe, list_universes

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = "q018_official_event_source_validation"
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
REQUESTED_CANDLES = 3520
TARGET_COMMON_CANDLES = 3500


def _fingerprint(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run(*, output_path: str | Path) -> dict:
    if (
        settings.PAPER_ONLY is not True
        or settings.LIVE_TRADING_ENABLED is not False
        or settings.ORDERS_ENABLED is not False
        or settings.AUTOMATIC_PROMOTION is not False
    ):
        raise RuntimeError("Q020 requires the paper-only safety configuration.")

    universe = get_universe(UNIVERSE)
    fixed_symbols = set(universe.symbols)
    for existing in list_universes():
        if existing.name != UNIVERSE and fixed_symbols.intersection(existing.symbols):
            raise RuntimeError(
                f"Q020 fixed universe overlaps {existing.name}: "
                f"{sorted(fixed_symbols.intersection(existing.symbols))}"
            )

    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    snapshot_dir = output.parent / "q020_market_coverage_snapshot"
    canonical = build_frozen_snapshot(
        SnapshotSpec(
            universe=UNIVERSE,
            symbols=tuple(universe.symbols),
            interval="1d",
            requested_candles=REQUESTED_CANDLES,
            target_common_candles=TARGET_COMMON_CANDLES,
            minimum_in_window_candles=TARGET_COMMON_CANDLES,
            output_dir=snapshot_dir,
            dataset_subdir=".",
            study_start=STUDY_START,
            study_end=STUDY_END,
        )
    )

    common_count = canonical.get("coverage", {}).get("common_calendar_count", 0)
    complete_symbols = all(
        canonical.get("coverage", {}).get("per_symbol", {}).get(symbol, {}).get("status")
        == "COVERAGE_VALID"
        for symbol in universe.symbols
    )
    status = (
        "COVERAGE_VALIDATED"
        if canonical.get("status") == "COVERAGE_PASSED"
        and common_count >= TARGET_COMMON_CANDLES
        and complete_symbols
        else "DATA_INSUFFICIENT"
    )

    result = {
        "schema_version": "1.0",
        "task_id": "Q-020-TREASURY-MARKET-COVERAGE",
        "status": status,
        "study_window": {
            "start": STUDY_START.isoformat(),
            "end": STUDY_END.isoformat(),
        },
        "universe": {"name": UNIVERSE, "symbols": list(universe.symbols)},
        "requested_candles": REQUESTED_CANDLES,
        "required_common_calendar": TARGET_COMMON_CANDLES,
        "canonical_status": canonical.get("status"),
        "coverage": canonical.get("coverage", {}),
        "snapshot_fingerprint": canonical.get("snapshot_fingerprint"),
        "governance": {
            "coverage_only": True,
            "performance_evaluation": False,
            "holdout_used": False,
            "selection_used": False,
            "parameter_search": False,
            "asset_search": False,
            "feature_search": False,
            "horizon_search": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "next_rule": (
            "A coverage pass does not authorize performance; a coverage failure must "
            "not be rescued by changing assets or sample geometry."
        ),
    }
    result["fingerprint"] = _fingerprint(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": result["task_id"],
        "status": result["status"],
        "common_calendar_count": common_count,
        "fingerprint": result["fingerprint"],
    }, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="research/runs/source_feasibility/q020_treasury_market_coverage.json",
    )
    args = parser.parse_args()
    try:
        result = run(output_path=args.output)
    except (RuntimeError, ValueError) as exc:
        print(json.dumps({"task_id": "Q-020-TREASURY-MARKET-COVERAGE", "status": "DATA_INSUFFICIENT", "error": str(exc)}))
        return 2
    return 0 if result["status"] in {"COVERAGE_VALIDATED", "DATA_INSUFFICIENT"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
