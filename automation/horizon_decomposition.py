"""Controlled 2x2 horizon decomposition for benchmark research.

Outer split controls:
- short training: candles [2250:4500]
- long training: candles [0:4500]
- holdout 250: candles [4500:4750]
- holdout 500: candles [4500:5000]

Both training conditions end at the same index and both holdouts start at
the same index. Holdout size is therefore isolated from candidate selection.
This is a new causal-decomposition control, not a replay of the historical
2,500-candle report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

from automation.backtest_runner import _rolling_window_sizes, _run_candidate
from automation.prepare_research_data import prepare
from automation.research_run import parameter_space_identity
from backtesting.engine import BacktestEngine
from config import settings
from config.parameter_space import ParameterSpace
from optimization.optimizer import Optimizer
from optimization.selection_profiles import available_selection_profile_names
from research.protocol import dataset_fingerprint
from validation.research_gates import (
    ResearchGateConfig,
    check_backtest,
    check_data_quality,
    check_holdout,
    check_overfit,
    check_robustness,
    check_rolling_walk_forward,
    check_walk_forward,
)
from validation.rolling_walk_forward import RollingWalkForwardValidator
from validation.walk_forward import WalkForwardValidator


SCHEMA_VERSION = 1
TARGET_COUNT = 5000
SHORT_TRAIN_START = 2250
RESEARCH_END = 4500
HOLDOUT_START = 4500
SHORT_HOLDOUT_END = 4750
LONG_HOLDOUT_END = 5000

TRAINING_CONDITIONS = {
    "short_2250": (SHORT_TRAIN_START, RESEARCH_END),
    "long_4500": (0, RESEARCH_END),
}
HOLDOUT_CONDITIONS = {
    "holdout_250": (HOLDOUT_START, SHORT_HOLDOUT_END),
    "holdout_500": (HOLDOUT_START, LONG_HOLDOUT_END),
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fingerprint(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("diagnostic_fingerprint", None)
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()


def _safe(value: Any) -> Any:
    if isinstance(value, float):
        if value == float("inf"):
            return "inf"
        if value != value:
            return None
    return value


def _candidate(candidate) -> dict[str, Any]:
    return {
        "risk_per_trade": candidate.risk_per_trade,
        "leverage": candidate.leverage,
        "strategy": asdict(candidate.strategy),
    }


def _metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: _safe(v) for k, v in metrics.items()}


def _failed_criteria(gate: dict[str, Any]) -> list[str]:
    if gate.get("passed"):
        return []
    d = gate.get("details", {})
    if not isinstance(d, dict):
        return ["unclassified_failure"]
    n = gate.get("name")
    out: list[str] = []

    if n == "data_quality":
        if d.get("error"):
            out.append("data_validation_error")
        if d.get("candle_count", 0) < d.get("minimum_candles", 0):
            out.append("insufficient_candles")
    elif n == "backtest":
        if d.get("metrics_valid") is False:
            out.append("invalid_metrics")
        if d.get("trade_count", 0) < d.get("minimum_trades", 0):
            out.append("insufficient_trades")
        if d.get("final_capital_eur", 0) <= 0:
            out.append("nonpositive_final_capital")
        if d.get("max_drawdown_percent", 0) > d.get("maximum_drawdown_percent", 10):
            out.append("drawdown_limit")
    elif n == "walk_forward":
        if d.get("metrics_valid") is False:
            out.append("invalid_metrics")
        if d.get("oos_trade_count", 0) < d.get("minimum_oos_trades", 0):
            out.append("insufficient_oos_trades")
        if d.get("oos_net_profit_eur", 0) <= 0:
            out.append("nonpositive_oos_profit")
        pf = d.get("profit_factor")
        if pf != "inf" and isinstance(pf, (int, float)) and pf < d.get("minimum_profit_factor", 1.1):
            out.append("profit_factor")
        if d.get("oos_max_drawdown_percent", 0) > d.get("maximum_drawdown_percent", 10):
            out.append("drawdown_limit")
    elif n == "rolling_walk_forward":
        if d.get("window_count", 0) <= 0:
            out.append("no_windows")
        if d.get("total_trade_count", 0) < d.get("minimum_total_trades", 30):
            out.append("insufficient_total_trades")
        if d.get("total_net_profit_eur", 0) <= 0:
            out.append("nonpositive_total_profit")
        pf = d.get("overall_profit_factor")
        if pf != "inf" and isinstance(pf, (int, float)) and pf < d.get("minimum_profit_factor", 1.1):
            out.append("profit_factor")
        if d.get("profitable_window_ratio", 0) < d.get("minimum_profitable_window_ratio", 0.5):
            out.append("profitable_window_ratio")
        if d.get("zero_trade_window_ratio", 1) > d.get("maximum_zero_trade_window_ratio", 0.25):
            out.append("zero_trade_window_ratio")
        if d.get("average_drawdown_percent", 0) > d.get("maximum_drawdown_percent", 10):
            out.append("drawdown_limit")
    elif n == "robustness":
        if d.get("variant_count", 0) < d.get("minimum_variants", 4):
            out.append("insufficient_variants")
        if d.get("profitable_variant_ratio", 0) < d.get("minimum_profitable_variant_ratio", 0.5):
            out.append("profitable_variant_ratio")
        if isinstance(d.get("stressed_net_profit_eur"), (int, float)) and d["stressed_net_profit_eur"] < 0:
            out.append("stress_cost_failure")
    elif n == "overfit":
        if d.get("train_return_percent", 0) <= 0:
            out.append("nonpositive_is_return")
        if d.get("oos_to_is_return_ratio", 0) < d.get("minimum_oos_to_is_return_ratio", 0.25):
            out.append("oos_to_is_ratio")
    elif n == "holdout":
        if d.get("trade_count", 0) < d.get("minimum_holdout_trades", 10):
            out.append("insufficient_holdout_trades")
        if d.get("net_profit_eur", 0) <= 0:
            out.append("nonpositive_holdout_profit")
        pf = d.get("profit_factor")
        if pf != "inf" and isinstance(pf, (int, float)) and pf < d.get("minimum_profit_factor", 1.1):
            out.append("profit_factor")
        if d.get("max_drawdown_percent", 0) > d.get("maximum_drawdown_percent", 10):
            out.append("drawdown_limit")

    return out or ["unclassified_failure"]


def _gate(gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": gate["name"],
        "scope": gate["scope"],
        "passed": bool(gate["passed"]),
        "details": _metrics(gate["details"]),
        "failed_criteria": _failed_criteria(gate),
    }


def _run_training(
    candles,
    symbol: str,
    profile: str,
    train_start: int,
    train_end: int,
    *,
    parameter_space: ParameterSpace,
    gate_config: ResearchGateConfig,
) -> dict[str, Any]:
    research = tuple(candles[train_start:train_end])
    baseline = BacktestEngine(
        fee_rate=gate_config.fee_rate,
        slippage_rate=gate_config.slippage_rate,
    ).run(symbol=symbol, candles=research)

    optimizer = Optimizer(candles=research, symbol=symbol, parameter_space=parameter_space)
    top = optimizer.optimize(top_n=1, selection_profile=profile)
    if not top:
        raise ValueError("Optimizer lieferte keinen Kandidaten.")
    optimized_candidate = top[0].candidate

    wfo = WalkForwardValidator(
        candles=research,
        symbol=symbol,
        parameter_space=parameter_space,
        train_ratio=0.7,
        selection_profile=profile,
    ).validate()

    # Full-research optimizer and WFO-selected candidate intentionally
    # use different training scopes; only the WFO candidate is used for the
    # formal downstream gates, matching the existing research pipeline.

    train_size, test_size, step_size = _rolling_window_sizes(
        len(research), train_ratio=0.5, test_ratio=0.1, step_ratio=0.1
    )
    rolling_validator = RollingWalkForwardValidator(
        candles=research,
        symbol=symbol,
        parameter_space=parameter_space,
        train_size=train_size,
        test_size=test_size,
        step_size=step_size,
        minimum_trades_required=gate_config.minimum_rolling_trades,
        selection_profile=profile,
    )
    rolling_results = rolling_validator.validate()
    rolling_summary = rolling_validator.summarize(rolling_results)

    wfo_test = research[wfo.train_candles:wfo.train_candles + wfo.test_candles]
    robustness = check_robustness(
        wfo.selected_candidate,
        wfo_test,
        symbol,
        gate_config,
        fee_rate=gate_config.fee_rate,
        slippage_rate=gate_config.slippage_rate,
    )
    train_result = _run_candidate(
        wfo.selected_candidate,
        research[:wfo.train_candles],
        symbol,
        fee_rate=gate_config.fee_rate,
        slippage_rate=gate_config.slippage_rate,
    )

    gates = [
        check_data_quality(candles, gate_config),
        check_backtest(baseline.metrics, gate_config),
        check_walk_forward(asdict(wfo), gate_config),
        check_rolling_walk_forward(asdict(rolling_summary), gate_config),
        robustness,
        check_overfit(train_result.metrics, asdict(wfo), gate_config),
    ]

    return {
        "training_condition": "short_2250" if train_start else "long_4500",
        "research_slice": [train_start, train_end],
        "research_candle_count": len(research),
        "research_start": research[0].timestamp.isoformat(),
        "research_end": research[-1].timestamp.isoformat(),
        "research_fingerprint": dataset_fingerprint(research),
        "selected_candidate": _candidate(wfo.selected_candidate),
        "wfo": _metrics(asdict(wfo)),
        "rolling_summary": _metrics(asdict(rolling_summary)),
        "gates": {g["name"]: _gate(g) for g in gates},
    }


def _run_holdout(
    candles,
    symbol: str,
    training: dict[str, Any],
    holdout_name: str,
    holdout_start: int,
    holdout_end: int,
    *,
    gate_config: ResearchGateConfig,
) -> dict[str, Any]:
    from validation.research_gates import _candidate_from_dict

    holdout = tuple(candles[holdout_start:holdout_end])
    candidate = _candidate_from_dict(training["selected_candidate"])
    result = _run_candidate(
        candidate,
        holdout,
        symbol,
        fee_rate=gate_config.fee_rate,
        slippage_rate=gate_config.slippage_rate,
    )
    gate = check_holdout(result.metrics, gate_config)
    return {
        "holdout_condition": holdout_name,
        "slice": [holdout_start, holdout_end],
        "candle_count": len(holdout),
        "start": holdout[0].timestamp.isoformat(),
        "end": holdout[-1].timestamp.isoformat(),
        "fingerprint": dataset_fingerprint(holdout),
        "metrics": _metrics(result.metrics),
        "gate": _gate(gate),
    }


def _factorial_summary(cells: list[dict[str, Any]]) -> dict[str, Any]:
    names = sorted({n for row in cells for n in row["all_gates"]})
    out: dict[str, Any] = {}
    for gate in names:
        rates: dict[str, float] = {}
        for train in TRAINING_CONDITIONS:
            for holdout in HOLDOUT_CONDITIONS:
                rows = [r for r in cells if r["training_condition"] == train and r["holdout_condition"] == holdout]
                rates[f"{train}|{holdout}"] = sum(r["all_gates"][gate]["passed"] for r in rows) / len(rows)

        training_effect = (
            (rates["long_4500|holdout_250"] + rates["long_4500|holdout_500"]) / 2
            - (rates["short_2250|holdout_250"] + rates["short_2250|holdout_500"]) / 2
        )
        holdout_effect = (
            (rates["short_2250|holdout_500"] + rates["long_4500|holdout_500"]) / 2
            - (rates["short_2250|holdout_250"] + rates["long_4500|holdout_250"]) / 2
        )
        interaction = (
            rates["long_4500|holdout_500"]
            - rates["long_4500|holdout_250"]
            - rates["short_2250|holdout_500"]
            + rates["short_2250|holdout_250"]
        )
        out[gate] = {
            "cells": {
                key: {
                    "pass_rate": value,
                    "passed_count": sum(
                        r["all_gates"][gate]["passed"]
                        for r in cells
                        if f"{r['training_condition']}|{r['holdout_condition']}" == key
                    ),
                    "evaluation_count": sum(
                        1 for r in cells
                        if f"{r['training_condition']}|{r['holdout_condition']}" == key
                    ),
                }
                for key, value in rates.items()
            },
            "training_history_main_effect_pass_rate": training_effect,
            "holdout_size_main_effect_pass_rate": holdout_effect,
            "training_holdout_interaction": interaction,
        }
    return out


def _assert_contract(cells: list[dict[str, Any]]) -> None:
    grouped = defaultdict(set)
    for row in cells:
        grouped[(row["symbol"], row["selection_profile"], row["training_condition"])].add(
            _canonical(row["selected_candidate"])
        )
    for key, candidates in grouped.items():
        if len(candidates) != 1:
            raise RuntimeError(f"Holdout-Größe verändert Kandidatenauswahl: {key}")
    for row in cells:
        if row["holdout_start_index"] != HOLDOUT_START:
            raise RuntimeError("Holdout-Start ist nicht kontrolliert.")
        if row["research_end_index"] != RESEARCH_END:
            raise RuntimeError("Research-Endpunkt ist nicht kontrolliert.")


def run_decomposition(
    universe: str = "benchmark",
    target_count: int = TARGET_COUNT,
    output_dir: str = "research/horizon_decomposition",
) -> dict[str, Any]:
    if universe != "benchmark":
        raise ValueError("Nur benchmark ist fuer diese Dekomposition zulaessig.")
    output = Path(output_dir)
    manifest, _ = prepare(
        target_count=target_count,
        output_path=output / "data_manifest.json",
        universe=universe,
        minimum_count=target_count,
    )

    from data.market_store import MarketDataStore

    store = MarketDataStore()
    parameter_space = ParameterSpace()
    gate_config = ResearchGateConfig()
    profiles = available_selection_profile_names()
    datasets = []
    for item in manifest["datasets"]:
        candles = tuple(store.load(item["symbol"], item["interval"]))
        if len(candles) != target_count:
            raise RuntimeError(f"{item['symbol']}: {len(candles)} statt {target_count} Candles.")
        datasets.append((item["symbol"], item["interval"], candles, item))

    training_runs: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    for symbol, interval, candles, manifest_item in datasets:
        for profile in profiles:
            by_training = {}
            for train_name, (start, end) in TRAINING_CONDITIONS.items():
                run = _run_training(
                    candles, symbol, profile, start, end,
                    parameter_space=parameter_space, gate_config=gate_config,
                )
                by_training[train_name] = run
                training_runs.append({
                    "symbol": symbol,
                    "interval": interval,
                    "selection_profile": profile,
                    **run,
                })
            for train_name, training in by_training.items():
                for holdout_name, (start, end) in HOLDOUT_CONDITIONS.items():
                    holdout = _run_holdout(
                        candles, symbol, training, holdout_name, start, end,
                        gate_config=gate_config,
                    )
                    all_gates = dict(training["gates"])
                    all_gates["holdout"] = holdout["gate"]
                    cells.append({
                        "symbol": symbol,
                        "interval": interval,
                        "selection_profile": profile,
                        "training_condition": train_name,
                        "holdout_condition": holdout_name,
                        "research_start_index": training["research_slice"][0],
                        "research_end_index": training["research_slice"][1],
                        "holdout_start_index": start,
                        "holdout_end_index": end,
                        "selected_candidate": training["selected_candidate"],
                        "wfo": training["wfo"],
                        "rolling_summary": training["rolling_summary"],
                        "holdout": holdout,
                        "all_gates": all_gates,
                    })

    _assert_contract(cells)

    candidate_changes = []
    for symbol, interval, candles, _ in datasets:
        for profile in profiles:
            short = next(r for r in training_runs if r["symbol"] == symbol and r["selection_profile"] == profile and r["training_condition"] == "short_2250")
            long = next(r for r in training_runs if r["symbol"] == symbol and r["selection_profile"] == profile and r["training_condition"] == "long_4500")
            candidate_changes.append({
                "symbol": symbol,
                "selection_profile": profile,
                "same_candidate": short["selected_candidate"] == long["selected_candidate"],
                "short_candidate": short["selected_candidate"],
                "long_candidate": long["selected_candidate"],
            })

    failures = defaultdict(lambda: defaultdict(int))
    for row in cells:
        for gate in row["all_gates"].values():
            if not gate["passed"]:
                for criterion in gate["failed_criteria"]:
                    failures[gate["name"]][criterion] += 1

    report = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_type": "horizon_decomposition_2x2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "universe": universe,
        "target_count": target_count,
        "dataset_manifest": manifest,
        "parameter_space": parameter_space_identity(parameter_space),
        "selection_profiles": list(profiles),
        "design": {
            "training": {
                "short_2250": [SHORT_TRAIN_START, RESEARCH_END],
                "long_4500": [0, RESEARCH_END],
            },
            "holdout": {
                "holdout_250": [HOLDOUT_START, SHORT_HOLDOUT_END],
                "holdout_500": [HOLDOUT_START, LONG_HOLDOUT_END],
            },
            "same_research_endpoint": True,
            "same_holdout_start": True,
            "holdout_excluded_from_candidate_selection": True,
            "no_strategy_changes": True,
            "no_parameter_space_changes": True,
            "no_gate_changes": True,
        },
        "dataset_fingerprints": {
            item["symbol"]: {
                "full": item["fingerprint"],
                "research_short": dataset_fingerprint(
                    tuple(store.load(item["symbol"], item["interval"]))[SHORT_TRAIN_START:RESEARCH_END]
                ),
                "research_long": dataset_fingerprint(
                    tuple(store.load(item["symbol"], item["interval"]))[:RESEARCH_END]
                ),
                "holdout_250": dataset_fingerprint(
                    tuple(store.load(item["symbol"], item["interval"]))[HOLDOUT_START:SHORT_HOLDOUT_END]
                ),
                "holdout_500": dataset_fingerprint(
                    tuple(store.load(item["symbol"], item["interval"]))[HOLDOUT_START:LONG_HOLDOUT_END]
                ),
            }
            for item in manifest["datasets"]
        },
        "training_runs": training_runs,
        "cells": cells,
        "candidate_training_changes": candidate_changes,
        "factorial_summary": _factorial_summary(cells),
        "failure_criteria_counts": {
            gate: dict(sorted(criteria.items()))
            for gate, criteria in sorted(failures.items())
        },
        "interpretation_scope": {
            "diagnostic_only": True,
            "historical_2500_report_replayed": False,
            "training_history_effect": "short_2250 versus long_4500 with common endpoint",
            "holdout_effect": "250 versus 500 with common start",
            "inner_wfo_window_geometry_changes_with_research_length": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    report["diagnostic_fingerprint"] = _fingerprint(report)
    output.mkdir(parents=True, exist_ok=True)
    (output / "horizon_decomposition.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    _write_summary_markdown(report, output / "horizon_decomposition.md")
    return report


def _write_summary_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Horizon-Decomposition — Benchmark 2x2 Control",
        "",
        "Diagnostic-only control. No strategy, parameter-space or gate changes.",
        "",
        "| Gate | Training effect | Holdout effect | Interaction |",
        "| --- | ---: | ---: | ---: |",
    ]
    for gate, item in report["factorial_summary"].items():
        lines.append(
            f"| {gate} | {item['training_history_main_effect_pass_rate']:+.3f} | "
            f"{item['holdout_size_main_effect_pass_rate']:+.3f} | "
            f"{item['training_holdout_interaction']:+.3f} |"
        )
    lines += ["", "## Failure criteria", "", "| Gate | Criterion | Count |", "| --- | --- | ---: |"]
    for gate, criteria in report["failure_criteria_counts"].items():
        for criterion, count in criteria.items():
            lines.append(f"| {gate} | {criterion} | {count} |")
    lines += [
        "",
        f"Diagnostic fingerprint: {report['diagnostic_fingerprint']}",
        "Paper-only: True; live trading: False; orders: False.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", default="benchmark")
    parser.add_argument("--target-count", type=int, default=TARGET_COUNT)
    parser.add_argument("--output-dir", default="research/horizon_decomposition")
    args = parser.parse_args()
    report = run_decomposition(
        universe=args.universe,
        target_count=args.target_count,
        output_dir=args.output_dir,
    )
    print("HORIZON_DECOMPOSITION: COMPLETED")
    print("DIAGNOSTIC_FINGERPRINT:", report["diagnostic_fingerprint"])
    print("CELLS:", report["cells"] and len(report["cells"]))
    print("TRAINING_RUNS:", len(report["training_runs"]))
    print("PAPER_ONLY:", report["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", report["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
