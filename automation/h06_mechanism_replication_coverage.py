"""Research-only coverage repair preflight for H06 sector-neutral residual momentum.

No forward-return evaluation, no holdout use, no parameter search, no asset selection.
The preflight verifies the fixed sector map, common calendar, and signal-history contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import os
from datetime import date
from pathlib import Path

from config import settings
from data.canonical_snapshot import (
    SnapshotSpec,
    build_frozen_snapshot,
    load_frozen_snapshot,
)
from research.asset_universes import get_universe, list_universes

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = "validation_2026_09_26_h06_mechanism_replication"
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
TARGET_COMMON_CANDLES = 3500
RESEARCH_CANDLES = 2798
REQUESTED_CANDLES = 4000
LOOKBACK = 252
SKIP = 21

SECTOR_MAP = {
    "technology": ("MU", "ADBE", "CRM"),
    "healthcare": ("ABT", "BMY", "BAX"),
    "industrials": ("PH", "ROK", "DOV"),
    "consumer_staples": ("CPB", "SJM", "CAG"),
    "utilities": ("EXC", "SRE", "CMS"),
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


def _raw_score(closes: list[float], index: int) -> float:
    return (
        closes[index - SKIP] / closes[index - LOOKBACK]
    ) - 1.0


def run(
    *,
    output_path: str | Path =
    "research/runs/wide_search/h06_mechanism_replication_coverage.json",
) -> dict:
    if (
        settings.PAPER_ONLY is not True
        or settings.LIVE_TRADING_ENABLED is not False
        or settings.ORDERS_ENABLED is not False
    ):
        raise RuntimeError("H06 coverage requires the paper-only safety configuration.")

    universe = get_universe(UNIVERSE)
    expected_set = set(universe.symbols)
    for existing in list_universes():
        if existing.name == UNIVERSE:
            continue
        overlap = expected_set.intersection(existing.symbols)
        if overlap:
            raise RuntimeError(
                f"Replication universe overlaps existing universe {existing.name}: {sorted(overlap)}"
            )
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
    snapshot_dir = output.parent / "h06_replication_datasets"
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
    if canonical["status"] != "COVERAGE_PASSED":
        raise RuntimeError(
            "H06 canonical coverage failed: "
            + json.dumps(canonical["coverage"], sort_keys=True)
        )

    assets = load_frozen_snapshot(snapshot_dir / "snapshot_manifest.json")
    closes = {
        symbol: [bar.close for bar in assets[symbol][:RESEARCH_CANDLES]]
        for symbol in universe.symbols
    }

    decision_dates = RESEARCH_CANDLES - LOOKBACK
    complete_dates = 0
    nondegenerate_dates = 0
    sector_residual_sum_max_abs = 0.0
    residual_abs_values: list[float] = []

    for index in range(LOOKBACK, RESEARCH_CANDLES):
        raw = {
            symbol: _raw_score(closes[symbol], index)
            for symbol in universe.symbols
        }
        if not all(math.isfinite(value) for value in raw.values()):
            continue
        complete_dates += 1

        residuals = {}
        for sector, members in SECTOR_MAP.items():
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
        "schema_version": "1.0",
        "task_id": "WIDE-SEARCH-H06-MECHANISM-REPLICATION-COVERAGE",
        "workflow_run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
        "hypothesis_id": "H06",
        "recorded_at": date.today().isoformat(),
        "universe": UNIVERSE,
        "replication_of": "H06-SECTOR-NEUTRAL-RESIDUAL-MOMENTUM",
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
            "study_start": STUDY_START.isoformat(),
            "study_end": STUDY_END.isoformat(),
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
            "replication_reason": "Independent mechanism replication: same acquisition headroom and fixed study geometry on a fresh disjoint universe.",
            "research_calendar_start": canonical["selected_common_calendar_start"],
            "research_calendar_end": (
                assets[universe.symbols[0]][RESEARCH_CANDLES - 1]
                .timestamp.date()
                .isoformat()
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

    output = Path(output_path)
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
        "h06_mechanism_replication_coverage.json",
    )
    args = parser.parse_args()
    run(output_path=args.output)


if __name__ == "__main__":
    main()
