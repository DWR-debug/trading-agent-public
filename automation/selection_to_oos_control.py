"""Re-run the Rolling-WF control on an immutable archived dataset and retain selection metadata.

This is diagnostic research only. It never downloads new market data, evaluates
selection metadata on OOS data, changes the selection profiles, changes gates,
or places orders.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from automation.rolling_geometry_control import (
    LARGE,
    RESEARCH_END,
    SMALL,
    _run_geometry,
)
from automation.verify_rolling_raw_archive import verify as verify_raw_archive
from config import settings
from config.parameter_space import ParameterSpace
from data.market_store import MarketDataStore
from automation.research_run import parameter_space_identity
from optimization.selection_profiles import available_selection_profile_names
from research.protocol import dataset_fingerprint
from validation.research_gates import ResearchGateConfig


TARGET_COUNT = 5000
EXPECTED_UNIVERSE = "benchmark"
EXPECTED_SYMBOLS = ("IWM", "QQQ", "SPY")


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        _canonical(value).encode("utf-8")
    ).hexdigest()


def _assert_safety(payload: dict, label: str) -> None:
    safety = payload.get("safety", {})
    if safety.get("paper_only") is not True:
        raise ValueError(f"{label}: Paper-Only safety flag is not enabled.")
    if safety.get("live_trading_enabled") is not False:
        raise ValueError(f"{label}: live trading must remain disabled.")
    if safety.get("orders_enabled") is not False:
        raise ValueError(f"{label}: orders must remain disabled.")


def _core_window(window: dict) -> dict:
    return {
        "window_index": window["window_index"],
        "train_size": window["train_size"],
        "test_size": window["test_size"],
        "step_size": window["step_size"],
        "train_start_index": window["train_start_index"],
        "train_end_index": window["train_end_index"],
        "test_start_index": window["test_start_index"],
        "test_end_index": window["test_end_index"],
        "test_start": window["test_start"],
        "test_end": window["test_end"],
        "candidate": window["candidate"],
        "candidate_fingerprint": window["candidate_fingerprint"],
        "net_profit_eur": window["net_profit_eur"],
        "return_percent": window["return_percent"],
        "win_rate_percent": window["win_rate_percent"],
        "profit_factor": window["profit_factor"],
        "max_drawdown_percent": window["max_drawdown_percent"],
        "sharpe_ratio": window["sharpe_ratio"],
        "trade_count": window["trade_count"],
        "average_trade_eur": window["average_trade_eur"],
    }


def _core_run(run: dict) -> dict:
    return {
        "geometry": run["geometry"],
        "train_size": run["train_size"],
        "test_size": run["test_size"],
        "step_size": run["step_size"],
        "window_count": run["window_count"],
        "summary": run["summary"],
        "gate": run["gate"],
    }


def _verify_core_equivalence(
    source: dict,
    enriched: dict,
) -> None:
    """Fail closed if enrichment changes any pre-existing control result."""

    source_by_key = {}
    enriched_by_key = {}

    for dataset in source["datasets"]:
        for profile in dataset["profiles"]:
            for geometry in ("small", "large"):
                for window in profile[geometry]["windows"]:
                    key = (
                        dataset["symbol"],
                        profile["selection_profile"],
                        geometry,
                        window["window_index"],
                    )
                    source_by_key[key] = _core_window(window)

    for dataset in enriched["datasets"]:
        for profile in dataset["profiles"]:
            for geometry in ("small", "large"):
                for window in profile[geometry]["windows"]:
                    key = (
                        dataset["symbol"],
                        profile["selection_profile"],
                        geometry,
                        window["window_index"],
                    )
                    enriched_by_key[key] = _core_window(window)

    if set(source_by_key) != set(enriched_by_key):
        raise RuntimeError("Source- und angereicherte Window-Menge unterscheiden sich.")

    for key in sorted(source_by_key):
        if _canonical(source_by_key[key]) != _canonical(enriched_by_key[key]):
            raise RuntimeError(
                f"Bestehender Rolling-Control-Befund verändert: {key}"
            )

    source_runs = {}
    enriched_runs = {}
    for payload, target in (
        (source, source_runs),
        (enriched, enriched_runs),
    ):
        for dataset in payload["datasets"]:
            for profile in dataset["profiles"]:
                for geometry in ("small", "large"):
                    run = profile[geometry]
                    key = (
                        dataset["symbol"],
                        profile["selection_profile"],
                        geometry,
                    )
                    target[key] = _core_run(run)

    if set(source_runs) != set(enriched_runs):
        raise RuntimeError("Source- und angereicherte Run-Menge unterscheiden sich.")

    for key in sorted(source_runs):
        if _canonical(source_runs[key]) != _canonical(enriched_runs[key]):
            raise RuntimeError(
                f"Bestehender Rolling-Control-Run verändert: {key}"
            )


def build_control(
    source_rolling: dict,
    source_manifest: dict,
    archive_manifest: dict,
    *,
    data_dir: str | Path,
    source_manifest_path: str | Path,
) -> dict:
    _assert_safety(source_rolling, "Source Rolling-Control")
    _assert_safety(source_manifest, "Source data manifest")
    _assert_safety(archive_manifest, "Archive manifest")

    if source_rolling.get("diagnostic_type") != "rolling_geometry_time_phase_control":
        raise ValueError("Unexpected source Rolling-Control diagnostic type.")
    if source_rolling.get("universe") != EXPECTED_UNIVERSE:
        raise ValueError("Unexpected source Rolling-Control universe.")
    if int(source_rolling.get("target_count", 0)) != TARGET_COUNT:
        raise ValueError("Unexpected source Rolling-Control target count.")
    if int(source_rolling.get("research_candle_count", 0)) != RESEARCH_END:
        raise ValueError("Unexpected source Rolling-Control research length.")

    if source_manifest.get("source") != "yahoo_chart":
        raise ValueError("Unexpected source data origin.")
    if source_manifest.get("universe") != EXPECTED_UNIVERSE:
        raise ValueError("Unexpected source data universe.")
    if int(source_manifest.get("target_count", 0)) != TARGET_COUNT:
        raise ValueError("Unexpected source data target count.")

    symbols = tuple(sorted(item["symbol"] for item in source_manifest["datasets"]))
    if symbols != tuple(sorted(EXPECTED_SYMBOLS)):
        raise ValueError(f"Unexpected symbols: {symbols!r}")

    if archive_manifest.get("manifest_fingerprint") != source_manifest.get(
        "manifest_fingerprint"
    ):
        raise ValueError("Archive/data manifest fingerprint mismatch.")

    source_profiles = tuple(source_rolling.get("selection_profiles", ()))
    profiles = available_selection_profile_names()
    if source_profiles != profiles:
        raise ValueError(
            f"Selection-Profile-Menge verändert: {profiles!r} != {source_profiles!r}"
        )

    archive_verification = verify_raw_archive(
        source_manifest_path,
        data_dir=data_dir,
        expected_count=TARGET_COUNT,
    )

    store = MarketDataStore(base_dir=data_dir)
    parameter_space = ParameterSpace()
    if parameter_space_identity(parameter_space) != source_rolling["parameter_space"]:
        raise ValueError("Parameterraum stimmt nicht mit dem Source-Control überein.")
    gate_config = ResearchGateConfig()

    datasets = []
    for item in source_manifest["datasets"]:
        symbol = item["symbol"]
        interval = item["interval"]
        candles = tuple(store.load(symbol, interval))

        if len(candles) != TARGET_COUNT:
            raise RuntimeError(
                f"{symbol}: {len(candles)} Candles statt {TARGET_COUNT}."
            )

        if item["fingerprint"] != archive_verification["datasets"][
            next(
                i
                for i, archived in enumerate(
                    archive_verification["datasets"]
                )
                if archived["symbol"] == symbol
            )
        ]["dataset_fingerprint"]:
            raise RuntimeError(f"{symbol}: immutable Dataset-Fingerprint abweichend.")

        research = candles[:RESEARCH_END]
        profile_rows = []

        for profile in profiles:
            small = _run_geometry(
                research,
                symbol,
                profile,
                "small_1125_225",
                SMALL,
                gate_config,
                parameter_space,
            )
            large = _run_geometry(
                research,
                symbol,
                profile,
                "large_2250_450",
                LARGE,
                gate_config,
                parameter_space,
            )
            profile_rows.append(
                {
                    "selection_profile": profile,
                    "small": small,
                    "large": large,
                }
            )

        datasets.append(
            {
                "symbol": symbol,
                "interval": interval,
                "full_data_fingerprint": item["fingerprint"],
                "research_fingerprint": dataset_fingerprint(research),
                "research_start": research[0].timestamp.isoformat(),
                "research_end": research[-1].timestamp.isoformat(),
                "profiles": profile_rows,
            }
        )

    enriched = {
        "schema_version": 1,
        "diagnostic_type": "rolling_selection_to_oos_control",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "source_diagnostic_fingerprint": source_rolling[
            "diagnostic_fingerprint"
        ],
        "source_manifest_fingerprint": source_manifest[
            "manifest_fingerprint"
        ],
        "source_run_id": source_manifest["provenance"].get("run_id"),
        "universe": EXPECTED_UNIVERSE,
        "target_count": TARGET_COUNT,
        "research_candle_count": RESEARCH_END,
        "parameter_space": copy.deepcopy(source_rolling["parameter_space"]),
        "selection_profiles": list(profiles),
        "design": {
            "small_geometry": {
                "train_size": SMALL[0],
                "test_size": SMALL[1],
                "step_size": SMALL[2],
                "window_count": 15,
            },
            "large_geometry": {
                "train_size": LARGE[0],
                "test_size": LARGE[1],
                "step_size": LARGE[2],
                "window_count": 5,
            },
            "common_test_span": [2250, 4500],
            "small_common_window_indices": list(range(6, 16)),
            "holdout_used": False,
            "no_strategy_changes": True,
            "no_parameter_space_changes": True,
            "no_gate_changes": True,
            "selection_metadata_only": True,
            "source_core_results_verified_unchanged": True,
        },
        "datasets": datasets,
        "archive_verification": {
            "manifest_fingerprint": archive_verification[
                "manifest_fingerprint"
            ],
            "datasets": archive_verification["datasets"],
        },
        "interpretation_scope": {
            "diagnostic_only": True,
            "same_immutable_raw_data": True,
            "same_selection_profiles": True,
            "same_parameter_space": True,
            "same_gate_configuration": True,
            "same_oos_evaluations": True,
            "training_selection_metadata_archived": True,
            "selection_rank_is_profile_rank_one_by_definition": True,
            "raw_score_rank_is_informative_across_profiles": True,
            "no_oos_ranking_used_for_selection": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    _verify_core_equivalence(source_rolling, enriched)
    enriched["diagnostic_fingerprint"] = _fingerprint(enriched)
    return enriched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-rolling-json", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--archive-manifest", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument(
        "--output-dir",
        default="research/selection_to_oos_control",
    )
    args = parser.parse_args()

    source_rolling = json.loads(
        Path(args.source_rolling_json).read_text(encoding="utf-8")
    )
    source_manifest = json.loads(
        Path(args.source_manifest).read_text(encoding="utf-8")
    )
    archive_manifest = json.loads(
        Path(args.archive_manifest).read_text(encoding="utf-8")
    )

    result = build_control(
        source_rolling,
        source_manifest,
        archive_manifest,
        data_dir=args.data_dir,
        source_manifest_path=args.source_manifest,
    )

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "selection_to_oos_control.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    print("SELECTION_TO_OOS_CONTROL: COMPLETED")
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    print("SOURCE_DIAGNOSTIC_FINGERPRINT:", result["source_diagnostic_fingerprint"])
    print("PAPER_ONLY:", result["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", result["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
