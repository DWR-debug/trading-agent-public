"""Measure cross-profile candidate consensus on the immutable Selection-to-OOS control."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EXPECTED_PROFILES = (
    "score_max",
    "boundary_averse",
    "risk_averse",
    "trade_rich",
)
EXPECTED_WINDOWS = 60


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


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denominator = math.sqrt(
        sum((x - mx) ** 2 for x in xs)
        * sum((y - my) ** 2 for y in ys)
    )
    return numerator / denominator if denominator else None


def _collect(control: dict[str, Any]) -> list[dict[str, Any]]:
    if control.get("diagnostic_type") != "rolling_selection_to_oos_control":
        raise ValueError("Unexpected Selection-to-OOS control type.")

    safety = control.get("safety", {})
    if safety.get("paper_only") is not True:
        raise ValueError("Paper-Only safety flag is not enabled.")
    if safety.get("live_trading_enabled") is not False:
        raise ValueError("Live trading must remain disabled.")
    if safety.get("orders_enabled") is not False:
        raise ValueError("Orders must remain disabled.")

    profiles = tuple(control.get("selection_profiles", ()))
    if profiles != EXPECTED_PROFILES:
        raise ValueError(f"Unexpected selection profiles: {profiles!r}")

    by_window: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for dataset in control["datasets"]:
        for profile in dataset["profiles"]:
            profile_name = profile["selection_profile"]
            for geometry in ("small", "large"):
                for window in profile[geometry]["windows"]:
                    selection = window.get("selection")
                    if not isinstance(selection, dict):
                        raise ValueError("Selection metadata missing.")
                    by_window[
                        (
                            dataset["symbol"],
                            geometry,
                            int(window["window_index"]),
                        )
                    ].append(
                        {
                            "profile": profile_name,
                            "candidate_fingerprint": window["candidate_fingerprint"],
                            "raw_score_rank": int(selection["raw_score_rank"]),
                            "oos_profit_eur": float(window["net_profit_eur"]),
                            "oos_positive": float(window["net_profit_eur"]) > 0.0,
                            "oos_pf_pass": (
                                window["profit_factor"] == "inf"
                                or float(window["profit_factor"]) >= 1.10
                            ),
                        }
                    )

    if len(by_window) != EXPECTED_WINDOWS:
        raise ValueError(
            f"Expected {EXPECTED_WINDOWS} unique market windows, got {len(by_window)}."
        )

    rows = []
    for key, values in sorted(by_window.items()):
        if tuple(sorted(v["profile"] for v in values)) != tuple(
            sorted(EXPECTED_PROFILES)
        ):
            raise ValueError(f"Profile coverage mismatch for {key!r}.")

        fingerprints = [v["candidate_fingerprint"] for v in values]
        counts = Counter(fingerprints)
        consensus_size = max(counts.values())
        unique_candidates = len(counts)
        agreeing_pairs = sum(
            count * (count - 1) // 2 for count in counts.values()
        )
        pair_count = len(EXPECTED_PROFILES) * (len(EXPECTED_PROFILES) - 1) // 2
        oos_profits = [v["oos_profit_eur"] for v in values]
        raw_ranks = [v["raw_score_rank"] for v in values]
        consensus_fp, _ = counts.most_common(1)[0]
        consensus_rows = [
            v for v in values if v["candidate_fingerprint"] == consensus_fp
        ]

        rows.append(
            {
                "symbol": key[0],
                "geometry": key[1],
                "window_index": key[2],
                "unique_candidate_count": unique_candidates,
                "consensus_size": consensus_size,
                "consensus_rate": consensus_size / len(EXPECTED_PROFILES),
                "pairwise_agreement_rate": agreeing_pairs / pair_count,
                "raw_score_rank_median": statistics.median(raw_ranks),
                "raw_score_rank_range": max(raw_ranks) - min(raw_ranks),
                "raw_score_rank_std": statistics.pstdev(raw_ranks),
                "oos_profit_mean_eur": statistics.mean(oos_profits),
                "oos_profit_median_eur": statistics.median(oos_profits),
                "oos_profit_range_eur": max(oos_profits) - min(oos_profits),
                "oos_profit_std_eur": statistics.pstdev(oos_profits),
                "oos_positive_count": sum(v["oos_positive"] for v in values),
                "oos_pf_pass_count": sum(v["oos_pf_pass"] for v in values),
                "consensus_candidate_fingerprint": consensus_fp,
                "consensus_candidate_count": len(consensus_rows),
                "consensus_candidate_oos_mean_eur": (
                    statistics.mean(v["oos_profit_eur"] for v in consensus_rows)
                    if consensus_rows
                    else None
                ),
            }
        )

    return rows


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "market_window_count": 0,
            "all_four_agree_rate": 0.0,
            "at_least_three_agree_rate": 0.0,
            "median_unique_candidate_count": None,
            "median_consensus_rate": None,
            "median_oos_profit_mean_eur": None,
            "median_oos_profit_range_eur": None,
        }

    return {
        "market_window_count": len(rows),
        "all_four_agree_rate": sum(
            row["consensus_size"] == 4 for row in rows
        ) / len(rows),
        "at_least_three_agree_rate": sum(
            row["consensus_size"] >= 3 for row in rows
        ) / len(rows),
        "median_unique_candidate_count": statistics.median(
            row["unique_candidate_count"] for row in rows
        ),
        "median_consensus_rate": statistics.median(
            row["consensus_rate"] for row in rows
        ),
        "median_oos_profit_mean_eur": statistics.median(
            row["oos_profit_mean_eur"] for row in rows
        ),
        "median_oos_profit_range_eur": statistics.median(
            row["oos_profit_range_eur"] for row in rows
        ),
    }


def _correlations(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mappings = {
        "unique_candidates_vs_oos_mean": (
            "unique_candidate_count",
            "oos_profit_mean_eur",
        ),
        "consensus_rate_vs_oos_mean": (
            "consensus_rate",
            "oos_profit_mean_eur",
        ),
        "raw_rank_range_vs_oos_range": (
            "raw_score_rank_range",
            "oos_profit_range_eur",
        ),
        "raw_rank_std_vs_oos_range": (
            "raw_score_rank_std",
            "oos_profit_range_eur",
        ),
    }
    result = {}
    for name, (xkey, ykey) in mappings.items():
        xs = [float(row[xkey]) for row in rows]
        ys = [float(row[ykey]) for row in rows]
        result[name] = {
            "n": len(xs),
            "pearson": _pearson(xs, ys),
        }
    return result


def _pairwise_agreement(
    control: dict[str, Any],
) -> list[dict[str, Any]]:
    pairs = [
        tuple(sorted((EXPECTED_PROFILES[i], EXPECTED_PROFILES[j])))
        for i in range(len(EXPECTED_PROFILES))
        for j in range(i + 1, len(EXPECTED_PROFILES))
    ]
    results = []
    rows = []
    for dataset in control["datasets"]:
        for profile in dataset["profiles"]:
            for geometry in ("small", "large"):
                for window in profile[geometry]["windows"]:
                    rows.append(
                        (
                            dataset["symbol"],
                            geometry,
                            int(window["window_index"]),
                            profile["selection_profile"],
                            window["candidate_fingerprint"],
                        )
                    )

    grouped = defaultdict(dict)
    for symbol, geometry, index, profile, fingerprint in rows:
        grouped[(symbol, geometry, index)][profile] = fingerprint

    for pair in pairs:
        matches = 0
        total = 0
        for values in grouped.values():
            if pair[0] in values and pair[1] in values:
                total += 1
                matches += values[pair[0]] == values[pair[1]]
        results.append(
            {
                "profile_a": pair[0],
                "profile_b": pair[1],
                "market_window_count": total,
                "candidate_agreement_rate": matches / total if total else 0.0,
            }
        )
    return results


def analyze(control: dict[str, Any]) -> dict[str, Any]:
    rows = _collect(control)
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["symbol"], row["geometry"])].append(row)

    result = {
        "schema_version": 1,
        "diagnostic_type": "selection_profile_consensus_analysis",
        "source_control_fingerprint": control["diagnostic_fingerprint"],
        "evaluation_count": 240,
        "unique_market_window_count": len(rows),
        "profile_count": len(EXPECTED_PROFILES),
        "profiles": list(EXPECTED_PROFILES),
        "overall": {
            "summary": _summary(rows),
            "consensus_size_distribution": dict(
                sorted(
                    Counter(row["consensus_size"] for row in rows).items()
                )
            ),
            "unique_candidate_distribution": dict(
                sorted(
                    Counter(row["unique_candidate_count"] for row in rows).items()
                )
            ),
            "correlations": _correlations(rows),
        },
        "pairwise_agreement": _pairwise_agreement(control),
        "by_asset_geometry": {
            f"{symbol}|{geometry}": _summary(group_rows)
            | {"correlations": _correlations(group_rows)}
            for (symbol, geometry), group_rows in sorted(grouped.items())
        },
        "interpretation_scope": {
            "diagnostic_only": True,
            "same_market_windows_across_profiles": True,
            "profile_disagreement_is_not_itself_a_selection_failure": True,
            "cross_profile_consensus_is_not_used_as_a_selection_rule": True,
            "oos_is_outcome_only": True,
            "correlations_are_descriptive_not_causal": True,
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
    summary = result["overall"]["summary"]

    lines = [
        "# Selection-Profile-Konsistenzanalyse",
        "",
        f"- Analysis-Fingerprint: {result['analysis_fingerprint']}",
        f"- Source-Control-Fingerprint: {result['source_control_fingerprint']}",
        f"- Marktfenster: {result['unique_market_window_count']}",
        f"- Selection-Profile: {result['profile_count']}",
        "",
        "## Gesamt",
        "",
        f"- alle vier Profile identisch: {summary['all_four_agree_rate']:.3f}",
        f"- mindestens drei Profile identisch: {summary['at_least_three_agree_rate']:.3f}",
        f"- Median Anzahl unterschiedlicher Kandidaten: {summary['median_unique_candidate_count']}",
        f"- Median Consensus-Rate: {summary['median_consensus_rate']:.3f}",
        f"- Median OOS-Profit-Mittelwert: {summary['median_oos_profit_mean_eur']:.2f} EUR",
        f"- Median OOS-Profit-Range über Profile: {summary['median_oos_profit_range_eur']:.2f} EUR",
        "",
        "## Konsens-Verteilung",
        "",
        "| Konsensgröße | Marktfenster | Quote |",
        "| ---: | ---: | ---: |",
    ]
    total = summary["market_window_count"]
    for size, count in sorted(
        result["overall"]["consensus_size_distribution"].items()
    ):
        lines.append(
            f"| {size} | {count} | {count / total:.3f} |"
        )

    lines += [
        "",
        "## Paarweise Profile",
        "",
        "| Profil A | Profil B | Marktfenster | Kandidaten-Übereinstimmung |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in result["pairwise_agreement"]:
        lines.append(
            f"| {row['profile_a']} | {row['profile_b']} | "
            f"{row['market_window_count']} | {row['candidate_agreement_rate']:.3f} |"
        )

    lines += [
        "",
        "## Asset x Geometrie",
        "",
        "| Gruppe | Fenster | alle 4 identisch | mind. 3 identisch | Median unique Kandidaten | Median OOS-Profit | Median OOS-Range |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, item in result["by_asset_geometry"].items():
        s = item
        lines.append(
            f"| {key} | {s['market_window_count']} | "
            f"{s['all_four_agree_rate']:.3f} | {s['at_least_three_agree_rate']:.3f} | "
            f"{s['median_unique_candidate_count']} | "
            f"{s['median_oos_profit_mean_eur']:.2f} EUR | "
            f"{s['median_oos_profit_range_eur']:.2f} EUR |"
        )

    lines += [
        "",
        "## Korrelationen",
        "",
        "| Merkmal | n | Pearson |",
        "| --- | ---: | ---: |",
    ]
    for name, item in result["overall"]["correlations"].items():
        value = "n/a" if item["pearson"] is None else f"{item['pearson']:.4f}"
        lines.append(f"| {name} | {item['n']} | {value} |")

    lines += [
        "",
        "## Methodische Einordnung",
        "",
        "Die vier Profile optimieren unterschiedliche Ziele. Divergierende Kandidaten sind daher nicht automatisch ein Fehler.",
        "Die Analyse misst, wie stark diese unterschiedlichen Selection-Ziele auf denselben Marktfenstern zu unterschiedlichen Kandidaten führen und wie stark sich deren nachfolgende OOS-Ergebnisse unterscheiden.",
        "Die gemeinsamen Marktfenster bedeuten, dass profilebasierte Evaluationen innerhalb eines Fensters nicht unabhängig sind.",
        "Cross-Profile-Konsens wird nicht als neue Selection-Regel verwendet.",
        "",
        "Paper-Only: True; Live-Trading: False; Orders: False.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-json", required=True)
    parser.add_argument(
        "--output-dir",
        default="research/selection_profile_consensus",
    )
    args = parser.parse_args()

    control = json.loads(Path(args.control_json).read_text(encoding="utf-8"))
    result = analyze(control)

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "selection_profile_consensus_analysis.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    (output / "selection_profile_consensus_analysis.md").write_text(
        markdown(result),
        encoding="utf-8",
    )
    print("SELECTION_PROFILE_CONSENSUS: COMPLETED")
    print("ANALYSIS_FINGERPRINT:", result["analysis_fingerprint"])
    print("MARKET_WINDOWS:", result["unique_market_window_count"])
    print("PAPER_ONLY:", result["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", result["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
