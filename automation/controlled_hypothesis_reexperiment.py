"""Paired controlled re-experiment for the predeclared hypothesis.

Only mean_reversion.window is swapped 5 <-> 10 on the exact source OOS windows.
Selection, the other four parameters, the data and gate definitions stay fixed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

from backtesting.engine import BacktestEngine
from config import settings
from config.parameters import MeanReversionParameters, MomentumParameters, StrategyParameters
from data.market_store import MarketDataStore
from research.protocol import dataset_fingerprint

SOURCE_RUN_ID = "35747170025"
SOURCE_REPORT_FINGERPRINT = "06ba10b5fb540de887fd2494f8cc328fa849b8f80ac0a867b16386a73525e0e2"
SOURCE_UNIVERSE = "benchmark"
TARGET_COUNT = 5000
RESEARCH_CANDLES = 4500
PROFILE = "trade_rich"
GEOMETRY = "small"
FORMAL_ASSETS = {"IWM", "QQQ"}
WINDOW_10_SIGNATURE = "069c70d7614f7b64bc9217c61ae4c604399020446684c423da83b1483ca431c9"
WINDOW_5_SIGNATURE = "6ef4826bffba4c449596f6c05e8d5da26c2a970993561ad9d0d82e9f87fb7b7a"
FIXED = {
    "risk_per_trade": 0.0025,
    "leverage": 1.0,
    "momentum.lookback": 3,
    "mean_reversion.threshold": 0.01,
}
DATA_FINGERPRINTS = {
    "IWM": "51a385563ebd0a3a659d844bcbeccab354f79fd52c1d521633865ff0de476821",
    "QQQ": "7923245473b99e9f9f32dafe58d48c3ba101454048eba04a9c14508aacc3b52f",
    "SPY": "8c62c32b84fa68b7633670302f90a7f935dc047a1a7ae33cc0e561e79f8266a3",
}
SAFETY = {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False}


def values(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_per_trade": float(candidate["risk_per_trade"]),
        "leverage": float(candidate["leverage"]),
        "momentum.lookback": int(candidate["strategy"]["momentum"]["lookback"]),
        "mean_reversion.window": int(candidate["strategy"]["mean_reversion"]["window"]),
        "mean_reversion.threshold": float(candidate["strategy"]["mean_reversion"]["threshold"]),
    }


def fingerprint(candidate: dict[str, Any]) -> str:
    raw = json.dumps(candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def counterfactual(candidate: dict[str, Any]) -> dict[str, Any]:
    v = values(candidate)
    for key, expected in FIXED.items():
        if v[key] != expected:
            raise ValueError("Source candidate is outside the predeclared fixed-parameter hypothesis.")
    window = v["mean_reversion.window"]
    if window not in (5, 10):
        raise ValueError(f"Unexpected source window: {window}")
    other = 10 if window == 5 else 5
    return {
        "risk_per_trade": v["risk_per_trade"],
        "leverage": v["leverage"],
        "strategy": {
            "momentum": {"lookback": v["momentum.lookback"]},
            "mean_reversion": {
                "window": other,
                "threshold": v["mean_reversion.threshold"],
            },
        },
    }


def parameter_diff(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    a, b = values(left), values(right)
    return sorted(k for k in a if a[k] != b[k])


def candidate_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_per_trade": float(data["risk_per_trade"]),
        "leverage": float(data["leverage"]),
        "strategy": {
            "momentum": {"lookback": int(data["strategy"]["momentum"]["lookback"])},
            "mean_reversion": {
                "window": int(data["strategy"]["mean_reversion"]["window"]),
                "threshold": float(data["strategy"]["mean_reversion"]["threshold"]),
            },
        },
    }


def validate_source(rolling: dict[str, Any], manifest: dict[str, Any]) -> None:
    if rolling.get("diagnostic_type") != "rolling_geometry_time_phase_control":
        raise ValueError("Unexpected rolling source diagnostic type.")
    if rolling.get("universe") != SOURCE_UNIVERSE:
        raise ValueError("Unexpected source universe.")
    if int(rolling.get("target_count", 0)) != TARGET_COUNT:
        raise ValueError("Unexpected source target count.")
    if int(rolling.get("research_candle_count", 0)) != RESEARCH_CANDLES:
        raise ValueError("Unexpected source research candle count.")
    if rolling.get("safety") != SAFETY or manifest.get("safety") != SAFETY:
        raise ValueError("Paper-Only safety contract violated.")
    actual = {item["symbol"]: item["fingerprint"] for item in manifest.get("datasets", [])}
    if actual != DATA_FINGERPRINTS:
        raise ValueError("Raw dataset fingerprints do not match the immutable historical source.")
    if int(manifest.get("target_count", 0)) != TARGET_COUNT:
        raise ValueError("Data manifest target count mismatch.")


def metric_equal(source: Any, actual: float, tolerance: float = 1e-9) -> bool:
    if source == "inf":
        return math.isinf(actual)
    return math.isclose(float(source), float(actual), rel_tol=tolerance, abs_tol=tolerance)


def run_candidate(candidate: dict[str, Any], candles, symbol: str) -> dict[str, Any]:
    strategy = StrategyParameters(
        momentum=MomentumParameters(lookback=int(candidate["strategy"]["momentum"]["lookback"])),
        mean_reversion=MeanReversionParameters(
            window=int(candidate["strategy"]["mean_reversion"]["window"]),
            threshold=float(candidate["strategy"]["mean_reversion"]["threshold"]),
        ),
    )
    result = BacktestEngine(
        initial_capital=settings.INITIAL_CAPITAL_EUR,
        risk_per_trade=float(candidate["risk_per_trade"]),
        leverage=float(candidate["leverage"]),
        fee_rate=0.001,
        slippage_rate=0.0005,
        parameters=strategy,
    ).run(symbol=symbol, candles=candles)
    return result.metrics


def primary(metrics: dict[str, Any]) -> dict[str, bool]:
    pf = math.inf if metrics["profit_factor"] == "inf" else float(metrics["profit_factor"])
    return {
        "positive_profit": float(metrics["net_profit_eur"]) > 0,
        "profit_factor_pass": pf >= 1.10,
        "drawdown_pass": float(metrics["max_drawdown_percent"]) <= 10.0,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    base = [float(x["baseline"]["net_profit_eur"]) for x in rows]
    cf = [float(x["counterfactual"]["net_profit_eur"]) for x in rows]
    delta = [float(x["paired_delta_eur"]) for x in rows]
    return {
        "window_count": len(rows),
        "baseline_total_profit_eur": sum(base),
        "counterfactual_total_profit_eur": sum(cf),
        "paired_delta_total_eur": sum(delta),
        "median_paired_delta_eur": statistics.median(delta),
        "baseline_positive_rate": sum(x > 0 for x in base) / len(base),
        "counterfactual_positive_rate": sum(x > 0 for x in cf) / len(cf),
        "baseline_pf_pass_rate": sum(bool(x["baseline_primary"]["profit_factor_pass"]) for x in rows) / len(rows),
        "counterfactual_pf_pass_rate": sum(bool(x["counterfactual_primary"]["profit_factor_pass"]) for x in rows) / len(rows),
        "counterfactual_better_profit_count": sum(x > 0 for x in delta),
        "baseline_better_profit_count": sum(x < 0 for x in delta),
        "equal_profit_count": sum(x == 0 for x in delta),
    }


def run_experiment(rolling_json: str | Path, manifest_json: str | Path, data_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    rolling = json.loads(Path(rolling_json).read_text(encoding="utf-8"))
    manifest = json.loads(Path(manifest_json).read_text(encoding="utf-8"))
    validate_source(rolling, manifest)

    store = MarketDataStore(base_dir=data_dir)
    paired: list[dict[str, Any]] = []

    for dataset in rolling["datasets"]:
        symbol = dataset["symbol"]
        candles = tuple(store.load(symbol, dataset["interval"]))
        if len(candles) != TARGET_COUNT or dataset_fingerprint(candles) != DATA_FINGERPRINTS[symbol]:
            raise ValueError(f"{symbol}: raw data integrity mismatch.")

        profile = next((p for p in dataset["profiles"] if p["selection_profile"] == PROFILE), None)
        if profile is None:
            raise ValueError(f"{symbol}: missing profile {PROFILE}.")

        for window in profile[GEOMETRY]["windows"]:
            source_candidate = candidate_from_dict(window["candidate"])
            v = values(source_candidate)
            if not all(v[key] == expected for key, expected in FIXED.items()):
                continue
            if v["mean_reversion.window"] not in (5, 10):
                continue
            sig = fingerprint(source_candidate)
            cf_candidate = counterfactual(source_candidate)
            if parameter_diff(source_candidate, cf_candidate) != ["mean_reversion.window"]:
                raise ValueError("Counterfactual changes more than one parameter.")

            start = int(window["test_start_index"])
            end = int(window["test_end_index"])
            oos = candles[start:end]
            baseline = run_candidate(source_candidate, oos, symbol)
            for key, actual in (
                ("net_profit_eur", baseline["net_profit_eur"]),
                ("profit_factor", baseline["profit_factor"]),
                ("max_drawdown_percent", baseline["max_drawdown_percent"]),
            ):
                if not metric_equal(window[key], actual):
                    raise ValueError(f"{symbol} window {window['window_index']}: source replay mismatch for {key}.")
            if int(window["trade_count"]) != int(baseline["trade_count"]):
                raise ValueError(f"{symbol} window {window['window_index']}: source replay mismatch for trade_count.")

            cf = run_candidate(cf_candidate, oos, symbol)
            paired.append({
                "symbol": symbol,
                "window_index": int(window["window_index"]),
                "phase": window.get("phase"),
                "test_start_index": start,
                "test_end_index": end,
                "source_candidate_signature": sig,
                "source_window_value": values(source_candidate)["mean_reversion.window"],
                "counterfactual_window_value": values(cf_candidate)["mean_reversion.window"],
                "baseline": baseline,
                "counterfactual": cf,
                "baseline_primary": primary(baseline),
                "counterfactual_primary": primary(cf),
                "paired_delta_eur": float(cf["net_profit_eur"]) - float(baseline["net_profit_eur"]),
            })

    symbols = {x["symbol"] for x in paired}
    if len(paired) < 2 or not {"IWM", "QQQ"}.issubset(symbols):
        raise ValueError(
            f"Expected paired windows from both independent hypothesis assets; "
            f"found {len(paired)} pairs across {sorted(symbols)}."
        )

    formal_rows = [x for x in paired if x["symbol"] in FORMAL_ASSETS]
    holdout_rows = [x for x in paired if x["symbol"] not in FORMAL_ASSETS]
    if {x["symbol"] for x in formal_rows} != FORMAL_ASSETS:
        raise ValueError("Both predeclared formal hypothesis assets must be represented.")
    per_asset = {symbol: aggregate([x for x in formal_rows if x["symbol"] == symbol]) for symbol in sorted(FORMAL_ASSETS)}
    overall = aggregate(formal_rows)
    holdout_by_asset = {symbol: aggregate([x for x in holdout_rows if x["symbol"] == symbol]) for symbol in sorted({x["symbol"] for x in holdout_rows})}
    consistent = all(
        item["counterfactual_positive_rate"] > item["baseline_positive_rate"]
        and item["counterfactual_pf_pass_rate"] > item["baseline_pf_pass_rate"]
        for item in per_asset.values()
    )
    status = (
        "hypothesis_supported_on_paired_control"
        if consistent and overall["paired_delta_total_eur"] > 0
        else "hypothesis_not_supported_on_paired_control"
    )

    report = {
        "schema_version": 1,
        "diagnostic_type": "controlled_hypothesis_reexperiment",
        "source_run_id": SOURCE_RUN_ID,
        "reference_report_fingerprint": SOURCE_REPORT_FINGERPRINT,
        "replay_report_fingerprint": rolling["diagnostic_fingerprint"],
        "replay_run_id": "35766606233",
        "source_universe": SOURCE_UNIVERSE,
        "research_candle_count": RESEARCH_CANDLES,
        "formal_assets": sorted(FORMAL_ASSETS),
        "holdout_assets": sorted({x["symbol"] for x in paired if x["symbol"] not in FORMAL_ASSETS}),
        "selection_profile": PROFILE,
        "geometry": GEOMETRY,
        "hypothesis": {
            "parameter": "mean_reversion.window",
            "values": [5, 10],
            "fixed_parameters": FIXED,
            "selection_preserved": True,
            "oos_windows_preserved": True,
            "paired_counterfactual": True,
            "same_execution_model": True,
        },
        "source_data": {
            "dataset_fingerprints": DATA_FINGERPRINTS,
            "source_archive_verified": True,
            "new_data_downloads": False,
        },
        "summary": {"formal_overall": overall, "formal_by_asset": per_asset, "holdout_by_asset": holdout_by_asset, "paired_all_assets": aggregate(paired), "primary_metrics_improve_in_each_formal_asset": consistent, "status": status},
        "rows": sorted(paired, key=lambda x: (x["symbol"], x["window_index"])),
        "interpretation_scope": {
            "diagnostic_only": True,
            "no_selection_change": True,
            "no_parameter_space_change": True,
            "no_gate_change": True,
            "no_new_data_basis": True,
            "baseline_replayed_against_source_window_metrics": True,
            "counterfactual_changes_exactly_one_parameter": True,
            "oos_is_outcome_only": True,
            "not_causal": True,
            "not_a_global_parameter_recommendation": True,
            "formal_gates_not_recomputed_for_counterfactual": True,
        },
        "safety": SAFETY,
    }
    raw = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    report["analysis_fingerprint"] = hashlib.sha256(raw).hexdigest()

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "controlled_hypothesis_reexperiment.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    lines = [
        "# Controlled Hypothesis Re-Experiment",
        "",
        "Analysis-Fingerprint: " + report["analysis_fingerprint"],
        "Source-Run: " + SOURCE_RUN_ID,
        "Hypothesis: mean_reversion.window 10 <-> 5",
        "Profile/Geometrie: " + PROFILE + " / " + GEOMETRY,
        "Paired windows: " + str(len(paired)),
        "Status: " + status,
        "",
        "| Gruppe | Fenster | Baseline Profit | Counterfactual Profit | Delta | Baseline positiv | Counterfactual positiv | Baseline PF-Pass | Counterfactual PF-Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, item in [("Formal Gesamt", overall), *per_asset.items(), *[(f"Hold-out {k}", v) for k, v in holdout_by_asset.items()]]:
        lines.append(
            f"| {name} | {item['window_count']} | {item['baseline_total_profit_eur']:.3f} | "
            f"{item['counterfactual_total_profit_eur']:.3f} | {item['paired_delta_total_eur']:.3f} | "
            f"{item['baseline_positive_rate']:.3f} | {item['counterfactual_positive_rate']:.3f} | "
            f"{item['baseline_pf_pass_rate']:.3f} | {item['counterfactual_pf_pass_rate']:.3f} |"
        )
    lines += [
        "",
        "Paarweises Gegenexperiment auf unveränderten OOS-Fenstern; ausschließlich mean_reversion.window wird verändert.",
        "Kein Selection-, Parameterraum- oder Gate-Eingriff.",
        "Paper-Only: True; Live-Trading: False; Orders: False.",
    ]
    (output / "controlled_hypothesis_reexperiment.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rolling-json", required=True)
    parser.add_argument("--manifest-json", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", default="research/controlled_hypothesis_reexperiment")
    args = parser.parse_args()
    report = run_experiment(args.rolling_json, args.manifest_json, args.data_dir, args.output_dir)
    print("CONTROLLED_HYPOTHESIS_REEXPERIMENT: COMPLETED")
    print("STATUS:", report["summary"]["status"])
    print("PAIRED_WINDOWS_FORMAL:", report["summary"]["formal_overall"]["window_count"])
    print("PAIRED_WINDOWS_ALL_MATCHING:", len(report["rows"]))
    print("PAIRED_DELTA_EUR_FORMAL:", report["summary"]["formal_overall"]["paired_delta_total_eur"])
    print("ANALYSIS_FINGERPRINT:", report["analysis_fingerprint"])
    print("PAPER_ONLY:", report["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", report["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
