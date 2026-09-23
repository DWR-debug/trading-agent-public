"""Rolling-WF geometry and time-phase control on a common benchmark research span."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

from automation.horizon_decomposition import _candidate, _failed_criteria
from automation.prepare_research_data import prepare
from automation.research_run import parameter_space_identity
from config import settings
from config.parameter_space import ParameterSpace
from data.market_store import MarketDataStore
from optimization.selection_profiles import available_selection_profile_names
from research.protocol import dataset_fingerprint
from validation.research_gates import ResearchGateConfig, check_rolling_walk_forward
from validation.rolling_walk_forward import RollingWalkForwardValidator

TARGET_COUNT = 5000
RESEARCH_END = 4500
SMALL_TRAIN = 1125
SMALL_TEST = 225
SMALL_STEP = 225

LARGE_TRAIN = 2250
LARGE_TEST = 450
LARGE_STEP = 450

SMALL = (SMALL_TRAIN, SMALL_TEST, SMALL_STEP)
LARGE = (LARGE_TRAIN, LARGE_TEST, LARGE_STEP)


def _safe(v: Any) -> Any:
    if isinstance(v, float):
        if v == float("inf"):
            return "inf"
        if v != v:
            return None
    return v


def _json_safe(v: Any) -> Any:
    if isinstance(v, dict):
        return {k: _json_safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_json_safe(x) for x in v]
    return _safe(v)


def _candidate_fp(candidate: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _gate_record(gate: dict[str, Any]) -> dict[str, Any]:
    record = {
        "name": gate["name"],
        "scope": gate["scope"],
        "passed": bool(gate["passed"]),
        "details": _json_safe(gate["details"]),
    }
    record["failed_criteria"] = _failed_criteria(record)
    return record


def _window_record(result, research, train_size, test_size, step_size):
    start = (result.window_index - 1) * step_size
    train_end = start + train_size
    test_start = train_end
    test_end = test_start + test_size
    candidate = _candidate(result.selected_candidate)
    return {
        "window_index": result.window_index,
        "train_size": train_size,
        "test_size": test_size,
        "step_size": step_size,
        "train_start_index": start,
        "train_end_index": train_end,
        "test_start_index": test_start,
        "test_end_index": test_end,
        "test_start": research[test_start].timestamp.isoformat(),
        "test_end": research[test_end - 1].timestamp.isoformat(),
        "candidate": candidate,
        "candidate_fingerprint": _candidate_fp(candidate),
        "selection": {
            "profile_rank": result.selection_rank,
            "candidate_count": result.selection_candidate_count,
            "score": _safe(result.selection_score),
            "runner_up_score_gap": _safe(
                result.selection_runner_up_score_gap
            ),
            "raw_score_rank": result.raw_score_rank,
            "selected_vs_best_raw_score_gap": _safe(
                result.selected_vs_best_raw_score_gap
            ),
        },
        "training": {
            "net_profit_eur": _safe(result.training_net_profit_eur),
            "return_percent": _safe(result.training_return_percent),
            "win_rate_percent": _safe(result.training_win_rate_percent),
            "profit_factor": _safe(result.training_profit_factor),
            "max_drawdown_percent": _safe(
                result.training_max_drawdown_percent
            ),
            "sharpe_ratio": _safe(result.training_sharpe_ratio),
            "trade_count": result.training_trade_count,
            "average_trade_eur": _safe(result.training_average_trade_eur),
        },
        "net_profit_eur": _safe(result.test_net_profit_eur),
        "return_percent": _safe(result.test_return_percent),
        "win_rate_percent": _safe(result.test_win_rate_percent),
        "profit_factor": _safe(result.test_profit_factor),
        "max_drawdown_percent": _safe(result.test_max_drawdown_percent),
        "sharpe_ratio": _safe(result.test_sharpe_ratio),
        "trade_count": result.test_trade_count,
        "average_trade_eur": _safe(result.test_average_trade_eur),
    }


def _run_geometry(research, symbol, profile, name, geometry, gate_config, parameter_space):
    train_size, test_size, step_size = geometry
    validator = RollingWalkForwardValidator(
        candles=research,
        symbol=symbol,
        parameter_space=parameter_space,
        train_size=train_size,
        test_size=test_size,
        step_size=step_size,
        minimum_trades_required=gate_config.minimum_rolling_trades,
        selection_profile=profile,
    )
    results = validator.validate()
    summary = validator.summarize(results)
    windows = [
        _window_record(r, research, train_size, test_size, step_size)
        for r in results
    ]
    gate = check_rolling_walk_forward(asdict(summary), gate_config)
    return {
        "geometry": name,
        "train_size": train_size,
        "test_size": test_size,
        "step_size": step_size,
        "window_count": len(windows),
        "summary": _json_safe(asdict(summary)),
        "gate": _gate_record(gate),
        "windows": windows,
    }


def _phase(windows, lo, hi):
    rows = [w for w in windows if lo <= w["window_index"] <= hi]
    profits = [w["net_profit_eur"] for w in rows if isinstance(w["net_profit_eur"], (int, float))]
    return {
        "window_count": len(rows),
        "profitable_windows": sum(p > 0 for p in profits),
        "profitable_window_ratio": sum(p > 0 for p in profits) / len(profits) if profits else 0.0,
        "total_net_profit_eur": sum(profits),
        "median_window_profit_eur": median(profits) if profits else None,
        "mean_window_profit_eur": mean(profits) if profits else None,
        "total_trade_count": sum(w["trade_count"] for w in rows),
    }


def _persistence(windows):
    rows = sorted(windows, key=lambda w: w["window_index"])
    same = [
        a["candidate_fingerprint"] == b["candidate_fingerprint"]
        for a, b in zip(rows, rows[1:])
    ]
    return {
        "adjacent_pairs": len(same),
        "adjacent_same_candidate": sum(same),
        "adjacent_same_candidate_ratio": sum(same) / len(same) if same else 0.0,
        "unique_candidates": len({w["candidate_fingerprint"] for w in rows}),
    }


def _common_blocks(small, large):
    sm = {w["window_index"]: w for w in small["windows"]}
    lg = {w["window_index"]: w for w in large["windows"]}
    out = []
    for i in range(1, 6):
        a = sm[2 * i + 4]
        b = sm[2 * i + 5]
        c = lg[i]
        if a["test_start_index"] != c["test_start_index"] or b["test_end_index"] != c["test_end_index"]:
            raise RuntimeError(f"Nicht identischer Testblock für Large-Fenster {i}.")
        small_profit = float(a["net_profit_eur"]) + float(b["net_profit_eur"])
        out.append({
            "large_window_index": i,
            "small_window_indices": [a["window_index"], b["window_index"]],
            "test_start_index": c["test_start_index"],
            "test_end_index": c["test_end_index"],
            "large_net_profit_eur": c["net_profit_eur"],
            "small_pair_net_profit_eur": small_profit,
            "geometry_profit_difference_eur": float(c["net_profit_eur"]) - small_profit,
            "large_candidate_fingerprint": c["candidate_fingerprint"],
            "small_candidate_fingerprints": [a["candidate_fingerprint"], b["candidate_fingerprint"]],
            "large_matches_small_candidate": c["candidate_fingerprint"] in {
                a["candidate_fingerprint"], b["candidate_fingerprint"]
            },
            "small_pair_same_candidate": a["candidate_fingerprint"] == b["candidate_fingerprint"],
        })
    return out


def run_control(universe="benchmark", target_count=TARGET_COUNT, output_dir="research/rolling_geometry_control"):
    if universe != "benchmark":
        raise ValueError("Nur benchmark ist zulässig.")
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only-Sicherheitsvertrag verletzt.")

    output = Path(output_dir)
    manifest, _ = prepare(
        target_count=target_count,
        output_path=output / "data_manifest.json",
        universe=universe,
        minimum_count=target_count,
    )
    store = MarketDataStore()
    parameter_space = ParameterSpace()
    gate_config = ResearchGateConfig()
    profiles = available_selection_profile_names()

    datasets = []
    all_runs = []
    positions = defaultdict(list)

    for item in manifest["datasets"]:
        candles = tuple(store.load(item["symbol"], item["interval"]))
        if len(candles) != target_count:
            raise RuntimeError(f"{item['symbol']}: unerwartete Candle-Anzahl.")
        research = candles[:RESEARCH_END]
        if len(research) != RESEARCH_END:
            raise RuntimeError("Research-Slice ist nicht 4.500 Candles lang.")

        profile_rows = []
        for profile in profiles:
            small = _run_geometry(
                research, item["symbol"], profile, "small_1125_225",
                SMALL, gate_config, parameter_space
            )
            large = _run_geometry(
                research, item["symbol"], profile, "large_2250_450",
                LARGE, gate_config, parameter_space
            )
            all_runs.extend([small, large])
            for geometry, run in [("small_1125_225", small), ("large_2250_450", large)]:
                for w in run["windows"]:
                    positions[geometry].append({
                        **w,
                        "symbol": item["symbol"],
                        "selection_profile": profile,
                    })
            profile_rows.append({
                "selection_profile": profile,
                "small": small,
                "large": large,
                "small_phases": {
                    "early_1_5": _phase(small["windows"], 1, 5),
                    "middle_6_10": _phase(small["windows"], 6, 10),
                    "recent_11_15": _phase(small["windows"], 11, 15),
                },
                "small_candidate_persistence": _persistence(small["windows"]),
                "large_candidate_persistence": _persistence(large["windows"]),
                "common_test_blocks": _common_blocks(small, large),
            })
        datasets.append({
            "symbol": item["symbol"],
            "interval": item["interval"],
            "full_data_fingerprint": item["fingerprint"],
            "research_fingerprint": dataset_fingerprint(research),
            "research_start": research[0].timestamp.isoformat(),
            "research_end": research[-1].timestamp.isoformat(),
            "profiles": profile_rows,
        })

    geometry_summary = {}
    for name in ("small_1125_225", "large_2250_450"):
        runs = [r for r in all_runs if r["geometry"] == name]
        geometry_summary[name] = {
            "evaluation_count": len(runs),
            "passed_gate_count": sum(r["gate"]["passed"] for r in runs),
            "pass_rate": sum(r["gate"]["passed"] for r in runs) / len(runs),
        }

    position_summary = {}
    for name, rows in positions.items():
        count = 15 if name == "small_1125_225" else 5
        position_summary[name] = [
            {
                "window_index": i,
                "evaluation_count": sum(r["window_index"] == i for r in rows),
                "profitable_windows": sum(
                    r["window_index"] == i and r["net_profit_eur"] > 0
                    for r in rows
                ),
                "profitable_window_ratio": (
                    sum(
                        r["window_index"] == i and r["net_profit_eur"] > 0
                        for r in rows
                    ) / sum(r["window_index"] == i for r in rows)
                ),
                "median_net_profit_eur": median([
                    r["net_profit_eur"] for r in rows
                    if r["window_index"] == i
                ]),
            }
            for i in range(1, count + 1)
        ]

    phase_summary = {}
    for name, lo, hi in [
        ("early_1_5", 1, 5),
        ("middle_6_10", 6, 10),
        ("recent_11_15", 11, 15),
    ]:
        phase_summary[name] = _phase(positions["small_1125_225"], lo, hi)

    failures = defaultdict(Counter)
    for run in all_runs:
        if not run["gate"]["passed"]:
            for criterion in run["gate"]["failed_criteria"]:
                failures[run["geometry"]][criterion] += 1

    persistence = {
        f"{d['symbol']}|{p['selection_profile']}": {
            "small": p["small_candidate_persistence"],
            "large": p["large_candidate_persistence"],
        }
        for d in datasets
        for p in d["profiles"]
    }

    common_blocks = [
        block
        for d in datasets
        for p in d["profiles"]
        for block in p["common_test_blocks"]
    ]

    report = {
        "schema_version": 1,
        "diagnostic_type": "rolling_geometry_time_phase_control",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "universe": universe,
        "target_count": target_count,
        "research_candle_count": RESEARCH_END,
        "parameter_space": parameter_space_identity(parameter_space),
        "selection_profiles": list(profiles),
        "design": {
            "small_geometry": {"train_size": SMALL[0], "test_size": SMALL[1], "step_size": SMALL[2], "window_count": 15},
            "large_geometry": {"train_size": LARGE[0], "test_size": LARGE[1], "step_size": LARGE[2], "window_count": 5},
            "common_test_span": [2250, 4500],
            "small_common_window_indices": list(range(6, 16)),
            "holdout_used": False,
            "no_strategy_changes": True,
            "no_parameter_space_changes": True,
            "no_gate_changes": True,
        },
        "dataset_manifest": manifest,
        "datasets": datasets,
        "geometry_summary": geometry_summary,
        "position_summary": position_summary,
        "phase_summary": phase_summary,
        "failure_criteria_counts": {
            k: dict(sorted(v.items())) for k, v in sorted(failures.items())
        },
        "candidate_persistence": persistence,
        "common_test_block_count": len(common_blocks),
        "common_test_block_profit_comparisons": common_blocks,
        "interpretation_scope": {
            "diagnostic_only": True,
            "same_research_span": True,
            "same_common_test_span_for_geometry_comparison": True,
            "geometry_difference_includes_training_window_size": True,
            "small_geometry_phase_analysis": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    report["diagnostic_fingerprint"] = hashlib.sha256(
        json.dumps(
            {k: v for k, v in report.items() if k != "diagnostic_fingerprint"},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()

    output.mkdir(parents=True, exist_ok=True)
    (output / "rolling_geometry_control.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    _write_markdown(report, output / "rolling_geometry_control.md")
    return report


def _write_markdown(report, path):
    lines = [
        "# Rolling-WF Geometry- und Zeitphasen-Control",
        "",
        f"Diagnostic-Fingerprint: {report['diagnostic_fingerprint']}",
        f"Code-Version: {report['code_version']}",
        "",
        "| Geometrie | Training | Test | Step | Fenster | Bestanden | Passrate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, item in report["geometry_summary"].items():
        cfg = report["design"]["small_geometry" if name.startswith("small") else "large_geometry"]
        lines.append(
            f"| {name} | {cfg['train_size']} | {cfg['test_size']} | "
            f"{cfg['step_size']} | {cfg['window_count']} | "
            f"{item['passed_gate_count']}/{item['evaluation_count']} | "
            f"{item['pass_rate']:.3f} |"
        )
    lines += [
        "",
        "| Phase | Fenster | profitable Fenster | Quote | Gesamtprofit EUR |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, item in report["phase_summary"].items():
        lines.append(
            f"| {name} | {item['window_count']} | {item['profitable_windows']} | "
            f"{item['profitable_window_ratio']:.3f} | "
            f"{item['total_net_profit_eur']:.2f} |"
        )
    lines += ["", "## Failure-Kriterien", "", "| Geometrie | Kriterium | Anzahl |", "| --- | --- | ---: |"]
    for geometry, criteria in report["failure_criteria_counts"].items():
        for criterion, count in criteria.items():
            lines.append(f"| {geometry} | {criterion} | {count} |")
    lines += [
        "",
        "Die Analyse ist diagnostisch. Geometrieunterschiede umfassen Trainingsfenstergröße, Testfenstergröße und daraus resultierende Kandidatenauswahl.",
        "Paper-Only: True; Live-Trading: False; Orders: False.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", default="benchmark")
    parser.add_argument("--target-count", type=int, default=TARGET_COUNT)
    parser.add_argument("--output-dir", default="research/rolling_geometry_control")
    args = parser.parse_args()
    report = run_control(args.universe, args.target_count, args.output_dir)
    print("ROLLING_GEOMETRY_CONTROL: COMPLETED")
    print("DIAGNOSTIC_FINGERPRINT:", report["diagnostic_fingerprint"])
    print("PAPER_ONLY:", report["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", report["safety"]["live_trading_enabled"])


if __name__ == "__main__":
    main()
