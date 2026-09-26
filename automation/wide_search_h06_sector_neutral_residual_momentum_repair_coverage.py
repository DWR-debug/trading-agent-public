"""Research-only H06 coverage preflight using the canonical data layer.

No forward-return evaluation, no holdout use, no parameter search, no asset selection.
All Yahoo acquisition, study-window filtering, calendar alignment and frozen snapshot
creation are delegated to data.canonical_snapshot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from datetime import date
from pathlib import Path

from config import settings
from data.canonical_snapshot import SnapshotSpec, build_frozen_snapshot, load_frozen_snapshot
from research.asset_universes import get_universe

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = "validation_2026_09_25_sector_neutral_residual_momentum_repair"
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
TARGET_COMMON_CANDLES = 3500
RESEARCH_CANDLES = 2798
REQUESTED_CANDLES = 4000
LOOKBACK = 252
SKIP = 21

SECTOR_MAP = {
    "technology": ("TXN", "ADI", "AMAT"),
    "healthcare": ("MDT", "SYK", "BDX"),
    "industrials": ("ETN", "ITW", "GD"),
    "consumer_staples": ("CL", "KMB", "GIS"),
    "utilities": ("AEP", "XEL", "DTE"),
}


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run(
    *,
    output_path: str | Path =
    "research/runs/wide_search/h06_sector_neutral_residual_momentum_repair_coverage.json",
) -> dict:
    if (
        settings.PAPER_ONLY is not True
        or settings.LIVE_TRADING_ENABLED is not False
        or settings.ORDERS_ENABLED is not False
    ):
        raise RuntimeError("H06 coverage requires the paper-only safety configuration.")

    universe = get_universe(UNIVERSE)
    expected_symbols = tuple(
        symbol for members in SECTOR_MAP.values() for symbol in members
    )
    if tuple(universe.symbols) != expected_symbols:
        raise RuntimeError("Fixed H06 universe does not match its preregistered sector map.")
    if any(len(members) != 3 for members in SECTOR_MAP.values()):
        raise RuntimeError("Each preregistered H06 sector must contain exactly three assets.")

    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    snapshot_root = output.parent / "h06_repair_datasets"

    canonical = build_frozen_snapshot(
        SnapshotSpec(
            universe=UNIVERSE,
            symbols=tuple(universe.symbols),
            interval="1d",
            requested_candles=REQUESTED_CANDLES,
            target_common_candles=TARGET_COMMON_CANDLES,
            minimum_in_window_candles=TARGET_COMMON_CANDLES,
            output_dir=snapshot_root,
            dataset_subdir=".",
            study_start=STUDY_START,
            study_end=STUDY_END,
        )
    )
    if canonical["status"] != "COVERAGE_PASSED":
        raise RuntimeError(
            "H06 canonical coverage failed: "
            + json.dumps(canonical["coverage"], sort_keys=True)
        )

    manifest_path = snapshot_root / "snapshot_manifest.json"
    assets = load_frozen_snapshot(manifest_path)
    closes = {
        symbol: [bar.close for bar in assets[symbol]]
        for symbol in universe.symbols
    }

    decision_dates = RESEARCH_CANDLES - LOOKBACK
    complete_dates = 0
    nondegenerate_dates = 0
    sector_residual_sum_max_abs = 0.0
    residual_abs_values: list[float] = []

    for index in range(LOOKBACK, RESEARCH_CANDLES):
        raw = {
            symbol: (
                closes[symbol][index - SKIP]
                / closes[symbol][index - LOOKBACK]
            ) - 1.0
            for symbol in universe.symbols
        }
        if not all(math.isfinite(value) for value in raw.values()):
            continue
        complete_dates += 1

        residuals: dict[str, float] = {}
        for members in SECTOR_MAP.values():
            sector_mean = statistics.fmean(raw[symbol] for symbol in members)
            for symbol in members:
                residuals[symbol] = raw[symbol] - sector_mean
            sector_sum = sum(residuals[symbol] for symbol in members)
            sector_residual_sum_max_abs = max(
                sector_residual_sum_max_abs,
                abs(sector_sum),
            )

        dispersion = max(residuals.values()) - min(residuals.values())
        if dispersion > 0.0:
            nondegenerate_dates += 1
        residual_abs_values.extend(abs(value) for value in residuals.values())

    coverage_ready = (
        complete_dates == decision_dates
        and nondegenerate_dates == decision_dates
        and sector_residual_sum_max_abs < 1e-12
    )

    result = {
        "schema_version": "1.1",
        "task_id": "WIDE-SEARCH-H06-SECTOR-NEUTRAL-RESIDUAL-MOMENTUM-REPAIR",
        "hypothesis_id": "H06-REPAIR",
        "recorded_at": date.today().isoformat(),
        "universe": UNIVERSE,
        "repair_of": "WIDE-SEARCH-H06-SECTOR-NEUTRAL-RESIDUAL-MOMENTUM",
        "symbols": list(universe.symbols),
        "sector_map": {key: list(value) for key, value in SECTOR_MAP.items()},
        "requested_candles": REQUESTED_CANDLES,
        "target_common_calendar": TARGET_COMMON_CANDLES,
        "research_candles_used": RESEARCH_CANDLES,
        "holdout_candles_unused": TARGET_COMMON_CANDLES - RESEARCH_CANDLES,
        "data_snapshot": canonical["data_snapshot"],
        "snapshot_fingerprint": canonical["snapshot_fingerprint"],
        "fixed_signal": {
            "formation_lookback_sessions": LOOKBACK,
            "skip_sessions": SKIP,
            "residualization": "equal_weight_sector_demean",
        },
        "coverage": {
            "status": "COVERAGE_READY" if coverage_ready else "DATA_INSUFFICIENT",
            "decision_dates_expected": decision_dates,
            "complete_decision_dates": complete_dates,
            "nondegenerate_decision_dates": nondegenerate_dates,
            "sector_residual_sum_max_abs": sector_residual_sum_max_abs,
            "median_abs_residual_score": (
                statistics.median(residual_abs_values)
                if residual_abs_values
                else 0.0
            ),
            "calendar_selection_rule": (
                "canonical:last_3500_timestamps_from_full_fixed_window_intersection"
            ),
            "repair_reason": (
                "Original 3520 request is sliced to newest bars by Yahoo loader before "
                "the fixed 2025-09-24 study cutoff; 4000 preserves the same study window "
                "while supplying acquisition headroom."
            ),
            "research_calendar_start": canonical["selected_common_calendar_start"],
            "research_calendar_end": (
                assets[universe.symbols[0]][RESEARCH_CANDLES - 1].timestamp.date().isoformat()
            ),
            "holdout_calendar_start": (
                assets[universe.symbols[0]][RESEARCH_CANDLES].timestamp.date().isoformat()
            ),
            "holdout_calendar_end": (
                assets[universe.symbols[0]][-1].timestamp.date().isoformat()
            ),
            "common_calendar_count": canonical["coverage"]["common_calendar_count"],
        },
        "governance": {
            "coverage_only": True,
            "performance_evaluation": False,
            "holdout_evaluation": False,
            "holdout_used_for_selection": False,
            "selection_used": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": canonical["safety"],
        "canonical_data_layer": "data/canonical_snapshot.py",
    }
    result["fingerprint"] = _fingerprint(result)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "task_id": result["task_id"],
                "status": result["coverage"]["status"],
                "complete_dates": result["coverage"]["complete_decision_dates"],
                "snapshot_fingerprint": result["snapshot_fingerprint"],
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="research/runs/wide_search/"
        "h06_sector_neutral_residual_momentum_repair_coverage.json",
    )
    args = parser.parse_args()
    run(output_path=args.output)


if __name__ == "__main__":
    main()
