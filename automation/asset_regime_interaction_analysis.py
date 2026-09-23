"""Diagnose asset-by-regime interactions from the immutable Rolling-Control artifact.

This layer is descriptive only. It imports the established combined
volatility/trend/choppiness analysis and adds asset-specific aggregation.
No downloads, backtests, optimization, or orders are performed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from automation.regime_trend_choppiness_analysis import analyze as analyze_combined


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "evaluation_count": 0,
            "unique_market_windows": 0,
            "positive_profit_rate": 0.0,
            "pf_pass_rate": 0.0,
            "median_profit_eur": None,
        }

    keys = {(r["symbol"], r["geometry"], r["window_index"]) for r in rows}
    return {
        "evaluation_count": len(rows),
        "unique_market_windows": len(keys),
        "positive_profit_rate": sum(
            float(r["net_profit_eur"]) > 0.0 for r in rows
        )
        / len(rows),
        "pf_pass_rate": sum(
            not r["flags"]["profit_factor_failure"] for r in rows
        )
        / len(rows),
        "median_profit_eur": statistics.median(
            float(r["net_profit_eur"]) for r in rows
        ),
    }


def _transition_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "transition_count": 0,
            "migration_count": 0,
            "migration_rate": 0.0,
            "positive_destination_rate": 0.0,
            "pf_pass_rate": 0.0,
            "median_destination_profit_eur": None,
        }

    return {
        "transition_count": len(rows),
        "migration_count": sum(bool(r["migration"]) for r in rows),
        "migration_rate": sum(bool(r["migration"]) for r in rows) / len(rows),
        "positive_destination_rate": sum(
            bool(r["destination_positive_profit"]) for r in rows
        )
        / len(rows),
        "pf_pass_rate": sum(
            not bool(r["destination_profit_factor_failure"]) for r in rows
        )
        / len(rows),
        "median_destination_profit_eur": statistics.median(
            float(r["destination_profit_eur"]) for r in rows
        ),
    }


def analyze_asset_interaction(
    rolling: dict[str, Any],
    archive_manifest: dict[str, Any],
    raw_dir: str | Path,
) -> dict[str, Any]:
    combined = analyze_combined(rolling, archive_manifest, raw_dir)

    rolling_by_symbol = {
        ds["symbol"]: ds for ds in rolling["datasets"]
    }
    market_map = {
        (row["symbol"], row["geometry"], row["window_index"]): row
        for row in combined["market_features"]
    }

    evaluations: list[dict[str, Any]] = []
    for ds in rolling["datasets"]:
        symbol = ds["symbol"]
        for profile in ds["profiles"]:
            profile_name = profile["selection_profile"]
            for geometry in ("small", "large"):
                for window in profile[geometry]["windows"]:
                    feature = market_map[
                        (symbol, geometry, int(window["window_index"]))
                    ]
                    pf = (
                        float("inf")
                        if window["profit_factor"] == "inf"
                        else float(window["profit_factor"])
                    )
                    evaluations.append(
                        {
                            "symbol": symbol,
                            "selection_profile": profile_name,
                            "geometry": geometry,
                            "window_index": int(window["window_index"]),
                            "net_profit_eur": float(window["net_profit_eur"]),
                            "profit_factor": pf,
                            "flags": {
                                "profit_factor_failure": pf < 1.10,
                                "nonpositive_profit": float(
                                    window["net_profit_eur"]
                                )
                                <= 0.0,
                            },
                            "pre_test_vol_regime": feature[
                                "pre_test_vol_regime"
                            ],
                            "pre_test_structure_regime": feature[
                                "pre_test_structure_regime"
                            ],
                            "pre_test_trend_direction": feature[
                                "pre_test_trend_direction"
                            ],
                        }
                    )

    asset_summary: dict[str, Any] = {}
    for symbol in sorted(rolling_by_symbol):
        asset_rows = [r for r in evaluations if r["symbol"] == symbol]
        asset_summary[symbol] = {
            "overall": _summary(asset_rows),
            "by_geometry": {
                geometry: _summary(
                    [
                        r
                        for r in asset_rows
                        if r["geometry"] == geometry
                    ]
                )
                for geometry in ("small", "large")
            },
            "by_combined_regime": {},
        }

        for geometry in ("small", "large"):
            for vol_regime in ("low", "middle", "high"):
                for structure_regime in ("choppy", "mixed", "trending"):
                    label = f"{vol_regime}__{structure_regime}"
                    rows = [
                        r
                        for r in asset_rows
                        if r["geometry"] == geometry
                        and r["pre_test_vol_regime"] == vol_regime
                        and r["pre_test_structure_regime"] == structure_regime
                    ]
                    asset_summary[symbol]["by_combined_regime"][
                        f"{geometry}__{label}"
                    ] = {
                        "geometry": geometry,
                        "vol_regime": vol_regime,
                        "structure_regime": structure_regime,
                        **_summary(rows),
                    }

    asset_migration: dict[str, Any] = {}
    for symbol in sorted(rolling_by_symbol):
        rows = [r for r in combined["transitions"] if r["symbol"] == symbol]
        asset_migration[symbol] = {
            "overall": _transition_summary(rows),
            "by_geometry": {
                geometry: _transition_summary(
                    [r for r in rows if r["geometry"] == geometry]
                )
                for geometry in ("small", "large")
            },
            "by_volatility_shift": {
                label: _transition_summary(
                    [r for r in rows if predicate(r["volatility_percentile_delta"])]
                )
                for label, predicate in {
                    "contracting": lambda value: value < -0.10,
                    "stable_band": lambda value: -0.10 <= value <= 0.10,
                    "expanding": lambda value: value > 0.10,
                }.items()
            },
            "by_structure_shift": {
                label: _transition_summary(
                    [r for r in rows if predicate(r["structure_percentile_delta"])]
                )
                for label, predicate in {
                    "contracting": lambda value: value < -0.10,
                    "stable_band": lambda value: -0.10 <= value <= 0.10,
                    "expanding": lambda value: value > 0.10,
                }.items()
            },
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "rolling_asset_regime_interaction_analysis",
        "source_diagnostic_fingerprint": combined[
            "source_diagnostic_fingerprint"
        ],
        "source_target_count": combined["source_target_count"],
        "source_research_candle_count": combined[
            "source_research_candle_count"
        ],
        "source_universe": combined["source_universe"],
        "combined_analysis_fingerprint": combined["analysis_fingerprint"],
        "archive_integrity": combined["archive_integrity"],
        "evaluation_count": len(evaluations),
        "transition_count": len(combined["transitions"]),
        "asset_summary": asset_summary,
        "asset_migration_summary": asset_migration,
        "interpretation_scope": {
            "diagnostic_only": True,
            "no_new_backtest": True,
            "no_new_optimization": True,
            "no_new_data_download": True,
            "uses_only_immutable_archived_raw_data": True,
            "associations_are_descriptive_not_causal": True,
            "evaluation_rows_repeat_market_windows_across_selection_profiles": True,
            "regime_labels_are_ex_ante_relative_to_each_test_start": True,
        },
        "safety": combined["safety"],
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
        ).encode()
    ).hexdigest()
    return result


def markdown(result: dict[str, Any]) -> str:
    def fmt(value: Any) -> str:
        return "n/a" if value is None else f"{value:.3f}"

    lines = [
        "# Rolling-WF Asset-x-Regime-Interaktionsanalyse",
        "",
        f"- Analysis-Fingerprint: {result['analysis_fingerprint']}",
        f"- Combined-Source-Fingerprint: {result['combined_analysis_fingerprint']}",
        f"- Rolling-Source-Fingerprint: {result['source_diagnostic_fingerprint']}",
        f"- Research-Candles: {result['source_research_candle_count']}",
        "- Basis: immutable archivierte Rohdaten; keine neuen Downloads, Backtests oder Optimierungen",
        "",
        "## Asset-Gesamtbild",
        "",
        "| Asset | Geometrie | Evaluationen | eindeutige Marktfenster | positive Ergebnisse | PF-Pass | Median Profit EUR | Migration-Rate |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for symbol, data in result["asset_summary"].items():
        for geometry, summary in data["by_geometry"].items():
            migration = result["asset_migration_summary"][symbol][
                "by_geometry"
            ][geometry]
            lines.append(
                f"| {symbol} | {geometry} | {summary['evaluation_count']} | "
                f"{summary['unique_market_windows']} | "
                f"{summary['positive_profit_rate']:.3f} | "
                f"{summary['pf_pass_rate']:.3f} | "
                f"{fmt(summary['median_profit_eur'])} | "
                f"{migration['migration_rate']:.3f} |"
            )

    lines += [
        "",
        "## Asset x kombiniertes Regime",
        "",
        "| Asset | Geometrie | Volatilität | Struktur | Evaluationen | eindeutige Marktfenster | positive Ergebnisse | PF-Pass | Median Profit EUR |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for symbol, data in result["asset_summary"].items():
        for item in data["by_combined_regime"].values():
            if item["evaluation_count"] == 0:
                continue
            lines.append(
                f"| {symbol} | {item['geometry']} | {item['vol_regime']} | "
                f"{item['structure_regime']} | {item['evaluation_count']} | "
                f"{item['unique_market_windows']} | "
                f"{item['positive_profit_rate']:.3f} | "
                f"{item['pf_pass_rate']:.3f} | "
                f"{fmt(item['median_profit_eur'])} |"
            )

    lines += [
        "",
        "## Asset-spezifische Kandidatenmigration",
        "",
        "| Asset | Geometrie | Transitions | Migrationen | Migration-Rate | positive Destinationen | PF-Pass | Median Destination Profit EUR |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for symbol, data in result["asset_migration_summary"].items():
        for geometry, item in data["by_geometry"].items():
            lines.append(
                f"| {symbol} | {geometry} | {item['transition_count']} | "
                f"{item['migration_count']} | {item['migration_rate']:.3f} | "
                f"{item['positive_destination_rate']:.3f} | "
                f"{item['pf_pass_rate']:.3f} | "
                f"{fmt(item['median_destination_profit_eur'])} |"
            )

    lines += [
        "",
        "## Interpretation",
        "",
        "Die Asset-Aufteilung dient dazu, die zuvor beobachteten kombinierten Regimeeffekte zu lokalisieren.",
        "Eindeutige Marktfenster werden separat ausgewiesen, weil vier Selection-Profile dasselbe Marktfenster wiederverwenden.",
        "Eine beobachtete Asset-Assoziation ist deskriptiv und beweist keine Ursache. Sie rechtfertigt keine automatische Änderung von Parameterraum, Selection-Profile oder Gates.",
        "",
        "Paper-Only: True; Live-Trading: False; Orders: False.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rolling-json", required=True)
    parser.add_argument("--archive-manifest", required=True)
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument(
        "--output-dir", default="research/asset_regime_interaction"
    )
    args = parser.parse_args()

    rolling = json.loads(Path(args.rolling_json).read_text(encoding="utf-8"))
    archive = json.loads(Path(args.archive_manifest).read_text(encoding="utf-8"))
    result = analyze_asset_interaction(rolling, archive, args.raw_dir)

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "asset_regime_interaction_analysis.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    (output / "asset_regime_interaction_analysis.md").write_text(
        markdown(result),
        encoding="utf-8",
    )
    print("ASSET_REGIME_INTERACTION_ANALYSIS: COMPLETED")
    print("ANALYSIS_FINGERPRINT:", result["analysis_fingerprint"])
    print("EVALUATIONS:", result["evaluation_count"])
    print("TRANSITIONS:", result["transition_count"])
    print("PAPER_ONLY:", result["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", result["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
