"""Diagnose Rolling-WF failure criteria by time phase, asset and candidate migration.

Diagnostic only: consumes archived rolling-control and candidate-migration reports.
No backtests, optimization or order execution are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

MIN_PROFIT_FACTOR = 1.10


def _pf_numeric(value: Any) -> float:
    return float("inf") if value == "inf" else float(value)


def _phase_label(window_index: int, window_count: int) -> str:
    if window_count <= 0:
        raise ValueError("window_count must be positive")
    fraction = (window_index - 0.5) / window_count
    if fraction < 1 / 3:
        return "early"
    if fraction < 2 / 3:
        return "middle"
    return "recent"


def _destination_flags(window: dict[str, Any]) -> dict[str, bool]:
    return {
        "nonpositive_profit": float(window["net_profit_eur"]) <= 0.0,
        "profit_factor_failure": _pf_numeric(window["profit_factor"]) < MIN_PROFIT_FACTOR,
        "zero_trades": int(window["trade_count"]) == 0,
    }


def _ratio(num: int, den: int) -> float:
    return num / den if den else 0.0


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    profits = [float(r["net_profit_eur"]) for r in rows]
    positive = sum(float(r["net_profit_eur"]) > 0 for r in rows)
    pf_pass = sum(_pf_numeric(r["profit_factor"]) >= MIN_PROFIT_FACTOR for r in rows)
    nonpositive = sum(float(r["net_profit_eur"]) <= 0 for r in rows)
    return {
        "window_count": len(rows),
        "profitable_windows": positive,
        "profitable_window_ratio": _ratio(positive, len(rows)),
        "profit_factor_pass_count": pf_pass,
        "profit_factor_pass_rate": _ratio(pf_pass, len(rows)),
        "nonpositive_profit_count": nonpositive,
        "nonpositive_profit_rate": _ratio(nonpositive, len(rows)),
        "zero_trade_windows": sum(int(r["trade_count"]) == 0 for r in rows),
        "total_net_profit_eur": sum(profits),
        "median_window_profit_eur": _median(profits),
        "total_trade_count": sum(int(r["trade_count"]) for r in rows),
    }


def analyze(rolling: dict[str, Any], migration: dict[str, Any]) -> dict[str, Any]:
    if migration.get("source_diagnostic_fingerprint") != rolling.get("diagnostic_fingerprint"):
        raise ValueError("migration source fingerprint does not match rolling report")

    migration_index = {
        (t["symbol"], t["selection_profile"], t["geometry"], t["destination_window"]): t
        for t in migration["transitions"]
    }

    windows: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []

    for dataset in rolling["datasets"]:
        symbol = dataset["symbol"]
        for profile in dataset["profiles"]:
            selection_profile = profile["selection_profile"]
            for geometry in ("small", "large"):
                block = profile[geometry]
                gate = block["gate"]
                failed_criteria = list(
                    gate.get("failed_criteria", gate.get("details", {}).get("failed_criteria", []))
                )
                evaluations.append({
                    "symbol": symbol,
                    "selection_profile": selection_profile,
                    "geometry": geometry,
                    "passed": bool(gate["passed"]),
                    "failed_criteria": failed_criteria,
                    "window_count": int(gate["details"]["window_count"]),
                    "total_trade_count": int(gate["details"]["total_trade_count"]),
                    "overall_profit_factor": float(gate["details"]["overall_profit_factor"]),
                    "profitable_window_ratio": float(gate["details"]["profitable_window_ratio"]),
                    "total_net_profit_eur": float(gate["details"]["total_net_profit_eur"]),
                })
                for window in block["windows"]:
                    row = {
                        "symbol": symbol,
                        "selection_profile": selection_profile,
                        "geometry": geometry,
                        "window_index": int(window["window_index"]),
                        "test_start": window["test_start"],
                        "test_end": window["test_end"],
                        "phase": _phase_label(
                            int(window["window_index"]),
                            int(block["window_count"]),
                        ),
                        "net_profit_eur": float(window["net_profit_eur"]),
                        "profit_factor": window["profit_factor"],
                        "max_drawdown_percent": float(window["max_drawdown_percent"]),
                        "trade_count": int(window["trade_count"]),
                    }
                    row["flags"] = _destination_flags(row)
                    migration_row = migration_index.get(
                        (
                            symbol,
                            selection_profile,
                            geometry,
                            row["window_index"],
                        )
                    )
                    if migration_row is None:
                        row["migration_status"] = "first_window"
                        row["changed_parameters"] = []
                    else:
                        row["migration_status"] = (
                            "migration" if migration_row["changed_parameters"] else "stable"
                        )
                        row["changed_parameters"] = list(migration_row["changed_parameters"])
                    windows.append(row)

    expected_transition_count = len(windows) - len(evaluations)
    if migration.get("transition_count_total") != expected_transition_count:
        raise ValueError(
            "migration transition count does not match rolling windows/evaluations"
        )

    phase_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    asset_phase_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    migration_phase_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    parameter_phase_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for row in windows:
        phase_groups[(row["geometry"], row["phase"])].append(row)
        asset_phase_groups[(row["symbol"], row["geometry"], row["phase"])].append(row)
        if row["migration_status"] in {"migration", "stable"}:
            migration_phase_groups[
                (row["geometry"], row["phase"], row["migration_status"])
            ].append(row)
            for parameter in row["changed_parameters"]:
                parameter_phase_groups[
                    (row["geometry"], row["phase"], parameter)
                ].append(row)

    phase_summary = {
        f"{geometry}:{phase}": _summary(rows)
        for (geometry, phase), rows in sorted(phase_groups.items())
    }
    asset_phase_summary = {
        f"{symbol}:{geometry}:{phase}": _summary(rows)
        for (symbol, geometry, phase), rows in sorted(asset_phase_groups.items())
    }
    migration_phase_summary = {
        f"{geometry}:{phase}:{status}": _summary(rows)
        for (geometry, phase, status), rows in sorted(migration_phase_groups.items())
    }

    parameter_phase_summary = {}
    for (geometry, phase, parameter), rows in sorted(parameter_phase_groups.items()):
        profits = [float(r["net_profit_eur"]) for r in rows]
        positive = sum(float(r["net_profit_eur"]) > 0 for r in rows)
        pf_pass = sum(_pf_numeric(r["profit_factor"]) >= MIN_PROFIT_FACTOR for r in rows)
        parameter_phase_summary[f"{geometry}:{phase}:{parameter}"] = {
            "transition_count": len(rows),
            "destination_profit_positive_rate": _ratio(positive, len(rows)),
            "destination_profit_factor_pass_rate": _ratio(pf_pass, len(rows)),
            "median_destination_profit_eur": _median(profits),
        }

    criteria = [
        "nonpositive_total_profit",
        "profit_factor",
        "profitable_window_ratio",
    ]
    formal_failure_summary = {
        key: {
            "evaluation_count": len(evaluations),
            "failed_count": sum(key in e["failed_criteria"] for e in evaluations),
            "fail_rate": _ratio(
                sum(key in e["failed_criteria"] for e in evaluations),
                len(evaluations),
            ),
        }
        for key in criteria
    }

    asset_failure_summary = {}
    for symbol in sorted({e["symbol"] for e in evaluations}):
        rows = [e for e in evaluations if e["symbol"] == symbol]
        asset_failure_summary[symbol] = {
            "evaluation_count": len(rows),
            "failed_criteria_counts": {
                key: sum(key in e["failed_criteria"] for e in rows)
                for key in criteria
            },
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "rolling_time_asset_failure_analysis",
        "source_rolling_diagnostic_type": rolling.get("diagnostic_type"),
        "source_rolling_diagnostic_fingerprint": rolling.get("diagnostic_fingerprint"),
        "source_rolling_code_version": rolling.get("code_version"),
        "source_migration_analysis_fingerprint": migration.get("analysis_fingerprint"),
        "transition_count_source": migration.get("transition_count_total"),
        "window_count": len(windows),
        "evaluation_count": len(evaluations),
        "formal_failure_summary": formal_failure_summary,
        "asset_failure_summary": asset_failure_summary,
        "phase_summary": phase_summary,
        "asset_phase_summary": asset_phase_summary,
        "migration_phase_summary": migration_phase_summary,
        "parameter_phase_summary": parameter_phase_summary,
        "evaluations": evaluations,
        "windows": windows,
        "interpretation_scope": {
            "diagnostic_only": True,
            "no_new_backtest": True,
            "no_new_optimization": True,
            "no_gate_changes": True,
            "descriptive_not_causal": True,
            "formal_gate_failures_kept_distinct_from_window_level_flags": True,
            "asset_scope_is_benchmark_asset_specific_not_asset_class_generalization": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["analysis_fingerprint"] = hashlib.sha256(
        json.dumps(
            {k: v for k, v in result.items() if k != "analysis_fingerprint"},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()
    return result


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Zeit-/Asset-Failure-Analyse — Rolling-WF",
        "",
        f"- Analysis-Fingerprint: {result['analysis_fingerprint']}",
        f"- Rolling Source-Fingerprint: {result['source_rolling_diagnostic_fingerprint']}",
        f"- Migration Source-Fingerprint: {result['source_migration_analysis_fingerprint']}",
        f"- Fenster: {result['window_count']}",
        f"- Evaluationen: {result['evaluation_count']}",
        "",
        "## Formale Rolling-Gate-Failures",
        "",
        "| Kriterium | Evaluationen | Failures | Fail-Rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for key, item in result["formal_failure_summary"].items():
        lines.append(
            f"| {key} | {item['evaluation_count']} | {item['failed_count']} | "
            f"{item['fail_rate']:.3f} |"
        )

    lines += [
        "",
        "## Zeitphasen",
        "",
        "Die Phasen werden je Rolling-Geometrie chronologisch in drei annähernd gleich große Abschnitte geteilt.",
        "",
        "| Geometrie | Phase | Fenster | positive Quote | PF-Pass | nonpositive | Gesamtprofit EUR | Median Fensterprofit EUR |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, item in result["phase_summary"].items():
        geometry, phase = key.split(":", 1)
        lines.append(
            f"| {geometry} | {phase} | {item['window_count']} | "
            f"{item['profitable_window_ratio']:.3f} | "
            f"{item['profit_factor_pass_rate']:.3f} | "
            f"{item['nonpositive_profit_rate']:.3f} | "
            f"{_fmt(item['total_net_profit_eur'])} | "
            f"{_fmt(item['median_window_profit_eur'])} |"
        )

    lines += [
        "",
        "## Asset-spezifische Failure-Dichte",
        "",
        "| Asset | Evaluationen | nonpositive_total_profit | profit_factor | profitable_window_ratio |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for symbol, item in result["asset_failure_summary"].items():
        c = item["failed_criteria_counts"]
        lines.append(
            f"| {symbol} | {item['evaluation_count']} | "
            f"{c['nonpositive_total_profit']} | {c['profit_factor']} | "
            f"{c['profitable_window_ratio']} |"
        )

    lines += [
        "",
        "## Asset- und Zeitphasen",
        "",
        "| Asset | Geometrie | Phase | Fenster | positive Quote | PF-Pass | Gesamtprofit EUR | Median Fensterprofit EUR |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, item in result["asset_phase_summary"].items():
        symbol, geometry, phase = key.split(":", 2)
        lines.append(
            f"| {symbol} | {geometry} | {phase} | {item['window_count']} | "
            f"{item['profitable_window_ratio']:.3f} | "
            f"{item['profit_factor_pass_rate']:.3f} | "
            f"{_fmt(item['total_net_profit_eur'])} | "
            f"{_fmt(item['median_window_profit_eur'])} |"
        )

    lines += [
        "",
        "## Migration vs. stabile Destination-Fenster nach Phase",
        "",
        "| Geometrie | Phase | Status | Fenster | positive Quote | PF-Pass | Median Profit EUR |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for key, item in result["migration_phase_summary"].items():
        geometry, phase, status = key.split(":", 2)
        lines.append(
            f"| {geometry} | {phase} | {status} | {item['window_count']} | "
            f"{item['profitable_window_ratio']:.3f} | "
            f"{item['profit_factor_pass_rate']:.3f} | "
            f"{_fmt(item['median_window_profit_eur'])} |"
        )

    lines += [
        "",
        "## Parameterwechsel nach Phase",
        "",
        "| Geometrie | Phase | Parameter | Transitionen | positive Destination | PF-Pass | Median Profit EUR |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for key, item in result["parameter_phase_summary"].items():
        geometry, phase, parameter = key.split(":", 2)
        lines.append(
            f"| {geometry} | {phase} | {parameter} | {item['transition_count']} | "
            f"{item['destination_profit_positive_rate']:.3f} | "
            f"{item['destination_profit_factor_pass_rate']:.3f} | "
            f"{_fmt(item['median_destination_profit_eur'])} |"
        )

    lines += [
        "",
        "## Asset-/Phasenkontext",
        "",
        "Die asset-/phasenbezogenen Tabellen dienen der Mustererkennung innerhalb des Benchmark-Universums. Sie sind keine Aussage über andere Assetklassen oder andere Marktregime.",
        "",
        "## Interpretation",
        "",
        "Formale Gate-Failures und Fensterdiagnostik werden bewusst getrennt ausgewiesen: nonpositive_total_profit, profit_factor und profitable_window_ratio sind Gate-Kriterien auf der jeweiligen Rolling-Auswertung; positive/negative Fenster sowie PF je Einzelfenster sind lokale Diagnosegrößen.",
        "",
        "Die Auswertung betrachtet Zeitphase, Asset und Kandidatenwechsel gemeinsam. Unterschiede zwischen Gruppen sind deskriptiv und nicht kausal. Sie rechtfertigen keine Änderung von Parameterraum, Selection-Profilen oder Gate-Schwellen.",
        "",
        "Sicherheitszustand: Paper-Only True; Live-Trading False; Orders False.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rolling-json", required=True)
    parser.add_argument("--migration-json", required=True)
    parser.add_argument("--output-dir", default="research/time_asset_failure")
    args = parser.parse_args()
    rolling = json.loads(Path(args.rolling_json).read_text(encoding="utf-8"))
    migration = json.loads(Path(args.migration_json).read_text(encoding="utf-8"))
    result = analyze(rolling, migration)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "time_asset_failure_analysis.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    (out / "time_asset_failure_analysis.md").write_text(
        markdown(result),
        encoding="utf-8",
    )
    print("TIME_ASSET_FAILURE_ANALYSIS: COMPLETED")
    print("ANALYSIS_FINGERPRINT:", result["analysis_fingerprint"])
    print("WINDOWS:", result["window_count"])
    print("EVALUATIONS:", result["evaluation_count"])
    print("PAPER_ONLY:", result["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", result["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
