"""Analyze adjacent Rolling-WF candidate migrations from an archived control report.

This is diagnostic only. It reuses already computed window results and performs
no backtest, optimization or order execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

MIN_PROFIT_FACTOR = 1.10
MAX_DRAWDOWN_PERCENT = 10.0


def _candidate_fp(candidate: dict[str, Any]) -> str:
    payload = json.dumps(
        candidate,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _flatten_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    flat = {
        "risk_per_trade": candidate["risk_per_trade"],
        "leverage": candidate["leverage"],
        "momentum.lookback": candidate["strategy"]["momentum"]["lookback"],
        "mean_reversion.window": candidate["strategy"]["mean_reversion"]["window"],
        "mean_reversion.threshold": candidate["strategy"]["mean_reversion"]["threshold"],
    }
    return flat


def _changed_parameters(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    a = _flatten_candidate(left)
    b = _flatten_candidate(right)
    return sorted(k for k in a if a[k] != b[k])


def _destination_flags(window: dict[str, Any]) -> dict[str, bool]:
    pf = window["profit_factor"]
    pf_numeric = float("inf") if pf == "inf" else float(pf)
    profit = float(window["net_profit_eur"])
    dd = float(window["max_drawdown_percent"])
    return {
        "nonpositive_profit": profit <= 0.0,
        "profit_factor_failure": pf_numeric < MIN_PROFIT_FACTOR,
        "drawdown_failure": dd > MAX_DRAWDOWN_PERCENT,
    }


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "transition_count": 0,
            "destination_profit_positive_rate": 0.0,
            "destination_profit_factor_pass_rate": 0.0,
            "destination_drawdown_pass_rate": 0.0,
            "median_destination_profit_eur": None,
        }

    profits = [float(r["destination"]["net_profit_eur"]) for r in rows]
    pf_pass = sum(not r["flags"]["profit_factor_failure"] for r in rows)
    dd_pass = sum(not r["flags"]["drawdown_failure"] for r in rows)
    profit_pos = sum(r["destination"]["net_profit_eur"] > 0 for r in rows)

    return {
        "transition_count": len(rows),
        "destination_profit_positive_rate": profit_pos / len(rows),
        "destination_profit_factor_pass_rate": pf_pass / len(rows),
        "destination_drawdown_pass_rate": dd_pass / len(rows),
        "median_destination_profit_eur": statistics.median(profits),
    }


def _parameter_summary(transitions: list[dict[str, Any]]) -> dict[str, Any]:
    params = [
        "risk_per_trade",
        "leverage",
        "momentum.lookback",
        "mean_reversion.window",
        "mean_reversion.threshold",
    ]
    out: dict[str, Any] = {}

    for parameter in params:
        changed = [t for t in transitions if parameter in t["changed_parameters"]]
        unchanged = [t for t in transitions if parameter not in t["changed_parameters"]]
        out[parameter] = {
            "changed": _summarize(changed),
            "unchanged": _summarize(unchanged),
            "change_count": len(changed),
        }

    return out


def analyze(report: dict[str, Any]) -> dict[str, Any]:
    transitions: list[dict[str, Any]] = []

    for dataset in report["datasets"]:
        for profile in dataset["profiles"]:
            for geometry_name in ("small", "large"):
                windows = profile[geometry_name]["windows"]
                for left, right in zip(windows, windows[1:]):
                    changed = _changed_parameters(
                        left["candidate"],
                        right["candidate"],
                    )
                    transitions.append({
                        "symbol": dataset["symbol"],
                        "selection_profile": profile["selection_profile"],
                        "geometry": geometry_name,
                        "source_window": left["window_index"],
                        "destination_window": right["window_index"],
                        "source_candidate_fingerprint": _candidate_fp(left["candidate"]),
                        "destination_candidate_fingerprint": _candidate_fp(right["candidate"]),
                        "changed_parameters": changed,
                        "change_count": len(changed),
                        "destination": {
                            "net_profit_eur": right["net_profit_eur"],
                            "profit_factor": right["profit_factor"],
                            "max_drawdown_percent": right["max_drawdown_percent"],
                            "trade_count": right["trade_count"],
                        },
                        "flags": _destination_flags(right),
                    })

    by_geometry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in transitions:
        by_geometry[t["geometry"]].append(t)

    migration_rows = [t for t in transitions if t["changed_parameters"]]
    stable_rows = [t for t in transitions if not t["changed_parameters"]]

    change_combinations = Counter(
        tuple(t["changed_parameters"])
        for t in transitions
        if t["changed_parameters"]
    )

    report_out = {
        "schema_version": 1,
        "diagnostic_type": "candidate_migration_failure_analysis",
        "source_diagnostic_type": report.get("diagnostic_type"),
        "source_diagnostic_fingerprint": report.get("diagnostic_fingerprint"),
        "source_code_version": report.get("code_version"),
        "source_target_count": report.get("target_count"),
        "source_research_candle_count": report.get("research_candle_count"),
        "source_universe": report.get("universe"),
        "transition_count_total": len(transitions),
        "transition_count_migration": len(migration_rows),
        "transition_count_stable": len(stable_rows),
        "migration_rate": len(migration_rows) / len(transitions) if transitions else 0.0,
        "overall": {
            "migration": _summarize(migration_rows),
            "stable": _summarize(stable_rows),
        },
        "by_geometry": {
            name: {
                "transition_count": len(rows),
                "migration": _summarize([t for t in rows if t["changed_parameters"]]),
                "stable": _summarize([t for t in rows if not t["changed_parameters"]]),
                "parameter_summary": _parameter_summary(rows),
            }
            for name, rows in by_geometry.items()
        },
        "parameter_summary": _parameter_summary(transitions),
        "change_combinations": [
            {
                "changed_parameters": list(key),
                "transition_count": count,
            }
            for key, count in change_combinations.most_common()
        ],
        "transitions": transitions,
        "interpretation_scope": {
            "diagnostic_only": True,
            "no_new_backtest": True,
            "no_new_optimization": True,
            "no_gate_changes": True,
            "associations_are_descriptive_not_causal": True,
            "destination_flags_are_window_level_not_formal_rolling_gate_failures": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    report_out["analysis_fingerprint"] = hashlib.sha256(
        json.dumps(
            {k: v for k, v in report_out.items() if k != "analysis_fingerprint"},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()
    return report_out


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Kandidaten-Migrationsanalyse — Rolling-WF",
        "",
        f"- Analysis-Fingerprint: {result['analysis_fingerprint']}",
        f"- Source-Fingerprint: {result['source_diagnostic_fingerprint']}",
        f"- Transitions: {result['transition_count_total']}",
        f"- Migrations: {result['transition_count_migration']}",
        f"- Stable: {result['transition_count_stable']}",
        f"- Migration-Rate: {result['migration_rate']:.3f}",
        "",
        "## Gesamtvergleich",
        "",
        "| Gruppe | Transitions | positive Destination | PF >= 1,10 | DD <= 10 % | Median Profit EUR |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for name in ("migration", "stable"):
        item = result["overall"][name]
        lines.append(
            f"| {name} | {item['transition_count']} | "
            f"{item['destination_profit_positive_rate']:.3f} | "
            f"{item['destination_profit_factor_pass_rate']:.3f} | "
            f"{item['destination_drawdown_pass_rate']:.3f} | "
            f"{item['median_destination_profit_eur']:.3f} |"
        )

    lines += [
        "",
        "## Geometrien",
        "",
        "| Geometrie | Gruppe | Transitions | positive Destination | PF >= 1,10 | Median Profit EUR |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for geometry, data in sorted(result["by_geometry"].items()):
        for group in ("migration", "stable"):
            item = data[group]
            lines.append(
                f"| {geometry} | {group} | {item['transition_count']} | "
                f"{item['destination_profit_positive_rate']:.3f} | "
                f"{item['destination_profit_factor_pass_rate']:.3f} | "
                f"{item['median_destination_profit_eur']:.3f} |"
            )

    lines += [
        "",
        "## Parameter-Assoziationen",
        "",
        "| Parameter | Änderung Count | positive Destination bei Änderung | positive Destination ohne Änderung | PF-Pass bei Änderung | PF-Pass ohne Änderung |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for parameter, item in result["parameter_summary"].items():
        changed = item["changed"]
        unchanged = item["unchanged"]
        lines.append(
            f"| {parameter} | {item['change_count']} | "
            f"{changed['destination_profit_positive_rate']:.3f} | "
            f"{unchanged['destination_profit_positive_rate']:.3f} | "
            f"{changed['destination_profit_factor_pass_rate']:.3f} | "
            f"{unchanged['destination_profit_factor_pass_rate']:.3f} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "Die Ergebnisse beschreiben nur Zusammenhänge zwischen einem Kandidatenwechsel und den Metriken des direkt folgenden Rolling-Fensters.",
        "Die Destination-Flags sind Fensterdiagnostik und nicht identisch mit den formalen Rolling-Gate-Kriterien, die auf den gesamten Rolling-Satz angewendet werden.",
        "Keine Beobachtung dieser Analyse rechtfertigt allein eine Änderung des Parameterraums, der Selection-Profile oder der Gate-Schwellen.",
        "",
        "Paper-Only: True; Live-Trading: False; Orders: False.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-dir", default="research/candidate_migration")
    args = parser.parse_args()

    source = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    result = analyze(source)

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "candidate_migration_analysis.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    (output / "candidate_migration_analysis.md").write_text(
        _markdown(result),
        encoding="utf-8",
    )

    print("CANDIDATE_MIGRATION_ANALYSIS: COMPLETED")
    print("ANALYSIS_FINGERPRINT:", result["analysis_fingerprint"])
    print("TRANSITIONS:", result["transition_count_total"])
    print("MIGRATIONS:", result["transition_count_migration"])
    print("STABLE:", result["transition_count_stable"])
    print("PAPER_ONLY:", result["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", result["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
