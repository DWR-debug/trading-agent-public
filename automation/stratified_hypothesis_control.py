"""Strictly stratified hypothesis generation from the immutable matrix control.

Diagnostic only. This module never changes Selection, the parameter space,
gates, strategy code, or execution settings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

EXPECTED_DIAGNOSTIC_TYPE = "rolling_regime_parameter_failure_matrix"
EXPECTED_SOURCE_UNIVERSE = "benchmark"
EXPECTED_TARGET_COUNT = 5000
EXPECTED_RESEARCH_CANDLE_COUNT = 4500
EXPECTED_SOURCE_ANALYSIS_FINGERPRINT = (
    "9aa88bf691bfcfc94b5e4de5cbabae950a606af1d7a80645e61b3ab8be960f2f"
)
MIN_RECURRENT_OCCURRENCES = 3
MIN_PHASES = 2
MIN_REGIMES = 2
MIN_ASSETS = 2
PRIMARY_METRICS = ("positive_rate", "pf_pass_rate")
PARAMETERS = (
    "risk_per_trade",
    "leverage",
    "momentum.lookback",
    "mean_reversion.window",
    "mean_reversion.threshold",
)
EXPECTED_SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
}


def _pf(value: Any) -> float:
    if value == "inf":
        return math.inf
    return float(value)


def _value_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _fingerprint(report: dict[str, Any]) -> str:
    payload = {k: v for k, v in report.items() if k != "analysis_fingerprint"}
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_source(report: dict[str, Any]) -> None:
    if report.get("diagnostic_type") != EXPECTED_DIAGNOSTIC_TYPE:
        raise ValueError("Unexpected source diagnostic type.")
    if report.get("source_universe") != EXPECTED_SOURCE_UNIVERSE:
        raise ValueError("Unexpected source universe.")
    if int(report.get("source_target_count", 0)) != EXPECTED_TARGET_COUNT:
        raise ValueError("Unexpected source target count.")
    if int(report.get("source_research_candle_count", 0)) != EXPECTED_RESEARCH_CANDLE_COUNT:
        raise ValueError("Unexpected source research candle count.")
    if report.get("analysis_fingerprint") != EXPECTED_SOURCE_ANALYSIS_FINGERPRINT:
        raise ValueError("Unexpected source analysis fingerprint.")
    if report.get("safety") != EXPECTED_SAFETY:
        raise ValueError("Source safety contract is not Paper-Only.")
    scope = report.get("interpretation_scope", {})
    if scope.get("no_parameter_change") is not True:
        raise ValueError("Source permits a parameter change.")
    if scope.get("no_selection_rule") is not True:
        raise ValueError("Source permits a Selection change.")
    if scope.get("no_gate_change") is not True:
        raise ValueError("Source permits a Gate change.")


def _context(row: dict[str, Any]) -> tuple[str, str, str]:
    return row["selection_profile"], row["symbol"], row["geometry"]


def _regime(row: dict[str, Any]) -> tuple[str, str]:
    return row["pre_test_vol_regime"], row["pre_test_structure_regime"]


def _group_rows(rows: list[dict[str, Any]]) -> dict[tuple[tuple[str, str, str], str], list[dict[str, Any]]]:
    grouped: dict[tuple[tuple[str, str, str], str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(_context(row), row["candidate_signature"])].append(row)
    return grouped


def _stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    profits = [float(row["net_profit_eur"]) for row in rows]
    return {
        "occurrences": len(rows),
        "unique_market_windows": len({row["window_index"] for row in rows}),
        "phases": sorted({row["phase"] for row in rows}),
        "phase_count": len({row["phase"] for row in rows}),
        "regimes": sorted({_regime(row) for row in rows}),
        "regime_count": len({_regime(row) for row in rows}),
        "positive_rate": sum(row["net_profit_eur"] > 0 for row in rows) / len(rows),
        "pf_pass_rate": sum(_pf(row["profit_factor"]) >= 1.10 for row in rows) / len(rows),
        "median_profit_eur": statistics.median(profits),
    }


def _recurrent_groups(source: dict[str, Any]) -> dict[tuple[tuple[str, str, str], str], list[dict[str, Any]]]:
    signatures = {item["candidate_signature"] for item in source["recurrent_candidates"]}
    groups = _group_rows(source["rows"])
    out: dict[tuple[tuple[str, str, str], str], list[dict[str, Any]]] = {}
    for key, rows in groups.items():
        if key[1] not in signatures or len(rows) < MIN_RECURRENT_OCCURRENCES:
            continue
        summary = _stats(rows)
        if summary["phase_count"] < MIN_PHASES or summary["regime_count"] < MIN_REGIMES:
            continue
        out[key] = rows
    return out


def _single_parameter_contrasts(source: dict[str, Any]) -> list[dict[str, Any]]:
    groups = _recurrent_groups(source)
    by_context: dict[tuple[str, str, str], dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    for (context, signature), rows in groups.items():
        by_context[context][signature] = rows

    contrasts: list[dict[str, Any]] = []
    for context, candidates in sorted(by_context.items()):
        signatures = sorted(candidates)
        for left_sig_index, left_sig in enumerate(signatures):
            for right_sig in signatures[left_sig_index + 1 :]:
                left_rows = candidates[left_sig]
                right_rows = candidates[right_sig]
                left_values = left_rows[0]["parameter_values"]
                right_values = right_rows[0]["parameter_values"]
                differing = [
                    parameter
                    for parameter in PARAMETERS
                    if left_values[parameter] != right_values[parameter]
                ]
                if len(differing) != 1:
                    continue

                parameter = differing[0]
                left_key = _value_key(left_values[parameter])
                right_key = _value_key(right_values[parameter])
                if left_key <= right_key:
                    value_a = left_values[parameter]
                    value_b = right_values[parameter]
                    signature_a, signature_b = left_sig, right_sig
                    rows_a, rows_b = left_rows, right_rows
                else:
                    value_a = right_values[parameter]
                    value_b = left_values[parameter]
                    signature_a, signature_b = right_sig, left_sig
                    rows_a, rows_b = right_rows, left_rows

                contrasts.append(
                    {
                        "selection_profile": context[0],
                        "symbol": context[1],
                        "geometry": context[2],
                        "parameter": parameter,
                        "value_a": value_a,
                        "value_b": value_b,
                        "fixed_parameters": {
                            p: left_values[p] for p in PARAMETERS if p != parameter
                        },
                        "candidate_signature_a": signature_a,
                        "candidate_signature_b": signature_b,
                        "stats_a": _stats(rows_a),
                        "stats_b": _stats(rows_b),
                    }
                )
    return contrasts


def _cross_asset_candidates(contrasts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for contrast in contrasts:
        grouped[
            (
                contrast["selection_profile"],
                contrast["geometry"],
                contrast["parameter"],
                _value_key(contrast["value_a"]),
                _value_key(contrast["value_b"]),
                _value_key(contrast["fixed_parameters"]),
            )
        ].append(contrast)

    out: list[dict[str, Any]] = []
    for _, contexts in sorted(grouped.items(), key=lambda item: str(item[0])):
        contexts = sorted(contexts, key=lambda item: item["symbol"])
        per_asset: list[dict[str, Any]] = []
        eligible_contexts: list[dict[str, Any]] = []

        for item in contexts:
            stats_a, stats_b = item["stats_a"], item["stats_b"]
            delta_positive = stats_a["positive_rate"] - stats_b["positive_rate"]
            delta_pf = stats_a["pf_pass_rate"] - stats_b["pf_pass_rate"]
            delta_median = stats_a["median_profit_eur"] - stats_b["median_profit_eur"]

            if delta_positive > 0 and delta_pf > 0:
                direction = "a_supported"
            elif delta_positive < 0 and delta_pf < 0:
                direction = "b_supported"
            else:
                direction = "mixed_or_flat"

            eligible = (
                stats_a["occurrences"] >= MIN_RECURRENT_OCCURRENCES
                and stats_b["occurrences"] >= MIN_RECURRENT_OCCURRENCES
                and stats_a["phase_count"] >= MIN_PHASES
                and stats_b["phase_count"] >= MIN_PHASES
                and stats_a["regime_count"] >= MIN_REGIMES
                and stats_b["regime_count"] >= MIN_REGIMES
            )
            if eligible:
                eligible_contexts.append(item)

            per_asset.append(
                {
                    "symbol": item["symbol"],
                    "candidate_a_signature": item["candidate_signature_a"],
                    "candidate_b_signature": item["candidate_signature_b"],
                    "stats_a": stats_a,
                    "stats_b": stats_b,
                    "delta_a_minus_b": {
                        "positive_rate": delta_positive,
                        "pf_pass_rate": delta_pf,
                        "median_profit_eur": delta_median,
                    },
                    "primary_direction": direction,
                }
            )

        assets = sorted({item["symbol"] for item in eligible_contexts})
        directions = [
            "a_supported"
            if item["stats_a"]["positive_rate"] > item["stats_b"]["positive_rate"]
            and item["stats_a"]["pf_pass_rate"] > item["stats_b"]["pf_pass_rate"]
            else "b_supported"
            if item["stats_a"]["positive_rate"] < item["stats_b"]["positive_rate"]
            and item["stats_a"]["pf_pass_rate"] < item["stats_b"]["pf_pass_rate"]
            else "mixed_or_flat"
            for item in eligible_contexts
        ]
        consistent = (
            len(assets) >= MIN_ASSETS
            and len(directions) == len(assets)
            and len(set(directions)) == 1
            and directions[0] in {"a_supported", "b_supported"}
        )

        candidate = {
            "selection_profile": contexts[0]["selection_profile"],
            "geometry": contexts[0]["geometry"],
            "parameter": contexts[0]["parameter"],
            "value_a": contexts[0]["value_a"],
            "value_b": contexts[0]["value_b"],
            "fixed_parameters": contexts[0]["fixed_parameters"],
            "assets": assets,
            "asset_count": len(assets),
            "eligible_context_count": len(eligible_contexts),
            "per_asset": per_asset,
            "consistent_primary_direction": consistent,
            "supported_value": (
                contexts[0]["value_a"]
                if consistent and directions[0] == "a_supported"
                else contexts[0]["value_b"]
                if consistent
                else None
            ),
        }
        candidate["experiment_ready"] = consistent
        out.append(candidate)

    return out


def analyze(source: dict[str, Any]) -> dict[str, Any]:
    _validate_source(source)
    contrasts = _single_parameter_contrasts(source)
    candidates = _cross_asset_candidates(contrasts)
    eligible = [item for item in candidates if item["experiment_ready"]]

    if len(eligible) == 1:
        status = "one_experiment_ready_hypothesis"
        next_action = "controlled_reexperiment"
        hypothesis = eligible[0]
    elif not eligible:
        status = "no_experiment_ready_hypothesis"
        next_action = "extend_evidence_before_parameter_change"
        hypothesis = None
    else:
        status = "multiple_experiment_ready_hypotheses"
        next_action = "do_not_choose_between_hypotheses_without_predeclared_rule"
        hypothesis = None

    report = {
        "schema_version": 1,
        "diagnostic_type": "strictly_stratified_hypothesis_control",
        "source_analysis_fingerprint": source["analysis_fingerprint"],
        "source_target_count": int(source["source_target_count"]),
        "source_research_candle_count": int(source["source_research_candle_count"]),
        "source_universe": source["source_universe"],
        "minimum_recurrent_occurrences": MIN_RECURRENT_OCCURRENCES,
        "minimum_phase_count": MIN_PHASES,
        "minimum_regime_count": MIN_REGIMES,
        "minimum_independent_assets": MIN_ASSETS,
        "primary_metrics": list(PRIMARY_METRICS),
        "recurring_single_parameter_contrasts": contrasts,
        "cross_asset_hypothesis_candidates": candidates,
        "eligible_hypothesis_count": len(eligible),
        "status": status,
        "next_action": next_action,
        "experiment_ready_hypothesis": hypothesis,
        "interpretation_scope": {
            "diagnostic_only": True,
            "no_backtests_run": True,
            "no_data_downloads": True,
            "no_selection_change": True,
            "no_parameter_space_change": True,
            "no_gate_change": True,
            "single_parameter_contrast_only": True,
            "same_fixed_parameters": True,
            "minimum_two_assets": True,
            "primary_metrics_require_same_direction_per_asset": True,
            "not_causal": True,
            "not_a_global_parameter_recommendation": True,
        },
        "safety": EXPECTED_SAFETY,
    }
    report["analysis_fingerprint"] = _fingerprint(report)
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Strictly Stratified Hypothesis Control",
        "",
        f"- Analysis-Fingerprint: `{report['analysis_fingerprint']}`",
        f"- Source-Matrix-Fingerprint: `{report['source_analysis_fingerprint']}`",
        f"- Status: `{report['status']}`",
        f"- Next action: `{report['next_action']}`",
        "",
        "## Prüfkriterien",
        "",
        f"- Wiederkehrende Kandidatenstruktur je Kontext: mindestens {report['minimum_recurrent_occurrences']} Fenster",
        f"- Je Kandidatenseite: mindestens {report['minimum_phase_count']} Phasen und {report['minimum_regime_count']} kombinierte Regime",
        f"- Cross-Asset-Replikation: mindestens {report['minimum_independent_assets']} Assets",
        "- Exakt ein Parameter darf abweichen; die übrigen vier Parameter müssen identisch sein.",
        "- Positive Fensterquote und PF-Pass müssen pro Asset dieselbe Richtung zeigen.",
        "",
        f"## Experimentbereite Hypothesen: {report['eligible_hypothesis_count']}",
        "",
    ]
    hypothesis = report["experiment_ready_hypothesis"]
    if hypothesis is None:
        lines.append("Keine eindeutige experimentbereite Hypothese identifiziert.")
    else:
        lines += [
            f"- Profil: `{hypothesis['selection_profile']}`",
            f"- Geometrie: `{hypothesis['geometry']}`",
            f"- Parameter: `{hypothesis['parameter']}`",
            f"- Vergleich: `{hypothesis['value_a']}` vs. `{hypothesis['value_b']}`",
            f"- Konsistent unterstützter Wert: `{hypothesis['supported_value']}`",
            f"- Assets: {', '.join(hypothesis['assets'])}",
            "",
            "| Asset | A n | B n | A positive | B positive | A PF-Pass | B PF-Pass | A-B Medianprofit | Richtung |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for item in hypothesis["per_asset"]:
            a, b = item["stats_a"], item["stats_b"]
            lines.append(
                f"| {item['symbol']} | {a['occurrences']} | {b['occurrences']} | "
                f"{a['positive_rate']:.3f} | {b['positive_rate']:.3f} | "
                f"{a['pf_pass_rate']:.3f} | {b['pf_pass_rate']:.3f} | "
                f"{item['delta_a_minus_b']['median_profit_eur']:.3f} | {item['primary_direction']} |"
            )

    lines += [
        "",
        "## Methodische Grenze",
        "",
        "Dies ist eine streng geschichtete deskriptive Assoziation aus bereits ausgewählten Rolling-Kandidaten, kein Kausalnachweis und keine globale Parameterempfehlung.",
        "Der nächste Schritt darf ausschließlich ein isoliertes kontrolliertes Re-Experiment mit identischer Datenbasis und unveränderten Gates/Selection-Definitionen sein.",
        "",
        "Paper-Only: True; Live-Trading: False; Orders: False.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-dir", default="research/stratified_hypothesis")
    args = parser.parse_args()

    source = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    report = analyze(source)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "stratified_hypothesis_control.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    (output / "stratified_hypothesis_control.md").write_text(
        markdown(report),
        encoding="utf-8",
    )
    print("STRATIFIED_HYPOTHESIS_CONTROL: COMPLETED")
    print("STATUS:", report["status"])
    print("ELIGIBLE_HYPOTHESES:", report["eligible_hypothesis_count"])
    print("ANALYSIS_FINGERPRINT:", report["analysis_fingerprint"])
    print("PAPER_ONLY:", report["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", report["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
