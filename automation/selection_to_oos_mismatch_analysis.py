"""Analyze Training-Selection to immediate Rolling-WF OOS mismatch."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

MIN_PROFIT_FACTOR = 1.10


def _safe_pf(value: Any) -> float:
    return float("inf") if value == "inf" else float(value)


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
    return hashlib.sha256(
        _canonical(value).encode("utf-8")
    ).hexdigest()


def _pearson(values_x: list[float], values_y: list[float]) -> float | None:
    if len(values_x) < 2 or len(values_x) != len(values_y):
        return None
    mean_x = statistics.mean(values_x)
    mean_y = statistics.mean(values_y)
    centered_x = [value - mean_x for value in values_x]
    centered_y = [value - mean_y for value in values_y]
    denominator = math.sqrt(
        sum(value * value for value in centered_x)
        * sum(value * value for value in centered_y)
    )
    if denominator == 0.0:
        return None
    return sum(
        x * y for x, y in zip(centered_x, centered_y)
    ) / denominator


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(
        range(len(values)),
        key=lambda index: (values[index], index),
    )
    ranks = [0.0] * len(values)
    start = 0

    while start < len(order):
        end = start + 1
        value = values[order[start]]
        while end < len(order) and values[order[end]] == value:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        for position in range(start, end):
            ranks[order[position]] = average_rank
        start = end

    return ranks


def _spearman(values_x: list[float], values_y: list[float]) -> float | None:
    ranks_x = _average_ranks(values_x)
    ranks_y = _average_ranks(values_y)
    return _pearson(ranks_x, ranks_y)


def _rank_percentile(rank: int, count: int) -> float:
    if count <= 1:
        return 1.0
    return 1.0 - ((rank - 1) / (count - 1))


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "evaluation_count": 0,
            "unique_market_windows": 0,
            "positive_oos_rate": 0.0,
            "pf_pass_rate": 0.0,
            "median_oos_profit_eur": None,
            "median_training_profit_eur": None,
            "median_raw_score_rank": None,
            "median_selection_score": None,
            "median_runner_up_score_gap": None,
            "median_selected_vs_best_raw_score_gap": None,
        }

    market_windows = {
        (row["symbol"], row["geometry"], row["window_index"])
        for row in rows
    }
    return {
        "evaluation_count": len(rows),
        "unique_market_windows": len(market_windows),
        "positive_oos_rate": sum(
            row["oos_positive"] for row in rows
        ) / len(rows),
        "pf_pass_rate": sum(
            row["oos_pf_pass"] for row in rows
        ) / len(rows),
        "median_oos_profit_eur": statistics.median(
            float(row["oos_profit_eur"]) for row in rows
        ),
        "median_training_profit_eur": statistics.median(
            float(row["training_profit_eur"]) for row in rows
        ),
        "median_raw_score_rank": statistics.median(
            int(row["raw_score_rank"]) for row in rows
        ),
        "median_selection_score": statistics.median(
            float(row["selection_score"]) for row in rows
        ),
        "median_runner_up_score_gap": statistics.median(
            float(row["runner_up_score_gap"])
            for row in rows
            if row["runner_up_score_gap"] is not None
        ) if any(
            row["runner_up_score_gap"] is not None for row in rows
        ) else None,
        "median_selected_vs_best_raw_score_gap": statistics.median(
            float(row["selected_vs_best_raw_score_gap"]) for row in rows
        ),
    }


def _correlations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    mappings = {
        "raw_score_rank_vs_oos_profit": (
            lambda row: float(row["raw_score_rank"])
        ),
        "selection_score_vs_oos_profit": (
            lambda row: float(row["selection_score"])
        ),
        "runner_up_score_gap_vs_oos_profit": (
            lambda row: row["runner_up_score_gap"]
        ),
        "selected_vs_best_raw_score_gap_vs_oos_profit": (
            lambda row: float(row["selected_vs_best_raw_score_gap"])
        ),
        "training_profit_vs_oos_profit": (
            lambda row: float(row["training_profit_eur"])
        ),
        "training_return_vs_oos_return": (
            lambda row: float(row["training_return_percent"])
        ),
        "training_profit_factor_vs_oos_profit": (
            lambda row: _safe_pf(row["training_profit_factor"])
        ),
        "training_trade_count_vs_oos_profit": (
            lambda row: float(row["training_trade_count"])
        ),
    }
    result = {}
    for name, getter in mappings.items():
        pairs = [
            (getter(row), float(row["oos_profit_eur"]))
            for row in rows
            if getter(row) is not None
            and math.isfinite(float(getter(row)))
            and math.isfinite(float(row["oos_profit_eur"]))
        ]
        x = [pair[0] for pair in pairs]
        y = [pair[1] for pair in pairs]
        result[name] = {
            "n": len(pairs),
            "pearson": _pearson(x, y),
            "spearman": _spearman(x, y),
        }
    return result


def _mismatch_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = {
        "training_positive__oos_positive": 0,
        "training_positive__oos_nonpositive": 0,
        "training_nonpositive__oos_positive": 0,
        "training_nonpositive__oos_nonpositive": 0,
    }
    for row in rows:
        training_positive = row["training_positive"]
        oos_positive = row["oos_positive"]
        if training_positive and oos_positive:
            key = "training_positive__oos_positive"
        elif training_positive and not oos_positive:
            key = "training_positive__oos_nonpositive"
        elif not training_positive and oos_positive:
            key = "training_nonpositive__oos_positive"
        else:
            key = "training_nonpositive__oos_nonpositive"
        buckets[key] += 1

    total = len(rows)
    return {
        key: {
            "count": count,
            "rate": count / total if total else 0.0,
        }
        for key, count in buckets.items()
    }


def _rank_bands(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []

    count = rows[0]["selection_candidate_count"]
    bands = (
        ("top_1_percent", 1, max(1, math.ceil(count * 0.01))),
        ("top_5_percent_excl_top_1", max(2, math.ceil(count * 0.01) + 1), math.ceil(count * 0.05)),
        ("top_10_percent_excl_top_5", math.ceil(count * 0.05) + 1, math.ceil(count * 0.10)),
        ("above_top_10_percent", math.ceil(count * 0.10) + 1, count),
    )
    result = []
    for label, low, high in bands:
        band = [row for row in rows if low <= row["raw_score_rank"] <= high]
        summary = _summary(band)
        result.append(
            {
                "band": label,
                "rank_min": low,
                "rank_max": high,
                **summary,
            }
        )
    return result


def _collect(control: dict[str, Any]) -> list[dict[str, Any]]:
    if control.get("diagnostic_type") != "rolling_selection_to_oos_control":
        raise ValueError("Unexpected Selection-to-OOS control type.")
    if control.get("universe") != "benchmark":
        raise ValueError("Unexpected Selection-to-OOS universe.")
    if int(control.get("target_count", 0)) != 5000:
        raise ValueError("Unexpected target count.")
    if int(control.get("research_candle_count", 0)) != 4500:
        raise ValueError("Unexpected research length.")

    safety = control.get("safety", {})
    if safety.get("paper_only") is not True:
        raise ValueError("Paper-Only safety flag is not enabled.")
    if safety.get("live_trading_enabled") is not False:
        raise ValueError("Live trading must remain disabled.")
    if safety.get("orders_enabled") is not False:
        raise ValueError("Orders must remain disabled.")

    rows = []
    for dataset in control["datasets"]:
        for profile in dataset["profiles"]:
            profile_name = profile["selection_profile"]
            for geometry in ("small", "large"):
                for window in profile[geometry]["windows"]:
                    selection = window.get("selection")
                    training = window.get("training")
                    if not isinstance(selection, dict) or not isinstance(training, dict):
                        raise ValueError("Selection-/Training-Metadaten fehlen.")
                    rank = int(selection["raw_score_rank"])
                    candidate_count = int(selection["candidate_count"])
                    if not 1 <= rank <= candidate_count:
                        raise ValueError("Ungültiger Raw-Score-Rang.")
                    if selection["profile_rank"] != 1:
                        raise ValueError("Profil-Rang des ausgewählten Kandidaten muss 1 sein.")

                    oos_profit = float(window["net_profit_eur"])
                    oos_pf = _safe_pf(window["profit_factor"])
                    training_profit = float(training["net_profit_eur"])
                    rows.append(
                        {
                            "symbol": dataset["symbol"],
                            "interval": dataset["interval"],
                            "selection_profile": profile_name,
                            "geometry": geometry,
                            "window_index": int(window["window_index"]),
                            "candidate_fingerprint": window["candidate_fingerprint"],
                            "selection_candidate_count": candidate_count,
                            "selection_score": float(selection["score"]),
                            "runner_up_score_gap": (
                                None
                                if selection["runner_up_score_gap"] is None
                                else float(selection["runner_up_score_gap"])
                            ),
                            "raw_score_rank": rank,
                            "raw_score_rank_percentile": _rank_percentile(
                                rank, candidate_count
                            ),
                            "selected_vs_best_raw_score_gap": float(
                                selection["selected_vs_best_raw_score_gap"]
                            ),
                            "training_profit_eur": training_profit,
                            "training_return_percent": float(training["return_percent"]),
                            "training_profit_factor": training["profit_factor"],
                            "training_max_drawdown_percent": float(
                                training["max_drawdown_percent"]
                            ),
                            "training_trade_count": int(training["trade_count"]),
                            "training_positive": training_profit > 0.0,
                            "training_pf_pass": _safe_pf(
                                training["profit_factor"]
                            ) >= MIN_PROFIT_FACTOR,
                            "oos_profit_eur": oos_profit,
                            "oos_return_percent": float(window["return_percent"]),
                            "oos_profit_factor": oos_pf,
                            "oos_positive": oos_profit > 0.0,
                            "oos_pf_pass": oos_pf >= MIN_PROFIT_FACTOR,
                        }
                    )

    return rows


def analyze(control: dict[str, Any], archive_manifest: dict[str, Any]) -> dict[str, Any]:
    archive_fp = archive_manifest.get("manifest_fingerprint")
    if archive_fp != control.get("source_manifest_fingerprint"):
        raise ValueError("Control- und Archive-Manifest-Fingerprint stimmen nicht überein.")

    rows = _collect(control)
    by_profile = defaultdict(list)
    by_asset_geometry = defaultdict(list)

    for row in rows:
        by_profile[row["selection_profile"]].append(row)
        by_asset_geometry[
            (row["symbol"], row["geometry"])
        ].append(row)

    market_windows = defaultdict(list)
    for row in rows:
        market_windows[
            (row["symbol"], row["geometry"], row["window_index"])
        ].append(row)

    balanced_rows = []
    for key, grouped in market_windows.items():
        balanced_rows.append(
            {
                "symbol": key[0],
                "geometry": key[1],
                "window_index": key[2],
                "raw_score_rank": statistics.mean(
                    row["raw_score_rank"] for row in grouped
                ),
                "selection_score": statistics.mean(
                    row["selection_score"] for row in grouped
                ),
                "runner_up_score_gap": statistics.mean(
                    row["runner_up_score_gap"]
                    for row in grouped
                    if row["runner_up_score_gap"] is not None
                ) if any(
                    row["runner_up_score_gap"] is not None
                    for row in grouped
                ) else None,
                "selected_vs_best_raw_score_gap": statistics.mean(
                    row["selected_vs_best_raw_score_gap"] for row in grouped
                ),
                "training_profit_eur": statistics.mean(
                    row["training_profit_eur"] for row in grouped
                ),
                "training_return_percent": statistics.mean(
                    row["training_return_percent"] for row in grouped
                ),
                "training_profit_factor": statistics.mean(
                    _safe_pf(row["training_profit_factor"])
                    for row in grouped
                    if math.isfinite(_safe_pf(row["training_profit_factor"]))
                ) if any(
                    math.isfinite(_safe_pf(row["training_profit_factor"]))
                    for row in grouped
                ) else 0.0,
                "training_trade_count": statistics.mean(
                    row["training_trade_count"] for row in grouped
                ),
                "oos_profit_eur": statistics.mean(
                    row["oos_profit_eur"] for row in grouped
                ),
            }
        )

    result = {
        "schema_version": 1,
        "diagnostic_type": "rolling_selection_to_oos_mismatch_analysis",
        "source_control_fingerprint": control["diagnostic_fingerprint"],
        "source_manifest_fingerprint": archive_fp,
        "source_diagnostic_fingerprint": control[
            "source_diagnostic_fingerprint"
        ],
        "evaluation_count": len(rows),
        "unique_market_window_count": len(market_windows),
        "mismatch_matrix": _mismatch_matrix(rows),
        "all_evaluations": {
            "summary": _summary(rows),
            "correlations": _correlations(rows),
            "raw_score_rank_bands": _rank_bands(rows),
        },
        "market_window_balanced": {
            "summary": {
                "evaluation_count": len(balanced_rows),
                "unique_market_windows": len(balanced_rows),
                "median_oos_profit_eur": statistics.median(
                    row["oos_profit_eur"] for row in balanced_rows
                ) if balanced_rows else None,
            },
            "correlations": _correlations(balanced_rows),
        },
        "by_selection_profile": {
            profile: {
                "summary": _summary(profile_rows),
                "correlations": _correlations(profile_rows),
                "mismatch_matrix": _mismatch_matrix(profile_rows),
            }
            for profile, profile_rows in sorted(by_profile.items())
        },
        "by_asset_geometry": {
            f"{symbol}|{geometry}": {
                "summary": _summary(group_rows),
                "correlations": _correlations(group_rows),
                "mismatch_matrix": _mismatch_matrix(group_rows),
            }
            for (symbol, geometry), group_rows in sorted(
                by_asset_geometry.items()
            )
        },
        "interpretation_scope": {
            "diagnostic_only": True,
            "raw_score_rank_is_independent_of_selection_profile": True,
            "profile_rank_is_one_by_definition": True,
            "runner_up_gap_uses_profile_ordering": True,
            "oos_is_never_used_for_selection": True,
            "four_profiles_reuse_the_same_market_windows": True,
            "market_window_balanced_view_is_descriptive": True,
            "correlations_are_descriptive_not_causal": True,
            "rank_bands_are_descriptive_not_selection_rules": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
        "rows": rows,
    }

    result = _json_safe(result)
    result["analysis_fingerprint"] = _fingerprint(result)
    return result


def markdown(result: dict[str, Any]) -> str:
    overall = result["all_evaluations"]["summary"]
    corr = result["all_evaluations"]["correlations"]
    mismatch = result["mismatch_matrix"]

    def fmt(value: Any) -> str:
        return "n/a" if value is None else f"{float(value):.4f}"

    lines = [
        "# Selection-to-OOS-Mismatch-Analyse",
        "",
        f"- Analysis-Fingerprint: {result['analysis_fingerprint']}",
        f"- Control-Fingerprint: {result['source_control_fingerprint']}",
        f"- Source Rolling-Control-Fingerprint: {result['source_diagnostic_fingerprint']}",
        f"- Evaluationen: {result['evaluation_count']}",
        f"- eindeutige Marktfenster: {result['unique_market_window_count']}",
        "",
        "## Gesamtbefund",
        "",
        f"- positive OOS-Fenster: {overall['positive_oos_rate']:.3f}",
        f"- PF-Pass: {overall['pf_pass_rate']:.3f}",
        f"- Median OOS-Profit EUR: {fmt(overall['median_oos_profit_eur'])}",
        f"- Median Training-Profit EUR: {fmt(overall['median_training_profit_eur'])}",
        f"- Median Raw-Score-Rang: {overall['median_raw_score_rank']}",
        "",
        "## Selection-vs.-OOS-Korrelationen",
        "",
        "| Merkmal | n | Pearson | Spearman |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, item in corr.items():
        lines.append(
            f"| {name} | {item['n']} | {fmt(item['pearson'])} | {fmt(item['spearman'])} |"
        )

    lines += [
        "",
        "## Training-positiv vs. OOS-positiv",
        "",
        "| Beziehung | Anzahl | Quote |",
        "| --- | ---: | ---: |",
    ]
    for key, item in mismatch.items():
        lines.append(
            f"| {key} | {item['count']} | {item['rate']:.3f} |"
        )

    lines += [
        "",
        "## Raw-Score-Rang-Bänder",
        "",
        "| Band | Rang | n | positive OOS | PF-Pass | Median OOS-Profit EUR | Median Training-Profit EUR |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for band in result["all_evaluations"]["raw_score_rank_bands"]:
        lines.append(
            f"| {band['band']} | {band['rank_min']}-{band['rank_max']} | "
            f"{band['evaluation_count']} | {band['positive_oos_rate']:.3f} | "
            f"{band['pf_pass_rate']:.3f} | {fmt(band['median_oos_profit_eur'])} | "
            f"{fmt(band['median_training_profit_eur'])} |"
        )

    lines += [
        "",
        "## Selection-Profile",
        "",
        "| Profil | Evaluationen | Marktfenster | Median Raw-Score-Rang | positive OOS | PF-Pass | Median OOS-Profit EUR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for profile, item in result["by_selection_profile"].items():
        summary = item["summary"]
        lines.append(
            f"| {profile} | {summary['evaluation_count']} | "
            f"{summary['unique_market_windows']} | {summary['median_raw_score_rank']} | "
            f"{summary['positive_oos_rate']:.3f} | {summary['pf_pass_rate']:.3f} | "
            f"{fmt(summary['median_oos_profit_eur'])} |"
        )

    lines += [
        "",
        "## Asset x Geometrie",
        "",
        "| Gruppe | Evaluationen | Marktfenster | Median Raw-Score-Rang | positive OOS | PF-Pass | Median OOS-Profit EUR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, item in result["by_asset_geometry"].items():
        summary = item["summary"]
        lines.append(
            f"| {key} | {summary['evaluation_count']} | "
            f"{summary['unique_market_windows']} | {summary['median_raw_score_rank']} | "
            f"{summary['positive_oos_rate']:.3f} | {summary['pf_pass_rate']:.3f} | "
            f"{fmt(summary['median_oos_profit_eur'])} |"
        )

    lines += [
        "",
        "## Methodische Einordnung",
        "",
        "Der Profil-Rang ist für den ausgewählten Kandidaten definitionsgemäß 1 und daher nicht als Qualitätsvariable interpretierbar.",
        "Der Raw-Score-Rang bewertet denselben ausgewählten Kandidaten unabhängig vom Selection-Profil innerhalb aller Trainingskandidaten.",
        "Die vier Profile teilen dieselben 60 Marktfenster; die 240 Evaluationen sind daher keine 240 unabhängigen Marktbeobachtungen.",
        "Die Korrelationen und Rang-Bänder sind deskriptiv und werden nicht als neue Selection-Regel verwendet.",
        "",
        "Paper-Only: True; Live-Trading: False; Orders: False.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-json", required=True)
    parser.add_argument("--archive-manifest", required=True)
    parser.add_argument(
        "--output-dir",
        default="research/selection_to_oos_mismatch",
    )
    args = parser.parse_args()

    control = json.loads(
        Path(args.control_json).read_text(encoding="utf-8")
    )
    archive_manifest = json.loads(
        Path(args.archive_manifest).read_text(encoding="utf-8")
    )
    result = analyze(control, archive_manifest)

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "selection_to_oos_mismatch_analysis.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    (output / "selection_to_oos_mismatch_analysis.md").write_text(
        markdown(result),
        encoding="utf-8",
    )
    print("SELECTION_TO_OOS_MISMATCH: COMPLETED")
    print("ANALYSIS_FINGERPRINT:", result["analysis_fingerprint"])
    print("EVALUATIONS:", result["evaluation_count"])
    print("UNIQUE_MARKET_WINDOWS:", result["unique_market_window_count"])
    print("PAPER_ONLY:", result["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", result["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
