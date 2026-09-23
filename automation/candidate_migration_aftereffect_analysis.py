"""Analyze the first OOS window immediately after candidate migration.

Diagnostic only: uses the immutable Rolling Geometry Control result. It does
not download data, run backtests, optimize parameters, or place orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

from automation.regime_trend_choppiness_analysis import changed_parameters

MIN_PROFIT_FACTOR = 1.10
MAX_DRAWDOWN_PERCENT = 10.0


def _profit_factor(value: Any) -> float:
    return float("inf") if value == "inf" else float(value)


def _flags(window: dict[str, Any]) -> dict[str, bool]:
    pf = _profit_factor(window["profit_factor"])
    return {
        "nonpositive_profit": float(window["net_profit_eur"]) <= 0.0,
        "profit_factor_failure": pf < MIN_PROFIT_FACTOR,
        "drawdown_failure": float(window["max_drawdown_percent"]) > MAX_DRAWDOWN_PERCENT,
    }


def _candidate_signature(candidate: dict[str, Any]) -> str:
    payload = json.dumps(
        candidate,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "transition_count": 0,
            "unique_destination_windows": 0,
            "migration_count": 0,
            "migration_rate": 0.0,
            "positive_destination_rate": 0.0,
            "pf_pass_rate": 0.0,
            "drawdown_pass_rate": 0.0,
            "median_destination_profit_eur": None,
            "median_source_to_destination_profit_delta_eur": None,
        }
    unique_destinations = {
        (row["symbol"], row["geometry"], row["destination_window"])
        for row in rows
    }
    return {
        "transition_count": len(rows),
        "unique_destination_windows": len(unique_destinations),
        "migration_count": sum(bool(row["migration"]) for row in rows),
        "migration_rate": sum(bool(row["migration"]) for row in rows) / len(rows),
        "positive_destination_rate": sum(
            bool(row["destination_positive_profit"]) for row in rows
        )
        / len(rows),
        "pf_pass_rate": sum(
            not bool(row["destination_profit_factor_failure"]) for row in rows
        )
        / len(rows),
        "drawdown_pass_rate": sum(
            not bool(row["destination_drawdown_failure"]) for row in rows
        )
        / len(rows),
        "median_destination_profit_eur": statistics.median(
            float(row["destination_profit_eur"]) for row in rows
        ),
        "median_source_to_destination_profit_delta_eur": statistics.median(
            float(row["destination_profit_delta_eur"]) for row in rows
        ),
    }


def analyze(rolling: dict[str, Any], archive_manifest: dict[str, Any]) -> dict[str, Any]:
    if rolling.get("diagnostic_type") != "rolling_geometry_time_phase_control":
        raise ValueError("Unexpected Rolling-Control diagnostic type.")
    if rolling.get("universe") != "benchmark":
        raise ValueError("Unexpected Rolling-Control universe.")
    if int(rolling.get("target_count", 0)) != 5000:
        raise ValueError("Unexpected Rolling-Control target count.")
    if int(rolling.get("research_candle_count", 0)) != 4500:
        raise ValueError("Unexpected Rolling-Control research candle count.")
    safety = rolling.get("safety", {})
    if safety.get("paper_only") is not True:
        raise ValueError("Paper-Only safety flag is not enabled.")
    if safety.get("live_trading_enabled") is not False:
        raise ValueError("Live trading must remain disabled.")
    if safety.get("orders_enabled") is not False:
        raise ValueError("Orders must remain disabled.")

    archive_safety = archive_manifest.get("safety", {})
    if archive_safety.get("paper_only") is not True:
        raise ValueError("Archived raw-data safety flag is not enabled.")
    if archive_safety.get("live_trading_enabled") is not False:
        raise ValueError("Archived raw-data live trading flag is enabled.")
    if archive_safety.get("orders_enabled") is not False:
        raise ValueError("Archived raw-data orders flag is enabled.")

    evaluations: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []

    for dataset in rolling["datasets"]:
        symbol = dataset["symbol"]
        for profile in dataset["profiles"]:
            profile_name = profile["selection_profile"]
            for geometry in ("small", "large"):
                windows = profile[geometry]["windows"]
                for window in windows:
                    candidate = window["candidate"]
                    evaluations.append(
                        {
                            "symbol": symbol,
                            "selection_profile": profile_name,
                            "geometry": geometry,
                            "window_index": int(window["window_index"]),
                            "candidate_signature": _candidate_signature(candidate),
                            "net_profit_eur": float(window["net_profit_eur"]),
                            "profit_factor": _profit_factor(window["profit_factor"]),
                            "max_drawdown_percent": float(
                                window["max_drawdown_percent"]
                            ),
                            "flags": _flags(window),
                        }
                    )

                for source, destination in zip(windows, windows[1:]):
                    changed = changed_parameters(
                        source["candidate"], destination["candidate"]
                    )
                    source_profit = float(source["net_profit_eur"])
                    destination_profit = float(destination["net_profit_eur"])
                    destination_flags = _flags(destination)
                    transitions.append(
                        {
                            "symbol": symbol,
                            "selection_profile": profile_name,
                            "geometry": geometry,
                            "source_window": int(source["window_index"]),
                            "destination_window": int(destination["window_index"]),
                            "source_candidate_signature": _candidate_signature(
                                source["candidate"]
                            ),
                            "destination_candidate_signature": _candidate_signature(
                                destination["candidate"]
                            ),
                            "migration": bool(changed),
                            "changed_parameters": changed,
                            "source_profit_eur": source_profit,
                            "destination_profit_eur": destination_profit,
                            "destination_profit_delta_eur": destination_profit
                            - source_profit,
                            "destination_profit_factor": (
                                "inf"
                                if destination["profit_factor"] == "inf"
                                else float(destination["profit_factor"])
                            ),
                            "destination_max_drawdown_percent": float(
                                destination["max_drawdown_percent"]
                            ),
                            "destination_positive_profit": destination_profit > 0.0,
                            "destination_profit_factor_failure": destination_flags[
                                "profit_factor_failure"
                            ],
                            "destination_drawdown_failure": destination_flags[
                                "drawdown_failure"
                            ],
                        }
                    )

    migration = [row for row in transitions if row["migration"]]
    stable = [row for row in transitions if not row["migration"]]

    by_asset_geometry: dict[str, Any] = {}
    for symbol in sorted({row["symbol"] for row in transitions}):
        by_asset_geometry[symbol] = {}
        for geometry in ("small", "large"):
            rows = [
                row
                for row in transitions
                if row["symbol"] == symbol and row["geometry"] == geometry
            ]
            by_asset_geometry[symbol][geometry] = {
                "all_transitions": _summary(rows),
                "after_migration": _summary(
                    [row for row in rows if row["migration"]]
                ),
                "after_stable_candidate": _summary(
                    [row for row in rows if not row["migration"]]
                ),
            }

    by_profile: dict[str, Any] = {}
    for profile in sorted({row["selection_profile"] for row in transitions}):
        rows = [row for row in transitions if row["selection_profile"] == profile]
        by_profile[profile] = {
            "all_transitions": _summary(rows),
            "after_migration": _summary(
                [row for row in rows if row["migration"]]
            ),
            "after_stable_candidate": _summary(
                [row for row in rows if not row["migration"]]
            ),
        }

    parameter_aftereffects: dict[str, Any] = {}
    parameters = (
        "risk_per_trade",
        "leverage",
        "momentum.lookback",
        "mean_reversion.window",
        "mean_reversion.threshold",
    )
    for parameter in parameters:
        rows = [
            row for row in migration if parameter in row["changed_parameters"]
        ]
        parameter_aftereffects[parameter] = _summary(rows)

    result = {
        "schema_version": 1,
        "diagnostic_type": "rolling_candidate_migration_aftereffect_analysis",
        "source_diagnostic_fingerprint": rolling["diagnostic_fingerprint"],
        "source_target_count": rolling["target_count"],
        "source_research_candle_count": rolling["research_candle_count"],
        "source_universe": rolling["universe"],
        "evaluation_count": len(evaluations),
        "transition_count": len(transitions),
        "migration_summary": {
            "all_transitions": _summary(transitions),
            "after_migration": _summary(migration),
            "after_stable_candidate": _summary(stable),
            "migration_vs_stable_profit_delta_eur": (
                (
                    _summary(migration)["median_destination_profit_eur"]
                    if migration
                    else None
                )
                - (
                    _summary(stable)["median_destination_profit_eur"]
                    if stable
                    else None
                )
                if migration and stable
                else None
            ),
            "migration_vs_stable_positive_rate_delta": (
                _summary(migration)["positive_destination_rate"]
                - _summary(stable)["positive_destination_rate"]
                if migration and stable
                else None
            ),
            "migration_vs_stable_pf_pass_rate_delta": (
                _summary(migration)["pf_pass_rate"]
                - _summary(stable)["pf_pass_rate"]
                if migration and stable
                else None
            ),
        },
        "by_asset_geometry": by_asset_geometry,
        "by_selection_profile": by_profile,
        "parameter_aftereffects": parameter_aftereffects,
        "transitions": transitions,
        "interpretation_scope": {
            "diagnostic_only": True,
            "first_oos_after_migration_is_destination_window": True,
            "stable_comparison_is_adjacent_destination_without_candidate_change": True,
            "no_new_backtest": True,
            "no_new_optimization": True,
            "no_new_data_download": True,
            "uses_rolling_control_artifact_only": True,
            "associations_are_descriptive_not_causal": True,
            "evaluation_rows_repeat_market_windows_across_selection_profiles": True,
        },
        "safety": safety,
        "archive_manifest_fingerprint": archive_manifest.get(
            "manifest_fingerprint"
        ),
    }
    result["analysis_fingerprint"] = hashlib.sha256(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key != "analysis_fingerprint"
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    return result


def markdown(result: dict[str, Any]) -> str:
    def fmt(value: Any) -> str:
        return "n/a" if value is None else f"{value:.3f}"

    overall = result["migration_summary"]
    lines = [
        "# Rolling-WF Kandidaten-Migrations-Nachwirkung",
        "",
        f"- Analysis-Fingerprint: {result['analysis_fingerprint']}",
        f"- Source-Fingerprint: {result['source_diagnostic_fingerprint']}",
        f"- Research-Candles: {result['source_research_candle_count']}",
        "- Basis: immutable Rolling-Control-Artifact; keine neuen Downloads, Backtests oder Optimierungen",
        "",
        "## Migration vs. stabiler Kandidat",
        "",
        "| Gruppe | Transitions | eindeutige Ziel-Fenster | Migrationen | positive Ziel-Fenster | PF-Pass | Median Ziel-Profit EUR | Median Profit-Delta EUR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, item in (
        ("alle", overall["all_transitions"]),
        ("nach Migration", overall["after_migration"]),
        ("stabiler Kandidat", overall["after_stable_candidate"]),
    ):
        lines.append(
            f"| {label} | {item['transition_count']} | {item['unique_destination_windows']} | "
            f"{item['migration_count']} | {item['positive_destination_rate']:.3f} | "
            f"{item['pf_pass_rate']:.3f} | {fmt(item['median_destination_profit_eur'])} | "
            f"{fmt(item['median_source_to_destination_profit_delta_eur'])} |"
        )

    lines += [
        "",
        "## Asset x Geometrie",
        "",
        "| Asset | Geometrie | Migration/Stable | Transitions | eindeutige Ziel-Fenster | positive Ziel-Fenster | PF-Pass | Median Ziel-Profit EUR | Median Profit-Delta EUR |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for symbol, geometries in result["by_asset_geometry"].items():
        for geometry, data in geometries.items():
            for label, key in (
                ("nach Migration", "after_migration"),
                ("stabiler Kandidat", "after_stable_candidate"),
            ):
                item = data[key]
                lines.append(
                    f"| {symbol} | {geometry} | {label} | {item['transition_count']} | "
                    f"{item['unique_destination_windows']} | {item['positive_destination_rate']:.3f} | "
                    f"{item['pf_pass_rate']:.3f} | {fmt(item['median_destination_profit_eur'])} | "
                    f"{fmt(item['median_source_to_destination_profit_delta_eur'])} |"
                )

    lines += [
        "",
        "## Selection-Profile",
        "",
        "| Profil | Gruppe | Transitions | positive Ziel-Fenster | PF-Pass | Median Ziel-Profit EUR |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for profile, data in result["by_selection_profile"].items():
        for label, key in (
            ("nach Migration", "after_migration"),
            ("stabiler Kandidat", "after_stable_candidate"),
        ):
            item = data[key]
            lines.append(
                f"| {profile} | {label} | {item['transition_count']} | "
                f"{item['positive_destination_rate']:.3f} | {item['pf_pass_rate']:.3f} | "
                f"{fmt(item['median_destination_profit_eur'])} |"
            )

    lines += [
        "",
        "## Parameterwechsel",
        "",
        "| Parameter | Wechselzahl | positive Ziel-Fenster | PF-Pass | Median Ziel-Profit EUR | Median Profit-Delta EUR |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for parameter, item in result["parameter_aftereffects"].items():
        lines.append(
            f"| {parameter} | {item['transition_count']} | "
            f"{item['positive_destination_rate']:.3f} | {item['pf_pass_rate']:.3f} | "
            f"{fmt(item['median_destination_profit_eur'])} | "
            f"{fmt(item['median_source_to_destination_profit_delta_eur'])} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "Das Ziel-Fenster einer Migration ist das unmittelbar folgende OOS-Fenster, in dem der neue Kandidat erstmals eingesetzt wird.",
        "Die Vergleichsgruppe enthält benachbarte Übergänge ohne Kandidatenänderung.",
        "Die Auswertung ist deskriptiv und nicht kausal; besonders bei kleinen Asset-/Geometriegruppen werden keine stabilen Schlüsse aus Einzelfällen gezogen.",
        "Die vier Selection-Profile verwenden dieselben Marktfenster und sind daher keine vier unabhängigen Marktbeobachtungen.",
        "",
        "Paper-Only: True; Live-Trading: False; Orders: False.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rolling-json", required=True)
    parser.add_argument("--archive-manifest", required=True)
    parser.add_argument(
        "--output-dir", default="research/candidate_migration_aftereffect"
    )
    args = parser.parse_args()

    rolling = json.loads(
        Path(args.rolling_json).read_text(encoding="utf-8")
    )
    archive = json.loads(
        Path(args.archive_manifest).read_text(encoding="utf-8")
    )
    result = analyze(rolling, archive)

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "candidate_migration_aftereffect_analysis.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    (output / "candidate_migration_aftereffect_analysis.md").write_text(
        markdown(result),
        encoding="utf-8",
    )
    print("CANDIDATE_MIGRATION_AFTEREFFECT: COMPLETED")
    print("ANALYSIS_FINGERPRINT:", result["analysis_fingerprint"])
    print("EVALUATIONS:", result["evaluation_count"])
    print("TRANSITIONS:", result["transition_count"])
    print("MIGRATIONS:", result["migration_summary"]["after_migration"]["transition_count"])
    print("PAPER_ONLY:", result["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", result["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
