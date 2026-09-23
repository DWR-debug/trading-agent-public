"""Training-only Selection-Stability Control.

Uses the existing immutable Selection-to-OOS control as the outer reference and
adds one internal 75%-training-prefix optimization per outer window/profile.
OOS is outcome-only and never participates in the stability metrics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
from pathlib import Path
from typing import Any

from automation.horizon_decomposition import _candidate
from automation.verify_rolling_raw_archive import verify as verify_raw_archive
from config.parameter_space import ParameterSpace
from data.market_store import MarketDataStore
from optimization.optimizer import Optimizer
from optimization.selection_profiles import (
    available_selection_profile_names,
    get_selection_profile,
)
from research.protocol import dataset_fingerprint


TARGET_COUNT = 5000
RESEARCH_END = 4500
SMALL_TRAIN = 1125
LARGE_TRAIN = 2250
PREFIX_FRACTION = 0.75
MIN_INTERNAL_TRAIN = 500
EXPECTED_PROFILES = (
    "score_max",
    "boundary_averse",
    "risk_averse",
    "trade_rich",
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        if math.isnan(value):
            return None
    return value


def _canonical(value: object) -> str:
    return json.dumps(
        _json_safe(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _candidate_fp(candidate: dict[str, Any]) -> str:
    return _fingerprint(candidate)


def _candidate_key(candidate: dict[str, Any]) -> tuple:
    return (
        int(candidate["strategy"]["momentum"]["lookback"]),
        int(candidate["strategy"]["mean_reversion"]["window"]),
        float(candidate["strategy"]["mean_reversion"]["threshold"]),
        float(candidate["risk_per_trade"]),
        float(candidate["leverage"]),
    )


def _parameter_distance(
    first: dict[str, Any],
    second: dict[str, Any],
) -> float:
    a = _candidate_key(first)
    b = _candidate_key(second)
    return sum(x != y for x, y in zip(a, b)) / len(a)


def _raw_rank(results, target_fp: str) -> tuple[int, float, float]:
    target = next(
        result for result in results
        if _candidate_fp(_candidate(result.candidate)) == target_fp
    )
    better = sum(result.score > target.score for result in results)
    best_score = max(result.score for result in results)
    return (
        1 + better,
        target.score - best_score,
        target.score,
    )


def _profile_rank(results, target_fp: str) -> int:
    for index, result in enumerate(results, start=1):
        if _candidate_fp(_candidate(result.candidate)) == target_fp:
            return index
    raise ValueError("Outer-Selected-Kandidat fehlt im internen Optimizer-Ergebnis.")


def _runner_up_gap(results, target_fp: str) -> float | None:
    position = None
    for index, result in enumerate(results):
        if _candidate_fp(_candidate(result.candidate)) == target_fp:
            position = index
            break
    if position is None:
        raise ValueError("Outer-Selected-Kandidat fehlt in der Profil-Reihenfolge.")
    if position + 1 >= len(results):
        return None
    return results[position].score - results[position + 1].score


def _profile_order(results, profile: str, parameter_space: ParameterSpace):
    selection_profile = get_selection_profile(profile)
    return sorted(
        results,
        key=lambda result: selection_profile.rank_key(
            result,
            parameter_space,
        ),
        reverse=True,
    )


def _internal_metrics(results, target_fp: str) -> dict[str, Any]:
    raw_sorted = sorted(results, key=lambda result: result.score, reverse=True)
    rank, gap_to_best, target_score = _raw_rank(raw_sorted, target_fp)
    profile_rank = _profile_rank(results, target_fp)
    runner_up_gap = _runner_up_gap(results, target_fp)
    scores = [float(result.score) for result in results]
    median_score = statistics.median(scores)
    abs_dev = [abs(score - median_score) for score in scores]
    mad = statistics.median(abs_dev)

    return {
        "outer_selected_profile_rank": profile_rank,
        "outer_selected_raw_score_rank": rank,
        "outer_selected_raw_score_rank_percentile": (
            1.0 - ((rank - 1) / (len(results) - 1))
            if len(results) > 1
            else 1.0
        ),
        "outer_selected_score": target_score,
        "outer_selected_vs_best_raw_score_gap": gap_to_best,
        "outer_selected_runner_up_profile_score_gap": runner_up_gap,
        "raw_score_mad": mad,
        "normalized_runner_up_gap": (
            runner_up_gap / mad
            if runner_up_gap is not None and mad > 0
            else None
        ),
        "raw_top1_member": rank <= 1,
        "raw_top5_member": rank <= 5,
        "raw_top10_member": rank <= 10,
    }


def _analyze_window(
    *,
    candles,
    symbol: str,
    profile: str,
    geometry: str,
    window: dict[str, Any],
    parameter_space: ParameterSpace,
) -> dict[str, Any]:
    train_size = SMALL_TRAIN if geometry == "small" else LARGE_TRAIN
    internal_train_size = max(
        MIN_INTERNAL_TRAIN,
        math.ceil(train_size * PREFIX_FRACTION),
    )
    if internal_train_size >= train_size:
        raise ValueError("Interne Trainingsgröße muss kleiner als äußeres Training sein.")

    train_start = int(window["train_start_index"])
    train_end = int(window["train_end_index"])
    if train_end - train_start != train_size:
        raise ValueError("Outer-Trainingsgröße stimmt nicht mit der Geometrie überein.")

    outer_selected = window["candidate"]
    target_fp = window["candidate_fingerprint"]

    internal_candles = candles[train_start:train_start + internal_train_size]
    optimizer = Optimizer(
        candles=tuple(internal_candles),
        symbol=symbol,
        parameter_space=parameter_space,
    )
    all_results = optimizer.optimize(top_n=parameter_space.size())
    results = _profile_order(all_results, profile, parameter_space)

    internal_selected = _candidate(results[0].candidate)
    internal_selected_fp = _candidate_fp(internal_selected)
    internal_metrics = _internal_metrics(results, target_fp)

    return {
        "symbol": symbol,
        "selection_profile": profile,
        "geometry": geometry,
        "window_index": int(window["window_index"]),
        "outer_train_size": train_size,
        "internal_train_size": internal_train_size,
        "internal_prefix_fraction": PREFIX_FRACTION,
        "outer_train_start_index": train_start,
        "outer_train_end_index": train_end,
        "outer_selected_candidate": outer_selected,
        "outer_selected_candidate_fingerprint": target_fp,
        "internal_selected_candidate": internal_selected,
        "internal_selected_candidate_fingerprint": internal_selected_fp,
        "selected_candidate_persists": internal_selected_fp == target_fp,
        "parameter_distance_internal_vs_outer_selected": _parameter_distance(
            internal_selected,
            outer_selected,
        ),
        **internal_metrics,
        "oos_profit_eur": window["net_profit_eur"],
        "oos_positive": (
            float(window["net_profit_eur"]) > 0.0
            if window["net_profit_eur"] is not None
            else False
        ),
        "oos_profit_factor": window["profit_factor"],
        "oos_pf_pass": (
            window["profit_factor"] == "inf"
            or float(window["profit_factor"]) >= 1.10
        ),
    }


def _safe_mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"evaluation_count": 0}

    persistence = [row["selected_candidate_persists"] for row in rows]
    distances = [row["parameter_distance_internal_vs_outer_selected"] for row in rows]
    raw_ranks = [row["outer_selected_raw_score_rank"] for row in rows]
    raw_percentiles = [
        row["outer_selected_raw_score_rank_percentile"] for row in rows
    ]
    stable_rows = [row for row in rows if row["selected_candidate_persists"]]

    def positive_rate(group):
        return (
            sum(row["oos_positive"] for row in group) / len(group)
            if group else None
        )

    return {
        "evaluation_count": len(rows),
        "unique_market_windows": len({
            (row["symbol"], row["geometry"], row["window_index"])
            for row in rows
        }),
        "candidate_persistence_rate": sum(persistence) / len(persistence),
        "median_parameter_distance": statistics.median(distances),
        "median_internal_raw_rank_of_outer_selected": statistics.median(raw_ranks),
        "median_internal_raw_percentile_of_outer_selected": statistics.median(
            raw_percentiles
        ),
        "stable_subset_count": len(stable_rows),
        "stable_subset_oos_positive_rate": positive_rate(stable_rows),
        "unstable_subset_count": len(rows) - len(stable_rows),
        "unstable_subset_oos_positive_rate": positive_rate(
            [row for row in rows if not row["selected_candidate_persists"]]
        ),
        "stable_subset_median_oos_profit_eur": (
            statistics.median(row["oos_profit_eur"] for row in stable_rows)
            if stable_rows else None
        ),
        "unstable_subset_median_oos_profit_eur": (
            statistics.median(
                row["oos_profit_eur"]
                for row in rows
                if not row["selected_candidate_persists"]
            )
            if len(stable_rows) < len(rows) else None
        ),
    }


def _correlation(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    pairs = [
        (float(row[key]), float(row["oos_profit_eur"]))
        for row in rows
        if row[key] is not None
        and row["oos_profit_eur"] is not None
        and math.isfinite(float(row[key]))
        and math.isfinite(float(row["oos_profit_eur"]))
    ]
    if len(pairs) < 2:
        return {"n": len(pairs), "pearson": None}

    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = math.sqrt(
        sum((x - mx) ** 2 for x in xs)
        * sum((y - my) ** 2 for y in ys)
    )
    return {"n": len(pairs), "pearson": num / den if den else None}


def _check_source(control: dict[str, Any]) -> None:
    if control.get("diagnostic_type") != "rolling_selection_to_oos_control":
        raise ValueError("Unexpected Selection-to-OOS control type.")
    if int(control.get("target_count", 0)) != TARGET_COUNT:
        raise ValueError("Unexpected target count.")
    if int(control.get("research_candle_count", 0)) != RESEARCH_END:
        raise ValueError("Unexpected research length.")
    if tuple(control.get("selection_profiles", ())) != EXPECTED_PROFILES:
        raise ValueError("Unexpected selection profile ordering.")

    safety = control.get("safety", {})
    if safety.get("paper_only") is not True:
        raise ValueError("Paper-Only safety flag is not enabled.")
    if safety.get("live_trading_enabled") is not False:
        raise ValueError("Live trading must remain disabled.")
    if safety.get("orders_enabled") is not False:
        raise ValueError("Orders must remain disabled.")


def analyze(
    control: dict[str, Any],
    *,
    data_dir: str | Path,
    archive_manifest_path: str | Path,
) -> dict[str, Any]:
    _check_source(control)

    archive = verify_raw_archive(
        archive_manifest_path,
        data_dir=data_dir,
        expected_count=TARGET_COUNT,
    )
    archive_by_symbol = {
        item["symbol"]: item["dataset_fingerprint"]
        for item in archive["datasets"]
    }

    store = MarketDataStore(base_dir=data_dir)
    parameter_space = ParameterSpace()
    if control["parameter_space"] != {
        "momentum_lookbacks": [3, 5, 8, 13, 21],
        "mean_reversion_windows": [5, 10, 20, 30],
        "mean_reversion_thresholds": [0.01, 0.02, 0.03, 0.05],
        "risk_per_trade_values": [0.0025, 0.005, 0.0075, 0.01],
        "leverage_values": [1.0, 1.5, 2.0, 3.0],
    }:
        raise ValueError("Parameterraum des Source-Controls weicht vom aktuellen Raum ab.")

    rows = []
    for dataset in control["datasets"]:
        symbol = dataset["symbol"]
        candles = tuple(store.load(symbol, dataset["interval"]))
        if len(candles) != TARGET_COUNT:
            raise ValueError(f"{symbol}: unerwartete Candle-Anzahl.")
        if dataset["full_data_fingerprint"] != archive_by_symbol[symbol]:
            raise ValueError(f"{symbol}: Dataset-Fingerprint mismatch.")
        research = candles[:RESEARCH_END]
        if dataset["research_fingerprint"] != dataset_fingerprint(research):
            raise ValueError(f"{symbol}: Research-Fingerprint mismatch.")

        for profile in dataset["profiles"]:
            profile_name = profile["selection_profile"]
            for geometry_name in ("small", "large"):
                geometry = profile[geometry_name]
                for window in geometry["windows"]:
                    rows.append(
                        _analyze_window(
                            candles=research,
                            symbol=symbol,
                            profile=profile_name,
                            geometry=(
                                "small" if geometry_name == "small" else "large"
                            ),
                            window=window,
                            parameter_space=parameter_space,
                        )
                    )

    by_profile = {}
    for profile in EXPECTED_PROFILES:
        group = [row for row in rows if row["selection_profile"] == profile]
        by_profile[profile] = {
            "summary": _summary(group),
            "correlations": {
                "parameter_distance_vs_oos_profit": _correlation(
                    group, "parameter_distance_internal_vs_outer_selected"
                ),
                "internal_raw_percentile_vs_oos_profit": _correlation(
                    group, "outer_selected_raw_score_rank_percentile"
                ),
                "normalized_runner_up_gap_vs_oos_profit": _correlation(
                    group, "normalized_runner_up_gap"
                ),
            },
        }

    by_asset_geometry = {}
    for symbol in sorted({row["symbol"] for row in rows}):
        for geometry in ("small", "large"):
            group = [
                row for row in rows
                if row["symbol"] == symbol and row["geometry"] == geometry
            ]
            by_asset_geometry[f"{symbol}|{geometry}"] = {
                "summary": _summary(group),
                "correlations": {
                    "parameter_distance_vs_oos_profit": _correlation(
                        group, "parameter_distance_internal_vs_outer_selected"
                    ),
                    "internal_raw_percentile_vs_oos_profit": _correlation(
                        group, "outer_selected_raw_score_rank_percentile"
                    ),
                    "normalized_runner_up_gap_vs_oos_profit": _correlation(
                        group, "normalized_runner_up_gap"
                    ),
                },
            }

    report = {
        "schema_version": 1,
        "diagnostic_type": "training_selection_stability_control",
        "generated_at": os.getenv("GITHUB_RUN_STARTED_AT") or "",
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "source_control_fingerprint": control["diagnostic_fingerprint"],
        "source_manifest_fingerprint": control["source_manifest_fingerprint"],
        "source_run_id": control["source_run_id"],
        "universe": "benchmark",
        "target_count": TARGET_COUNT,
        "research_candle_count": RESEARCH_END,
        "outer_window_count": len(rows),
        "profile_count": len(EXPECTED_PROFILES),
        "prefix_fraction": PREFIX_FRACTION,
        "internal_train_minimum": MIN_INTERNAL_TRAIN,
        "parameter_space": control["parameter_space"],
        "summary": _summary(rows),
        "by_selection_profile": by_profile,
        "by_asset_geometry": by_asset_geometry,
        "interpretation_scope": {
            "diagnostic_only": True,
            "training_only_stability_metrics": True,
            "oos_is_outcome_only": True,
            "no_new_selection_rule": True,
            "no_parameter_space_change": True,
            "no_gate_change": True,
            "same_outer_windows_as_source_control": True,
            "single_internal_prefix_for_efficiency": True,
            "one_internal_1280_candidate_evaluation_per_market_window": True,
            "profile_comparison_reuses_same_internal_candidate_evaluations": True,
            "75_percent_prefix_is_anchored_at_outer_train_start": True,
            "correlations_are_descriptive_not_causal": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
        "rows": rows,
    }
    report["diagnostic_fingerprint"] = _fingerprint(report)
    return _json_safe(report)


def markdown(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# Training-only Selection-Stability-Control",
        "",
        f"- Diagnostic-Fingerprint: {report['diagnostic_fingerprint']}",
        f"- Source-Control-Fingerprint: {report['source_control_fingerprint']}",
        f"- Outer Evaluations: {report['outer_window_count']}",
        f"- Prefix-Fraction: {report['prefix_fraction']:.2f}",
        "",
        "## Gesamt",
        "",
        f"- Kandidaten-Persistenz: {s['candidate_persistence_rate']:.3f}",
        f"- Median Parameter-Distanz: {s['median_parameter_distance']:.3f}",
        f"- Median interner Raw-Rang des Outer-Selected-Kandidaten: {s['median_internal_raw_rank_of_outer_selected']}",
        f"- Median interne Raw-Rang-Perzentile: {s['median_internal_raw_percentile_of_outer_selected']:.3f}",
        f"- stabile Fälle: {s['stable_subset_count']}",
        f"- instabile Fälle: {s['unstable_subset_count']}",
        f"- OOS-positive Rate bei stabilen Fällen: {s['stable_subset_oos_positive_rate']:.3f}",
        f"- OOS-positive Rate bei instabilen Fällen: {s['unstable_subset_oos_positive_rate'] if s['unstable_subset_oos_positive_rate'] is not None else 'n/a'}",
        f"- Median OOS-Profit stabile Fälle: {s['stable_subset_median_oos_profit_eur']}",
        f"- Median OOS-Profit instabile Fälle: {s['unstable_subset_median_oos_profit_eur']}",
        "",
        "## Selection-Profile",
        "",
        "| Profil | Evaluationen | Persistenz | Median Param.-Distanz | Median interner Raw-Rang | OOS positiv stabil | OOS positiv instabil |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for profile, item in report["by_selection_profile"].items():
        x = item["summary"]
        stable_rate = x["stable_subset_oos_positive_rate"]
        unstable_rate = x["unstable_subset_oos_positive_rate"]
        lines.append(
            f"| {profile} | {x['evaluation_count']} | "
            f"{x['candidate_persistence_rate']:.3f} | "
            f"{x['median_parameter_distance']:.3f} | "
            f"{x['median_internal_raw_rank_of_outer_selected']} | "
            f"{stable_rate if stable_rate is not None else 'n/a'} | "
            f"{unstable_rate if unstable_rate is not None else 'n/a'} |"
        )

    lines += [
        "",
        "## Asset x Geometrie",
        "",
        "| Gruppe | Fenster | Persistenz | Median Param.-Distanz | OOS positiv stabil | OOS positiv instabil |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, item in report["by_asset_geometry"].items():
        x = item["summary"]
        lines.append(
            f"| {key} | {x['evaluation_count']} | {x['candidate_persistence_rate']:.3f} | "
            f"{x['median_parameter_distance']:.3f} | "
            f"{x['stable_subset_oos_positive_rate'] if x['stable_subset_oos_positive_rate'] is not None else 'n/a'} | "
            f"{x['unstable_subset_oos_positive_rate'] if x['unstable_subset_oos_positive_rate'] is not None else 'n/a'} |"
        )

    lines += [
        "",
        "## Korrelationen",
        "",
        "| Profil | Merkmal | n | Pearson |",
        "| --- | --- | ---: | ---: |",
    ]
    for profile, item in report["by_selection_profile"].items():
        for key, corr in item["correlations"].items():
            lines.append(
                f"| {profile} | {key} | {corr['n']} | "
                f"{corr['pearson'] if corr['pearson'] is not None else 'n/a'} |"
            )

    lines += [
        "",
        "## Methodische Einordnung",
        "",
        "Stabilität wird ausschließlich aus dem Training bestimmt: Der 75%-Prefix startet am selben Outer-Trainingsbeginn und endet vor dem Outer-Trainingsende.",
        "Der Outer-Selected-Kandidat wird auf dem internen Prefix gegen alle 1.280 Kandidaten bewertet; seine interne Ranglage wird anschließend rein diagnostisch mit dem unmittelbar folgenden OOS-Ergebnis verbunden.",
        "Die OOS-Daten werden nicht zur Auswahl verwendet.",
        "Korrelationen und stabile/instabile Teilgruppen sind deskriptiv; sie sind kein kausaler Nachweis und keine neue Selection-Regel.",
        "",
        "Paper-Only: True; Live-Trading: False; Orders: False.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-json", required=True)
    parser.add_argument("--archive-manifest", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", default="research/selection_stability")
    args = parser.parse_args()

    control = json.loads(Path(args.control_json).read_text(encoding="utf-8"))
    report = analyze(
        control,
        data_dir=args.data_dir,
        archive_manifest_path=args.archive_manifest,
    )

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "selection_stability_control.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    (output / "selection_stability_control.md").write_text(
        markdown(report),
        encoding="utf-8",
    )
    print("SELECTION_STABILITY_CONTROL: COMPLETED")
    print("DIAGNOSTIC_FINGERPRINT:", report["diagnostic_fingerprint"])
    print("EVALUATIONS:", report["outer_window_count"])
    print("PREFIX_FRACTION:", report["prefix_fraction"])
    print("PAPER_ONLY:", report["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", report["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
