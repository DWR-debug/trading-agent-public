"""Reproducible time-phase and asset-universe diagnostics for Research reports.

Consumes existing fingerprint-verified Research reports only. No Research
re-execution, gate changes, candidate selection, or parameter-space changes.
Rolling phases are reported by relative window position, not calendar dates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Iterable


SCHEMA_VERSION = 1


def _canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    )


def diagnostic_fingerprint(payload: dict[str, Any]) -> str:
    value = dict(payload)
    value.pop("diagnostic_fingerprint", None)
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _verify(report: dict[str, Any]) -> None:
    from automation.research_workflow import verify_result_fingerprint
    verify_result_fingerprint(report)


def _number(value: Any) -> float | None:
    if value == "inf":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _median(values: Iterable[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return float(median(clean)) if clean else None


def _candidate_tuple(candidate: dict[str, Any]) -> tuple[Any, ...]:
    strategy = candidate.get("strategy", {})
    return (
        candidate.get("risk_per_trade"),
        candidate.get("leverage"),
        strategy.get("momentum", {}).get("lookback"),
        strategy.get("mean_reversion", {}).get("window"),
        strategy.get("mean_reversion", {}).get("threshold"),
    )


def _candidate_signature(candidate: dict[str, Any]) -> str:
    return _canonical(candidate)


def _universe(report: dict[str, Any]) -> str:
    value = report.get("run_manifest", {}).get("data_manifest", {}).get("universe")
    if not isinstance(value, str) or not value:
        raise ValueError("Research-Report besitzt kein gültiges Research-Universum.")
    return value


def _collect(reports: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    datasets: list[dict[str, Any]] = []
    windows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for report_index, report in enumerate(reports):
        _verify(report)
        safety = report.get("safety", {})
        if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
            raise ValueError(f"Report {report_index} besitzt einen unsicheren Safety-Zustand.")
        universe = _universe(report)

        for dataset in report.get("datasets", []):
            symbol = dataset.get("symbol")
            interval = dataset.get("interval")
            profile = dataset.get("statistical_diagnostics", {}).get(
                "multiple_testing", {}
            ).get("selection_profile")
            if not all(isinstance(v, str) and v for v in (symbol, interval, profile)):
                raise ValueError("Dataset besitzt unvollständige Identität.")

            key = (universe, symbol, profile)
            if key in seen:
                raise ValueError(f"Doppelte Dataset/Profile-Auswertung: {key}.")
            seen.add(key)

            wfo_candidate = dataset.get("walk_forward", {}).get("selected_candidate")
            if not isinstance(wfo_candidate, dict):
                raise ValueError(f"{key}: kein Selected Candidate.")

            gates = {
                gate.get("name"): bool(gate.get("passed"))
                for gate in dataset.get("research_gates", {}).get("gates", [])
                if isinstance(gate, dict) and isinstance(gate.get("name"), str)
            }
            datasets.append({
                "universe": universe,
                "symbol": symbol,
                "interval": interval,
                "profile": profile,
                "wfo_candidate": wfo_candidate,
                "gates": gates,
            })

            rolling = dataset.get("rolling_walk_forward", {}).get("windows", [])
            if not isinstance(rolling, list) or not rolling:
                raise ValueError(f"{key}: keine Rolling-WF-Fenster.")

            for window in rolling:
                candidate = window.get("selected_candidate")
                index = window.get("window_index")
                if not isinstance(candidate, dict) or not isinstance(index, int) or index < 1:
                    raise ValueError(f"{key}: ungültiges Rolling-WF-Fenster.")
                windows.append({
                    "universe": universe,
                    "symbol": symbol,
                    "profile": profile,
                    "window_index": index,
                    "candidate": candidate,
                    "same_as_wfo": candidate == wfo_candidate,
                    "profit": float(window.get("test_net_profit_eur", 0.0)),
                    "profit_factor": _number(window.get("test_profit_factor")),
                    "drawdown": float(window.get("test_max_drawdown_percent", 0.0)),
                    "trades": int(window.get("test_trade_count", 0)),
                })

    if not datasets:
        raise ValueError("Mindestens eine Dataset/Profile-Auswertung wird benötigt.")
    return datasets, windows


def _phase_summary(windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for row in windows:
        groups[(row["universe"], row["window_index"])].append(row)

    result = []
    for (universe, index), rows in sorted(groups.items()):
        profits = [r["profit"] for r in rows]
        positives = sum(v > 0 for v in profits)
        result.append({
            "universe": universe,
            "window_index": index,
            "evaluation_count": len(rows),
            "positive_profit_count": positives,
            "positive_profit_rate": positives / len(rows),
            "median_net_profit_eur": _median(profits),
            "median_profit_factor": _median(r["profit_factor"] for r in rows),
            "median_max_drawdown_percent": _median(r["drawdown"] for r in rows),
            "median_trade_count": _median(float(r["trades"]) for r in rows),
            "source_scope": "rolling_wf_window_position",
        })
    return result


def _asset_summary(datasets: list[dict[str, Any]], windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_asset = defaultdict(list)
    for row in datasets:
        by_asset[(row["universe"], row["symbol"])].append(row)

    result = []
    for (universe, symbol), rows in sorted(by_asset.items()):
        asset_windows = [r for r in windows if r["universe"] == universe and r["symbol"] == symbol]
        phases = []
        for index in sorted({r["window_index"] for r in asset_windows}):
            values = [r["profit"] for r in asset_windows if r["window_index"] == index]
            positives = sum(v > 0 for v in values)
            phases.append({
                "window_index": index,
                "evaluation_count": len(values),
                "positive_profit_count": positives,
                "positive_profit_rate": positives / len(values),
                "median_net_profit_eur": _median(values),
            })
        gate_names = sorted({name for row in rows for name in row["gates"]})
        gate_pass_rates = {}
        for name in gate_names:
            passed = sum(row["gates"].get(name, False) for row in rows)
            gate_pass_rates[name] = {
                "passed_count": passed,
                "evaluation_count": len(rows),
                "pass_rate": passed / len(rows),
            }
        result.append({
            "universe": universe,
            "asset": symbol,
            "profile_evaluation_count": len(rows),
            "gate_pass_rates": gate_pass_rates,
            "rolling_phase_profile": phases,
        })
    return result


def _candidate_persistence(datasets: list[dict[str, Any]], windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for row in windows:
        groups[(row["universe"], row["profile"])].append(row)

    result = []
    for (universe, profile), rows in sorted(groups.items()):
        same = sum(r["same_as_wfo"] for r in rows)
        unique = len({_candidate_signature(r["candidate"]) for r in rows})
        result.append({
            "universe": universe,
            "selection_profile": profile,
            "rolling_window_evaluations": len(rows),
            "same_as_fixed_wfo_count": same,
            "same_as_fixed_wfo_rate": same / len(rows),
            "unique_rolling_candidate_count": unique,
        })
    return result


def _candidate_modes(windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for row in windows:
        groups[(row["universe"], row["window_index"])].append(row)

    result = []
    for (universe, index), rows in sorted(groups.items()):
        counts = Counter(_candidate_tuple(r["candidate"]) for r in rows)
        modes = []
        for values, count in counts.most_common():
            modes.append({
                "parameter_tuple": {
                    "risk_per_trade": values[0],
                    "leverage": values[1],
                    "momentum_lookback": values[2],
                    "mean_reversion_window": values[3],
                    "mean_reversion_threshold": values[4],
                },
                "count": count,
            })
        result.append({
            "universe": universe,
            "window_index": index,
            "evaluation_count": len(rows),
            "candidate_parameter_modes": modes,
        })
    return result


def build_time_asset_diagnostics(reports: Iterable[dict[str, Any]]) -> dict[str, Any]:
    reports = list(reports)
    datasets, windows = _collect(reports)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_type": "time_phase_asset_universe",
        "report_count": len(reports),
        "dataset_profile_count": len(datasets),
        "rolling_window_count": len(windows),
        "universes": sorted({row["universe"] for row in datasets}),
        "source_run_fingerprints": sorted({
            report["run_manifest"]["run_fingerprint"]
            for report in reports
        }),
        "source_result_fingerprints": sorted({
            report["result_fingerprint"]
            for report in reports
        }),
        "phase_summary": _phase_summary(windows),
        "asset_summary": _asset_summary(datasets, windows),
        "candidate_persistence": _candidate_persistence(datasets, windows),
        "candidate_structure_modes": _candidate_modes(windows),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
        "interpretation": {
            "diagnostic_only": True,
            "research_reexecution": False,
            "gate_changes": False,
            "parameter_space_changes": False,
            "selection_logic_changes": False,
            "calendar_phase_claims": False,
        },
    }
    payload["diagnostic_fingerprint"] = diagnostic_fingerprint(payload)
    return payload


def load_report_files(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    reports = []
    for raw in paths:
        path = Path(raw)
        files = sorted(path.rglob("analysis_*.json")) if path.is_dir() else [path]
        for file_path in files:
            reports.append(json.loads(file_path.read_text(encoding="utf-8")))
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description="Zeitphasen-/Asset-Universe-Diagnose aus Research-Reports.")
    parser.add_argument("--reports-root", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = build_time_asset_diagnostics(load_report_files(args.reports_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    print(f"TIME_ASSET_DIAGNOSTIC: {output}")
    print(f"DIAGNOSTIC_FINGERPRINT: {result['diagnostic_fingerprint']}")
    print(f"REPORTS: {result['report_count']}")
    print(f"DATASET_PROFILES: {result['dataset_profile_count']}")
    print(f"ROLLING_WINDOWS: {result['rolling_window_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
