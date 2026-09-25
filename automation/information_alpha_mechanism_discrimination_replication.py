"""Q016: temporally disjoint replication of the fixed Q015 mechanism diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

from config import settings
from data.gdelt_events import GDELTDataUnavailableError
from automation.information_alpha_discovery import (
    DEFAULT_ASSETS,
    FIXED_FEATURES,
    _daily_event_features,
    _load_events,
    _yahoo_daily,
)
from automation.information_alpha_mechanism_discrimination import (
    GROUP_ORDER,
    MIN_CELL_OBSERVATIONS,
    MIN_EVENT_WINDOWS,
    MIN_TOTAL_OBSERVATIONS,
    _aggregate_cells,
    _all_subset_r2,
    _cell,
)
from automation.information_alpha_redundancy_long_window import _build_observations

DEFAULT_START = date(2024, 9, 25)
DEFAULT_END = date(2025, 9, 24)
REFERENCE_START = date(2025, 9, 25)
REFERENCE_END = date(2026, 9, 24)
CHUNK_WINDOWS = (
    ("01", date(2024, 9, 25), date(2024, 12, 25)),
    ("02", date(2024, 12, 26), date(2025, 3, 25)),
    ("03", date(2025, 3, 26), date(2025, 6, 25)),
    ("04", date(2025, 6, 26), date(2025, 9, 24)),
)
TASK_ID = "Q-016-INFORMATION-ALPHA-MECHANISM-DISCRIMINATION-REPLICATION"


def _assert_safety() -> None:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")


def _chunk_spec(chunk_id: str) -> tuple[str, date, date]:
    for spec in CHUNK_WINDOWS:
        if spec[0] == chunk_id:
            return spec
    raise ValueError(f"Unknown Q016 chunk id: {chunk_id}")


def _assert_temporal_disjointness() -> None:
    if not DEFAULT_END < REFERENCE_START:
        raise AssertionError("Q016 window must be fully disjoint from the Q015 reference window.")


def collect_q016_chunk(
    chunk_id: str,
    *,
    output_dir: str | Path = "research/runs/information_alpha_mechanism_discrimination_replication/q016_chunks",
) -> dict:
    _assert_safety()
    _, start, end = _chunk_spec(chunk_id)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    try:
        events, parse_stats = _load_events(start, end, None)
    except GDELTDataUnavailableError as exc:
        payload = {
            "schema_version": "1.0",
            "task_id": TASK_ID,
            "chunk_id": chunk_id,
            "status": "DATA_INSUFFICIENT",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "assets": list(DEFAULT_ASSETS),
            "fixed_features": list(FIXED_FEATURES),
            "daily_event_features": {},
            "data_quality": {
                "event_rows_seen": 0,
                "event_rows_skipped": 0,
                "missing_export": {
                    "day": exc.day,
                    "url": exc.url,
                    "status_code": exc.status_code,
                },
            },
            "point_in_time_contract": {
                "event_feature_window": "previous_market_day < event_day < target_market_day",
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
        path = root / f"q016_chunk_{chunk_id}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        return payload

    daily = _daily_event_features(events)
    payload = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "chunk_id": chunk_id,
        "status": "COMPLETED_DATA_COLLECTION",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "assets": list(DEFAULT_ASSETS),
        "fixed_features": list(FIXED_FEATURES),
        "daily_event_features": {
            day.isoformat(): values for day, values in sorted(daily.items())
        },
        "data_quality": {
            "event_rows_seen": parse_stats["rows_seen"],
            "event_rows_skipped": parse_stats["rows_skipped"],
        },
        "point_in_time_contract": {
            "event_feature_window": "previous_market_day < event_day < target_market_day",
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
    path = root / f"q016_chunk_{chunk_id}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return payload


def _load_chunks(chunk_dir: str | Path) -> list[dict]:
    root = Path(chunk_dir)
    expected = [(chunk_id, start.isoformat(), end.isoformat()) for chunk_id, start, end in CHUNK_WINDOWS]
    reports = []
    for chunk_id, _, _ in CHUNK_WINDOWS:
        path = root / f"q016_chunk_{chunk_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing Q016 chunk: {path}")
        reports.append(json.loads(path.read_text(encoding="utf-8")))
    actual = [(r["chunk_id"], r["start"], r["end"]) for r in reports]
    if actual != expected:
        raise ValueError("Q016 chunk window contract mismatch.")
    return reports


def freeze_q016_input(
    *,
    chunk_dir: str | Path,
    output_dir: str | Path = "research/runs/information_alpha_mechanism_discrimination_replication/q016_frozen_input",
) -> dict:
    _assert_safety()
    _assert_temporal_disjointness()
    reports = _load_chunks(chunk_dir)
    incomplete = [report for report in reports if report.get("status") == "DATA_INSUFFICIENT"]
    if incomplete:
        payload = {
            "schema_version": "1.0",
            "task_id": TASK_ID,
            "source_task": "Q-015-INFORMATION-ALPHA-MECHANISM-DISCRIMINATION-DIAGNOSTIC",
            "source_q015_workflow_run": 36161950582,
            "source_q015_artifact_id": 10875399037,
            "source_q015_result_fingerprint": "f7be165efe86a223f1e15dc0cfb206e992a95fecc596197a562c6eb65386e2da",
            "source_q015_input_fingerprint": "5475911e19dfae4aabbce1c66775962dacd7815b86f7dc4e63fe3ecb4fab4836",
            "source_q015_window": {"start": REFERENCE_START.isoformat(), "end": REFERENCE_END.isoformat(), "calendar_days": 365},
            "window": {"start": DEFAULT_START.isoformat(), "end": DEFAULT_END.isoformat(), "calendar_days": 365, "strictly_temporally_disjoint_from_q015": True},
            "assets": list(DEFAULT_ASSETS),
            "fixed_features": list(FIXED_FEATURES),
            "mechanism_groups": {
                "intensity_breadth": ["event_count", "attention_score", "source_breadth", "article_count"],
                "severity": ["negative_goldstein"],
                "tone": ["mean_tone"],
            },
            "status": "DATA_INSUFFICIENT",
            "observations": [],
            "event_windows": 0,
            "common_observations": 0,
            "chunk_fingerprints": {report["chunk_id"]: report["fingerprint"] for report in reports},
            "incomplete_chunks": [
                {
                    "chunk_id": report["chunk_id"],
                    "start": report["start"],
                    "end": report["end"],
                    "missing_export": report["data_quality"].get("missing_export"),
                }
                for report in incomplete
            ],
            "data_quality": {
                "source": "GDELT daily event exports",
                "status": "DATA_INSUFFICIENT",
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
        (root / "q016_frozen_input.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        return payload

    daily: dict[str, dict[str, float]] = {}
    rows_seen = 0
    rows_skipped = 0
    chunk_fingerprints = {}
    for report in reports:
        chunk_fingerprints[report["chunk_id"]] = report["fingerprint"]
        rows_seen += report["data_quality"]["event_rows_seen"]
        rows_skipped += report["data_quality"]["event_rows_skipped"]
        for day, payload in report["daily_event_features"].items():
            if day in daily and daily[day] != payload:
                raise ValueError(f"Conflicting event features for duplicate day {day}.")
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
        "task_id": TASK_ID,
        "source_task": "Q-015-INFORMATION-ALPHA-MECHANISM-DISCRIMINATION-DIAGNOSTIC",
        "source_q015_workflow_run": 36161950582,
        "source_q015_artifact_id": 10875399037,
        "source_q015_result_fingerprint": "f7be165efe86a223f1e15dc0cfb206e992a95fecc596197a562c6eb65386e2da",
        "source_q015_input_fingerprint": "5475911e19dfae4aabbce1c66775962dacd7815b86f7dc4e63fe3ecb4fab4836",
        "source_q015_window": {"start": REFERENCE_START.isoformat(), "end": REFERENCE_END.isoformat(), "calendar_days": 365},
        "window": {"start": DEFAULT_START.isoformat(), "end": DEFAULT_END.isoformat(), "calendar_days": 365, "strictly_temporally_disjoint_from_q015": True},
        "assets": list(DEFAULT_ASSETS),
        "fixed_features": list(FIXED_FEATURES),
        "mechanism_groups": {
            "intensity_breadth": ["event_count", "attention_score", "source_breadth", "article_count"],
            "severity": ["negative_goldstein"],
            "tone": ["mean_tone"],
        },
        "chunk_fingerprints": chunk_fingerprints,
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
    (root / "q016_frozen_input.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return payload


def analyze_q016(
    input_path: str | Path,
    *,
    output_dir: str | Path = "research/runs/information_alpha_mechanism_discrimination_replication/q016",
) -> dict:
    _assert_safety()
    _assert_temporal_disjointness()
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    if payload["window"]["start"] != DEFAULT_START.isoformat() or payload["window"]["end"] != DEFAULT_END.isoformat():
        raise ValueError("Q016 input window does not match the fixed replication window.")
    if not payload["window"]["strictly_temporally_disjoint_from_q015"]:
        raise ValueError("Q016 temporal-disjointness contract is not asserted.")

    if payload.get("status") == "DATA_INSUFFICIENT":
        status = "DATA_INSUFFICIENT"
        cells = []
        subset_keys = []
    else:
        observations = payload["observations"]
        event_windows = [row for row in observations if row["has_information_event"]]
        if len(observations) < MIN_TOTAL_OBSERVATIONS or len(event_windows) < MIN_EVENT_WINDOWS:
            status = "DATA_INSUFFICIENT"
            cells = []
        else:
            cells = [
                _cell(observations, symbol, horizon)
                for symbol in DEFAULT_ASSETS
                for horizon in ("next_market_day_return", "five_market_day_forward_return")
            ]
            status = "COMPLETED_DIAGNOSTIC_ONLY" if all(cell["status"] == "COMPLETED" for cell in cells) else "DATA_INSUFFICIENT"

        event_sample = [row for row in observations if row["has_information_event"]]
        subset_keys = sorted(_all_subset_r2(event_sample, DEFAULT_ASSETS[0], "next_market_day_return").keys()) if event_sample else []
    result = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "status": status,
        "research_only": True,
        "replication_only": True,
        "source_q015_workflow_run": payload["source_q015_workflow_run"],
        "source_q015_artifact_id": payload["source_q015_artifact_id"],
        "source_q015_result_fingerprint": payload["source_q015_result_fingerprint"],
        "source_q015_input_fingerprint": payload["source_q015_input_fingerprint"],
        "input_fingerprint": payload["fingerprint"],
        "window": payload["window"],
        "assets": list(DEFAULT_ASSETS),
        "fixed_features": list(FIXED_FEATURES),
        "mechanism_groups": payload["mechanism_groups"],
        "diagnostic_method": {
            "sample": "event-only observations with complete target return",
            "transform": "within-cell midranks for all predictors and outcome",
            "model": "OLS with intercept",
            "group_decomposition": "exact three-group Shapley decomposition of R-squared across 6 permutations",
            "fixed_group_order": list(GROUP_ORDER),
            "subset_models": subset_keys,
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
    (root / "q016_mechanism_discrimination_replication.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("collect_chunk", "freeze", "run", "analyze"), default="run")
    parser.add_argument("--chunk-id")
    parser.add_argument("--chunk-dir", default="research/runs/information_alpha_mechanism_discrimination_replication/q016_chunks")
    parser.add_argument("--input-path", default="research/runs/information_alpha_mechanism_discrimination_replication/q016_frozen_input/q016_frozen_input.json")
    parser.add_argument("--output-dir", default="research/runs/information_alpha_mechanism_discrimination_replication/q016")
    args = parser.parse_args()

    if args.mode == "collect_chunk":
        if args.chunk_id is None:
            raise ValueError("--chunk-id is required for collect_chunk")
        report = collect_q016_chunk(args.chunk_id, output_dir=args.chunk_dir)
        print("Q016_CHUNK:", report["chunk_id"])
        print("Q016_CHUNK_FINGERPRINT:", report["fingerprint"])
        return 0

    if args.mode == "freeze":
        payload = freeze_q016_input(chunk_dir=args.chunk_dir, output_dir=Path(args.input_path).parent)
        print("Q016_INPUT_FINGERPRINT:", payload["fingerprint"])
        return 0

    if args.mode == "analyze":
        report = analyze_q016(args.input_path, output_dir=args.output_dir)
    else:
        freeze_q016_input(chunk_dir=args.chunk_dir, output_dir=Path(args.input_path).parent)
        report = analyze_q016(args.input_path, output_dir=args.output_dir)

    print("Q016_STATUS:", report["status"])
    print("Q016_FINGERPRINT:", report["fingerprint"])
    print("Q016_INPUT_FINGERPRINT:", report["input_fingerprint"])
    frozen = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    print("Q016_OBSERVATIONS:", len(frozen["observations"]))
    print("Q016_EVENT_WINDOWS:", len([r for r in frozen["observations"] if r["has_information_event"]]))
    return 0 if report["status"] != "DATA_INSUFFICIENT" else 3


if __name__ == "__main__":
    raise SystemExit(main())
