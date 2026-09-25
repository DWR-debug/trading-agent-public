"""Q015: fixed, symmetric mechanism-discrimination diagnostic on the frozen Q014 dataset."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

import statsmodels.api as sm

from config import settings
from automation.information_alpha_discovery import (
    DEFAULT_ASSETS,
    FIXED_FEATURES,
    _ranks,
    _yahoo_daily,
)
from automation.information_alpha_redundancy import MECHANISM_GROUPS
from automation.information_alpha_redundancy_long_window import (
    CHUNK_WINDOWS,
    _build_observations,
    _load_chunks,
)

DEFAULT_START = date(2025, 9, 25)
DEFAULT_END = date(2026, 9, 24)
MIN_TOTAL_OBSERVATIONS = 80
MIN_EVENT_WINDOWS = 40
MIN_CELL_OBSERVATIONS = 40
GROUP_ORDER = ("intensity_breadth", "severity", "tone")


def _assert_safety() -> None:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")


def _fixed_group_features(group_names: tuple[str, ...]) -> tuple[str, ...]:
    features: list[str] = []
    for group in GROUP_ORDER:
        if group in group_names:
            features.extend(MECHANISM_GROUPS[group])
    return tuple(features)


def _r2_from_features(
    observations: list[dict],
    symbol: str,
    horizon: str,
    group_names: tuple[str, ...],
) -> float:
    if not group_names:
        return 0.0
    pairs = [
        (row["features"], row["market"][symbol][horizon])
        for row in observations
        if symbol in row["market"] and row["market"][symbol][horizon] is not None
    ]
    if not pairs:
        return 0.0
    y = _ranks([target for _, target in pairs])
    feature_names = _fixed_group_features(group_names)
    x = [_ranks([payload[name] for payload, _ in pairs]) for name in feature_names]
    if not x or len(y) < MIN_CELL_OBSERVATIONS:
        return 0.0
    matrix = [list(row) for row in zip(*x)]
    matrix = sm.add_constant(matrix, has_constant="add")
    fitted = sm.OLS(y, matrix).fit()
    value = float(fitted.rsquared)
    if not value == value:  # NaN
        return 0.0
    return max(0.0, min(1.0, value))


def _subset_key(groups: tuple[str, ...]) -> str:
    return "+".join(group for group in GROUP_ORDER if group in groups) or "empty"


def _all_subset_r2(
    observations: list[dict],
    symbol: str,
    horizon: str,
) -> dict[str, float]:
    out = {"empty": 0.0}
    for size in (1, 2, 3):
        for subset in itertools.combinations(GROUP_ORDER, size):
            out[_subset_key(subset)] = _r2_from_features(
                observations, symbol, horizon, tuple(subset)
            )
    return out


def _shapley_from_subset_r2(subset_r2: dict[str, float]) -> dict[str, float]:
    values = {"empty": 0.0, **subset_r2}
    contributions = {group: 0.0 for group in GROUP_ORDER}
    permutations = tuple(itertools.permutations(GROUP_ORDER))
    for permutation in permutations:
        current: tuple[str, ...] = ()
        previous = values["empty"]
        for group in permutation:
            expanded = tuple(current) + (group,)
            key = _subset_key(expanded)
            current = expanded
            marginal = values[key] - previous
            contributions[group] += marginal / len(permutations)
            previous = values[key]
    return contributions


def _cell(
    observations: list[dict],
    symbol: str,
    horizon: str,
) -> dict:
    event_observations = [
        row
        for row in observations
        if row["has_information_event"]
        and symbol in row["market"]
        and row["market"][symbol][horizon] is not None
    ]
    sample = len(event_observations)
    if sample < MIN_CELL_OBSERVATIONS:
        return {
            "symbol": symbol,
            "horizon": horizon,
            "sample": sample,
            "status": "DATA_INSUFFICIENT",
            "subset_r2": {},
            "shapley_r2_contribution": {},
            "full_model_r2": None,
            "shapley_conservation_error": None,
        }
    subset_r2 = _all_subset_r2(event_observations, symbol, horizon)
    shapley = _shapley_from_subset_r2(subset_r2)
    full_model = subset_r2[_subset_key(GROUP_ORDER)]
    conservation_error = full_model - sum(shapley.values())
    return {
        "symbol": symbol,
        "horizon": horizon,
        "sample": sample,
        "status": "COMPLETED",
        "subset_r2": subset_r2,
        "shapley_r2_contribution": shapley,
        "full_model_r2": full_model,
        "shapley_conservation_error": conservation_error,
    }


def _aggregate_cells(cells: list[dict]) -> dict:
    completed = [cell for cell in cells if cell["status"] == "COMPLETED"]
    out = {}
    for group in GROUP_ORDER:
        values = [cell["shapley_r2_contribution"][group] for cell in completed]
        out[group] = {
            "mean_shapley_r2": mean(values) if values else None,
            "non_positive_cell_count": sum(value <= 0.0 for value in values),
            "cell_count": len(values),
        }
    return out


def freeze_q014_input(
    *,
    source_dir: str | Path,
    output_dir: str | Path,
) -> dict:
    _assert_safety()
    reports = _load_chunks(source_dir)
    daily = {}
    rows_seen = 0
    rows_skipped = 0
    for report in reports:
        rows_seen += report["data_quality"]["event_rows_seen"]
        rows_skipped += report["data_quality"]["event_rows_skipped"]
        for day, payload in report["daily_event_features"].items():
            if day in daily and daily[day] != payload:
                raise ValueError(f"Conflicting Q014 event features for duplicate day {day}.")
            daily[day] = payload
    prices = {
        symbol: {
            day.isoformat(): value
            for day, value in _yahoo_daily(
                symbol,
                DEFAULT_START - timedelta(days=7),
                DEFAULT_END + timedelta(days=10),
            ).items()
        }
        for symbol in DEFAULT_ASSETS
    }
    typed_daily = {date.fromisoformat(day): payload for day, payload in daily.items()}
    observations = _build_observations(DEFAULT_START, DEFAULT_END, typed_daily, prices)
    payload = {
        "schema_version": "1.0",
        "task_id": "Q-015-INFORMATION-ALPHA-MECHANISM-DISCRIMINATION-DIAGNOSTIC",
        "source_q014_workflow_run": 36158184847,
        "source_q014_chunk_fingerprints": {r["chunk_id"]: r["fingerprint"] for r in reports},
        "window": {"start": DEFAULT_START.isoformat(), "end": DEFAULT_END.isoformat(), "calendar_days": 365},
        "assets": list(DEFAULT_ASSETS),
        "fixed_features": list(FIXED_FEATURES),
        "mechanism_groups": {name: list(features) for name, features in MECHANISM_GROUPS.items()},
        "observations": observations,
        "event_windows": sum(1 for row in observations if row["has_information_event"]),
        "common_observations": len(observations),
        "data_quality": {
            "event_rows_seen": rows_seen,
            "event_rows_skipped": rows_skipped,
            "market_price_source": "Yahoo Finance adjusted daily close",
        },
        "point_in_time_contract": {
            "event_feature_window": "previous_market_day < event_day < target_market_day",
            "target_return": "previous_market_close -> target_market_close",
            "five_day_horizon": "target_market_close -> fifth subsequent market close",
            "same_day_return_used": False,
        },
        "selection_used": False,
        "holdout_used": False,
        "parameter_search_used": False,
        "feature_selection_used": False,
        "asset_selection_used": False,
        "horizon_selection_used": False,
        "performance_trial_authorized": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    payload["fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "q015_frozen_input.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return payload


def analyze_q015(
    input_path: str | Path,
    *,
    output_dir: str | Path,
) -> dict:
    _assert_safety()
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    observations = payload["observations"]
    event_windows = [row for row in observations if row["has_information_event"]]
    if len(observations) < MIN_TOTAL_OBSERVATIONS or len(event_windows) < MIN_EVENT_WINDOWS:
        status = "DATA_INSUFFICIENT"
        cells: list[dict] = []
    else:
        cells = [
            _cell(observations, symbol, horizon)
            for symbol in DEFAULT_ASSETS
            for horizon in ("next_market_day_return", "five_market_day_forward_return")
        ]
        status = "COMPLETED_DIAGNOSTIC_ONLY" if all(
            cell["status"] == "COMPLETED" for cell in cells
        ) else "DATA_INSUFFICIENT"
    result = {
        "schema_version": "1.0",
        "task_id": "Q-015-INFORMATION-ALPHA-MECHANISM-DISCRIMINATION-DIAGNOSTIC",
        "status": status,
        "research_only": True,
        "source_q014_workflow_run": payload["source_q014_workflow_run"],
        "source_q014_chunk_fingerprints": payload["source_q014_chunk_fingerprints"],
        "input_fingerprint": payload["fingerprint"],
        "window": payload["window"],
        "assets": list(DEFAULT_ASSETS),
        "fixed_features": list(FIXED_FEATURES),
        "mechanism_groups": {name: list(features) for name, features in MECHANISM_GROUPS.items()},
        "diagnostic_method": {
            "sample": "event-only observations with complete target return",
            "transform": "within-cell midranks for all predictors and outcome",
            "model": "OLS with intercept",
            "group_decomposition": "exact three-group Shapley decomposition of R-squared across 6 permutations",
            "subset_models": sorted({key for cell in cells for key in cell["subset_r2"].keys()}),
        },
        "minimum_data_contract": {
            "common_observations": MIN_TOTAL_OBSERVATIONS,
            "event_windows": MIN_EVENT_WINDOWS,
            "complete_event_observations_per_asset_horizon": MIN_CELL_OBSERVATIONS,
        },
        "cells": cells,
        "aggregate": _aggregate_cells(cells),
        "selection_used": False,
        "holdout_used": False,
        "parameter_search_used": False,
        "feature_selection_used": False,
        "asset_selection_used": False,
        "horizon_selection_used": False,
        "performance_trial_authorized": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    result["fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "q015_mechanism_discrimination.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("run", "freeze", "analyze"), default="run")
    parser.add_argument("--source-dir", default="research/runs/information_alpha_mechanism_discrimination/q014_chunks")
    parser.add_argument("--input-path", default="research/runs/information_alpha_mechanism_discrimination/q015_frozen_input/q015_frozen_input.json")
    parser.add_argument("--output-dir", default="research/runs/information_alpha_mechanism_discrimination/q015")
    args = parser.parse_args()
    if args.mode in ("run", "freeze"):
        input_dir = Path(args.input_path).parent
        freeze_q014_input(source_dir=args.source_dir, output_dir=input_dir)
    if args.mode in ("run", "analyze"):
        input_path = (
            args.input_path
            if args.mode == "analyze"
            else str(Path(args.input_path).parent / "q015_frozen_input.json")
        )
        report = analyze_q015(input_path, output_dir=args.output_dir)
        print("Q015_STATUS:", report["status"])
        print("Q015_FINGERPRINT:", report["fingerprint"])
        print("Q015_INPUT_FINGERPRINT:", report["input_fingerprint"])
        print("Q015_EVENT_WINDOWS:", len([r for r in json.loads(Path(input_path).read_text())["observations"] if r["has_information_event"]]))
        return 0 if report["status"] != "DATA_INSUFFICIENT" else 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
