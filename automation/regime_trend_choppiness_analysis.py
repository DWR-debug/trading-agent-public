"""Diagnose Rolling-WF failures by joint volatility and trend/choppiness regimes.

Diagnostic only. Uses the immutable raw-data archive from a Rolling Geometry
Control artifact and performs no downloads, backtests, optimization or orders.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

MIN_PROFIT_FACTOR = 1.10
MAX_DRAWDOWN_PERCENT = 10.0
VOL_LOOKBACK = 20
STRUCTURE_LOOKBACK = 60
LOW = 1 / 3
HIGH = 2 / 3


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = {"timestamp", "open", "high", "low", "close", "volume"}
    if not rows or set(rows[0]) != expected:
        raise ValueError(f"Unexpected CSV schema: {path}")
    return [
        {
            "timestamp": datetime.fromisoformat(r["timestamp"]),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": float(r["volume"]),
        }
        for r in rows
    ]


def dataset_fingerprint(rows: list[dict[str, Any]]) -> str:
    payload = [
        {
            "timestamp": r["timestamp"].isoformat(),
            "open": r["open"],
            "high": r["high"],
            "low": r["low"],
            "close": r["close"],
            "volume": r["volume"],
        }
        for r in rows
    ]
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def log_returns(closes: list[float]) -> list[float]:
    return [math.log(b / a) for a, b in zip(closes, closes[1:])]


def annualized_vol(values: list[float]) -> float:
    return statistics.stdev(values) * math.sqrt(252.0) if len(values) >= 2 else 0.0


def percentile(values: list[float], value: float) -> float:
    return sum(v <= value for v in values) / len(values) if values else 0.5


def regime_from_percentile(value: float) -> str:
    if value < LOW:
        return "low"
    if value > HIGH:
        return "high"
    return "middle"


def structure_from_percentile(value: float) -> str:
    if value < LOW:
        return "choppy"
    if value > HIGH:
        return "trending"
    return "mixed"


def candidate_values(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_per_trade": candidate["risk_per_trade"],
        "leverage": candidate["leverage"],
        "momentum.lookback": candidate["strategy"]["momentum"]["lookback"],
        "mean_reversion.window": candidate["strategy"]["mean_reversion"]["window"],
        "mean_reversion.threshold": candidate["strategy"]["mean_reversion"]["threshold"],
    }


def changed_parameters(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    a, b = candidate_values(left), candidate_values(right)
    return sorted(k for k in a if a[k] != b[k])


def flags(window: dict[str, Any]) -> dict[str, bool]:
    pf = float("inf") if window["profit_factor"] == "inf" else float(window["profit_factor"])
    return {
        "nonpositive_profit": float(window["net_profit_eur"]) <= 0.0,
        "profit_factor_failure": pf < MIN_PROFIT_FACTOR,
        "drawdown_failure": float(window["max_drawdown_percent"]) > MAX_DRAWDOWN_PERCENT,
    }


def feature_series(rows: list[dict[str, Any]]) -> dict[str, list[float | None]]:
    closes = [r["close"] for r in rows]
    returns = log_returns(closes)
    vol = [None] * len(rows)
    trend_return = [None] * len(rows)
    efficiency = [None] * len(rows)

    for end in range(VOL_LOOKBACK, len(rows)):
        window = returns[end - VOL_LOOKBACK : end]
        vol[end] = annualized_vol(window)

    for end in range(STRUCTURE_LOOKBACK, len(rows)):
        window = returns[end - STRUCTURE_LOOKBACK : end]
        total = sum(abs(x) for x in window)
        signed = sum(window)
        efficiency[end] = abs(signed) / total if total else 0.0
        trend_return[end] = math.exp(signed) - 1.0

    return {
        "returns": returns,
        "vol20": vol,
        "trend_return60": trend_return,
        "efficiency60": efficiency,
    }


def market_features(
    rolling: dict[str, Any],
    raw_by_symbol: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    research_count = int(rolling["research_candle_count"])
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()

    for ds in rolling["datasets"]:
        symbol = ds["symbol"]
        rows = raw_by_symbol[symbol][:research_count]
        features = feature_series(rows)
        vol = features["vol20"]
        trend_return = features["trend_return60"]
        efficiency = features["efficiency60"]

        for profile in ds["profiles"]:
            for geometry in ("small", "large"):
                for window in profile[geometry]["windows"]:
                    key = (symbol, geometry, int(window["window_index"]))
                    if key in seen:
                        continue
                    seen.add(key)

                    start = int(window["test_start_index"])
                    end = int(window["test_end_index"])
                    if not (
                        STRUCTURE_LOOKBACK <= start < end <= research_count
                    ):
                        raise ValueError(f"Window outside feature range: {key}")

                    current_vol = vol[start]
                    current_eff = efficiency[start]
                    current_trend = trend_return[start]
                    if current_vol is None or current_eff is None or current_trend is None:
                        raise ValueError(f"Missing ex-ante feature for {key}")

                    historical_vol = [
                        value for value in vol[VOL_LOOKBACK:start] if value is not None
                    ]
                    historical_eff = [
                        value
                        for value in efficiency[STRUCTURE_LOOKBACK:start]
                        if value is not None
                    ]
                    if not historical_vol or not historical_eff:
                        raise ValueError(f"Insufficient historical features for {key}")

                    vol_pct = percentile(historical_vol, current_vol)
                    structure_pct = percentile(historical_eff, current_eff)

                    out.append(
                        {
                            "symbol": symbol,
                            "geometry": geometry,
                            "window_index": int(window["window_index"]),
                            "test_start": window["test_start"],
                            "test_end": window["test_end"],
                            "test_start_index": start,
                            "test_end_index": end,
                            "pre_test_vol_20d": current_vol,
                            "pre_test_vol_percentile": vol_pct,
                            "pre_test_vol_regime": regime_from_percentile(vol_pct),
                            "pre_test_trend_return_60d_pct": current_trend * 100.0,
                            "pre_test_structure_efficiency_60d": current_eff,
                            "pre_test_structure_percentile": structure_pct,
                            "pre_test_structure_regime": structure_from_percentile(
                                structure_pct
                            ),
                            "pre_test_trend_direction": (
                                "up"
                                if current_trend > 0.0
                                else "down"
                                if current_trend < 0.0
                                else "flat"
                            ),
                        }
                    )
    return out


def evaluation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "evaluation_count": 0,
            "positive_profit_rate": 0.0,
            "pf_pass_rate": 0.0,
            "drawdown_pass_rate": 0.0,
            "median_profit_eur": None,
        }

    profits = [float(r["net_profit_eur"]) for r in rows]
    return {
        "evaluation_count": len(rows),
        "positive_profit_rate": sum(float(r["net_profit_eur"]) > 0.0 for r in rows)
        / len(rows),
        "pf_pass_rate": sum(not r["flags"]["profit_factor_failure"] for r in rows)
        / len(rows),
        "drawdown_pass_rate": sum(not r["flags"]["drawdown_failure"] for r in rows)
        / len(rows),
        "median_profit_eur": statistics.median(profits),
    }


def transition_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
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


def analyze(
    rolling: dict[str, Any],
    archive_manifest: dict[str, Any],
    raw_dir: str | Path,
) -> dict[str, Any]:
    raw_root = Path(raw_dir)
    archive_by_symbol = {item["symbol"]: item for item in archive_manifest["datasets"]}
    raw_by_symbol: dict[str, list[dict[str, Any]]] = {}
    integrity = []

    for ds in rolling["datasets"]:
        symbol = ds["symbol"]
        archive = archive_by_symbol[symbol]
        interval = archive["interval"]
        path = raw_root / symbol / f"{interval}.csv"
        if sha256_file(path) != archive["byte_sha256"]:
            raise ValueError(f"{symbol}: byte SHA-256 mismatch")

        rows = load_csv(path)
        if len(rows) != int(archive["candle_count"]):
            raise ValueError(f"{symbol}: candle count mismatch")

        if dataset_fingerprint(rows) != archive["dataset_fingerprint"]:
            raise ValueError(f"{symbol}: full dataset fingerprint mismatch")

        research = rows[: int(rolling["research_candle_count"])]
        if dataset_fingerprint(research) != ds["research_fingerprint"]:
            raise ValueError(f"{symbol}: research fingerprint mismatch")

        raw_by_symbol[symbol] = rows
        integrity.append(
            {
                "symbol": symbol,
                "interval": interval,
                "full_candle_count": len(rows),
                "research_candle_count": len(research),
                "byte_sha256": archive["byte_sha256"],
                "full_dataset_fingerprint": archive["dataset_fingerprint"],
                "research_fingerprint": ds["research_fingerprint"],
            }
        )

    market = market_features(rolling, raw_by_symbol)
    market_map = {
        (row["symbol"], row["geometry"], row["window_index"]): row for row in market
    }

    evaluations: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []

    for ds in rolling["datasets"]:
        symbol = ds["symbol"]
        for profile in ds["profiles"]:
            profile_name = profile["selection_profile"]
            for geometry in ("small", "large"):
                windows = profile[geometry]["windows"]

                for window in windows:
                    feature = market_map[(symbol, geometry, int(window["window_index"]))]
                    evaluations.append(
                        {
                            "symbol": symbol,
                            "selection_profile": profile_name,
                            "geometry": geometry,
                            "window_index": int(window["window_index"]),
                            "net_profit_eur": float(window["net_profit_eur"]),
                            "profit_factor": window["profit_factor"],
                            "max_drawdown_percent": float(
                                window["max_drawdown_percent"]
                            ),
                            "flags": flags(window),
                            "pre_test_vol_percentile": feature[
                                "pre_test_vol_percentile"
                            ],
                            "pre_test_vol_regime": feature["pre_test_vol_regime"],
                            "pre_test_trend_return_60d_pct": feature[
                                "pre_test_trend_return_60d_pct"
                            ],
                            "pre_test_structure_efficiency_60d": feature[
                                "pre_test_structure_efficiency_60d"
                            ],
                            "pre_test_structure_percentile": feature[
                                "pre_test_structure_percentile"
                            ],
                            "pre_test_structure_regime": feature[
                                "pre_test_structure_regime"
                            ],
                            "pre_test_trend_direction": feature[
                                "pre_test_trend_direction"
                            ],
                        }
                    )

                for left, right in zip(windows, windows[1:]):
                    source = market_map[
                        (symbol, geometry, int(left["window_index"]))
                    ]
                    destination = market_map[
                        (symbol, geometry, int(right["window_index"]))
                    ]
                    changed = changed_parameters(
                        left["candidate"], right["candidate"]
                    )
                    destination_flags = flags(right)
                    transitions.append(
                        {
                            "symbol": symbol,
                            "selection_profile": profile_name,
                            "geometry": geometry,
                            "source_window": int(left["window_index"]),
                            "destination_window": int(right["window_index"]),
                            "migration": bool(changed),
                            "changed_parameters": changed,
                            "source_vol_percentile": source[
                                "pre_test_vol_percentile"
                            ],
                            "destination_vol_percentile": destination[
                                "pre_test_vol_percentile"
                            ],
                            "volatility_percentile_delta": (
                                destination["pre_test_vol_percentile"]
                                - source["pre_test_vol_percentile"]
                            ),
                            "source_structure_percentile": source[
                                "pre_test_structure_percentile"
                            ],
                            "destination_structure_percentile": destination[
                                "pre_test_structure_percentile"
                            ],
                            "structure_percentile_delta": (
                                destination["pre_test_structure_percentile"]
                                - source["pre_test_structure_percentile"]
                            ),
                            "source_structure_regime": source[
                                "pre_test_structure_regime"
                            ],
                            "destination_structure_regime": destination[
                                "pre_test_structure_regime"
                            ],
                            "destination_vol_regime": destination[
                                "pre_test_vol_regime"
                            ],
                            "destination_positive_profit": float(
                                right["net_profit_eur"]
                            )
                            > 0.0,
                            "destination_profit_factor_failure": destination_flags[
                                "profit_factor_failure"
                            ],
                            "destination_profit_eur": float(
                                right["net_profit_eur"]
                            ),
                        }
                    )

    combined_summary: dict[str, Any] = {}
    for geometry in ("small", "large"):
        rows = [r for r in evaluations if r["geometry"] == geometry]
        by_combined: dict[str, Any] = {}
        for vol_regime in ("low", "middle", "high"):
            for structure_regime in ("choppy", "mixed", "trending"):
                label = f"{vol_regime}__{structure_regime}"
                by_combined[label] = {
                    "vol_regime": vol_regime,
                    "structure_regime": structure_regime,
                    **evaluation_summary(
                        [
                            r
                            for r in rows
                            if r["pre_test_vol_regime"] == vol_regime
                            and r["pre_test_structure_regime"] == structure_regime
                        ]
                    ),
                }

        direction_groups = {
            direction: evaluation_summary(
                [r for r in rows if r["pre_test_trend_direction"] == direction]
            )
            for direction in ("up", "down", "flat")
        }

        combined_summary[geometry] = {
            "evaluation_count": len(rows),
            "combined_regimes": by_combined,
            "trend_direction": direction_groups,
        }

    migration_summary = {
        "transition_count": len(transitions),
        "migration_count": sum(bool(r["migration"]) for r in transitions),
        "stable_count": sum(not bool(r["migration"]) for r in transitions),
        "migration_rate": (
            sum(bool(r["migration"]) for r in transitions) / len(transitions)
            if transitions
            else 0.0
        ),
        "by_destination_combined_regime": {},
        "by_volatility_shift": {},
        "by_structure_shift": {},
        "parameter_associations": {},
    }

    for vol_regime in ("low", "middle", "high"):
        for structure_regime in ("choppy", "mixed", "trending"):
            label = f"{vol_regime}__{structure_regime}"
            matching = [
                r
                for r in transitions
                if r["destination_vol_regime"] == vol_regime
                and r["destination_structure_regime"] == structure_regime
            ]
            migration_summary["by_destination_combined_regime"][label] = (
                transition_summary(matching)
            )

    shift_groups = {
        "contracting": lambda value: value < -0.10,
        "stable_band": lambda value: -0.10 <= value <= 0.10,
        "expanding": lambda value: value > 0.10,
    }
    for label, predicate in shift_groups.items():
        migration_summary["by_volatility_shift"][label] = transition_summary(
            [r for r in transitions if predicate(r["volatility_percentile_delta"])]
        )
        migration_summary["by_structure_shift"][label] = transition_summary(
            [r for r in transitions if predicate(r["structure_percentile_delta"])]
        )

    parameters = (
        "risk_per_trade",
        "leverage",
        "momentum.lookback",
        "mean_reversion.window",
        "mean_reversion.threshold",
    )
    for parameter in parameters:
        changed = [
            r for r in transitions if parameter in r["changed_parameters"]
        ]
        unchanged = [
            r for r in transitions if parameter not in r["changed_parameters"]
        ]
        migration_summary["parameter_associations"][parameter] = {
            "change_count": len(changed),
            "changed_median_volatility_delta": (
                statistics.median(
                    r["volatility_percentile_delta"] for r in changed
                )
                if changed
                else None
            ),
            "changed_median_structure_delta": (
                statistics.median(
                    r["structure_percentile_delta"] for r in changed
                )
                if changed
                else None
            ),
            "changed_positive_destination_rate": (
                sum(r["destination_positive_profit"] for r in changed) / len(changed)
                if changed
                else 0.0
            ),
            "changed_pf_pass_rate": (
                sum(
                    not r["destination_profit_factor_failure"]
                    for r in changed
                )
                / len(changed)
                if changed
                else 0.0
            ),
            "unchanged_positive_destination_rate": (
                sum(r["destination_positive_profit"] for r in unchanged)
                / len(unchanged)
                if unchanged
                else 0.0
            ),
            "unchanged_pf_pass_rate": (
                sum(
                    not r["destination_profit_factor_failure"]
                    for r in unchanged
                )
                / len(unchanged)
                if unchanged
                else 0.0
            ),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "rolling_joint_regime_trend_choppiness_analysis",
        "source_diagnostic_fingerprint": rolling["diagnostic_fingerprint"],
        "source_code_version": rolling["code_version"],
        "source_target_count": rolling["target_count"],
        "source_research_candle_count": rolling["research_candle_count"],
        "source_universe": rolling["universe"],
        "volatility_definition": {
            "lookback_days": VOL_LOOKBACK,
            "annualization": 252,
            "regime_method": (
                "historical percentile using only observations strictly before each test start"
            ),
            "boundaries": {"low_below": LOW, "high_above": HIGH},
        },
        "structure_definition": {
            "lookback_days": STRUCTURE_LOOKBACK,
            "metric": (
                "directional efficiency = abs(sum(log returns)) / "
                "sum(abs(log returns))"
            ),
            "interpretation": (
                "low efficiency is choppy; high efficiency is trend-like"
            ),
            "regime_method": (
                "historical percentile using only observations strictly before each test start"
            ),
            "boundaries": {"choppy_below": LOW, "trending_above": HIGH},
            "trend_direction": "sign of 60-day log-return sum",
        },
        "archive_integrity": integrity,
        "market_feature_count": len(market),
        "market_features": market,
        "evaluation_count": len(evaluations),
        "regime_summary": combined_summary,
        "migration_summary": migration_summary,
        "transitions": transitions,
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
        "safety": rolling["safety"],
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
        "# Rolling-WF Kombinierte Regime-/Trend-/Choppiness-Analyse",
        "",
        f"- Analysis-Fingerprint: {result['analysis_fingerprint']}",
        f"- Source-Fingerprint: {result['source_diagnostic_fingerprint']}",
        f"- Research-Candles: {result['source_research_candle_count']}",
        "- Basis: immutable archivierte Rohdaten; keine neuen Downloads, Backtests oder Optimierungen",
        "",
        "## Gemeinsame Volatilitäts- und Strukturregime",
        "",
        "| Geometrie | Volatilität | Struktur | Evaluationen | positive Ergebnisse | PF-Pass | Median Profit EUR |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for geometry, section in result["regime_summary"].items():
        for data in section["combined_regimes"].values():
            lines.append(
                f"| {geometry} | {data['vol_regime']} | {data['structure_regime']} | "
                f"{data['evaluation_count']} | {data['positive_profit_rate']:.3f} | "
                f"{data['pf_pass_rate']:.3f} | {fmt(data['median_profit_eur'])} |"
            )

    lines += [
        "",
        "## Trendrichtung",
        "",
        "| Geometrie | Richtung | Evaluationen | positive Ergebnisse | PF-Pass | Median Profit EUR |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for geometry, section in result["regime_summary"].items():
        for direction, data in section["trend_direction"].items():
            lines.append(
                f"| {geometry} | {direction} | {data['evaluation_count']} | "
                f"{data['positive_profit_rate']:.3f} | {data['pf_pass_rate']:.3f} | "
                f"{fmt(data['median_profit_eur'])} |"
            )

    lines += [
        "",
        "## Kandidatenmigration nach Marktstruktur",
        "",
        "| Zielregime | Transitions | Migrationen | Migration-Rate | positive Destinationen | PF-Pass | Median Profit EUR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, data in result["migration_summary"][
        "by_destination_combined_regime"
    ].items():
        lines.append(
            f"| {label} | {data['transition_count']} | {data['migration_count']} | "
            f"{data['migration_rate']:.3f} | {data['positive_destination_rate']:.3f} | "
            f"{data['pf_pass_rate']:.3f} | {fmt(data['median_destination_profit_eur'])} |"
        )

    lines += [
        "",
        "## Strukturwechsel",
        "",
        "| Wechsel | Transitions | Migrationen | Migration-Rate | positive Destinationen | PF-Pass | Median Profit EUR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for category in ("contracting", "stable_band", "expanding"):
        data = result["migration_summary"]["by_structure_shift"][category]
        lines.append(
            f"| {category} | {data['transition_count']} | {data['migration_count']} | "
            f"{data['migration_rate']:.3f} | {data['positive_destination_rate']:.3f} | "
            f"{data['pf_pass_rate']:.3f} | {fmt(data['median_destination_profit_eur'])} |"
        )

    lines += [
        "",
        "## Parameterwechsel",
        "",
        "| Parameter | Änderung Count | Median Vol.-Delta | Median Struktur-Delta | positive Destinationen bei Änderung | PF-Pass bei Änderung |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for parameter, data in result["migration_summary"][
        "parameter_associations"
    ].items():
        lines.append(
            f"| {parameter} | {data['change_count']} | "
            f"{fmt(data['changed_median_volatility_delta'])} | "
            f"{fmt(data['changed_median_structure_delta'])} | "
            f"{data['changed_positive_destination_rate']:.3f} | "
            f"{data['changed_pf_pass_rate']:.3f} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "Volatilitäts- und Strukturregime werden je Teststart ausschließlich aus zuvor verfügbaren Beobachtungen gebildet.",
        "Die Auswertungen sind diagnostisch; sie beweisen keine Ursache und ändern keine Parameter, Selection-Profile oder Gates.",
        "Evaluationen über Selection-Profile wiederholen dieselben Marktfenster und sind daher keine unabhängigen Marktbeobachtungen.",
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
        "--output-dir", default="research/regime_trend_choppiness"
    )
    args = parser.parse_args()

    rolling = json.loads(Path(args.rolling_json).read_text(encoding="utf-8"))
    archive = json.loads(Path(args.archive_manifest).read_text(encoding="utf-8"))
    result = analyze(rolling, archive, args.raw_dir)

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "regime_trend_choppiness_analysis.json").write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    (output / "regime_trend_choppiness_analysis.md").write_text(
        markdown(result),
        encoding="utf-8",
    )

    print("REGIME_TREND_CHOPPINESS_ANALYSIS: COMPLETED")
    print("ANALYSIS_FINGERPRINT:", result["analysis_fingerprint"])
    print("EVALUATIONS:", result["evaluation_count"])
    print("MARKET_FEATURES:", result["market_feature_count"])
    print("TRANSITIONS:", len(result["transitions"]))
    print("PAPER_ONLY:", result["safety"]["paper_only"])
    print(
        "LIVE_TRADING_ENABLED:",
        result["safety"]["live_trading_enabled"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
