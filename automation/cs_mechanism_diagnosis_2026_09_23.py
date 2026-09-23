"""Mechanism-level diagnosis of the fixed cross-sectional momentum sleeve.

Diagnostic-only: reuses the immutable second-validation artifact. It does not
change parameters, signals, universes, sleeve weights, gates or production code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean, pstdev

from automation import candidate_validation_50_50_vol_budget as base
from automation.independent_validation_2026_09_23 import CS_UNIVERSE, TREND_UNIVERSE, _manifest
from config import settings
from research.asset_universes import get_universe

CS_LOOKBACK = base.CS_LOOKBACK
CS_SKIP = base.CS_SKIP
CS_REBALANCE = base.CS_REBALANCE
CS_TOP_N = base.CS_TOP_N
RESEARCH_COUNT = base.RESEARCH_COUNT
HOLDOUT_COUNT = base.HOLDOUT_COUNT
ROLLING_WIDTH = RESEARCH_COUNT // 5
WINDOWS = tuple(
    (i + 1, i * ROLLING_WIDTH, RESEARCH_COUNT if i == 4 else (i + 1) * ROLLING_WIDTH)
    for i in range(5)
)


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _period_return(values: list[float]) -> float:
    equity = 1.0
    for value in values:
        equity *= 1.0 + value
    return equity - 1.0


def _correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    left_dev = pstdev(left)
    right_dev = pstdev(right)
    if left_dev == 0.0 or right_dev == 0.0:
        return 0.0
    left_mean = mean(left)
    right_mean = mean(right)
    return mean((a - left_mean) * (b - right_mean) for a, b in zip(left, right)) / (left_dev * right_dev)


def _rank_snapshot(assets: dict[str, tuple], index: int) -> dict | None:
    if index < CS_LOOKBACK + CS_SKIP or index % CS_REBALANCE != 0:
        return None
    anchor = index - CS_SKIP
    origin = anchor - CS_LOOKBACK
    scores = {
        symbol: assets[symbol][anchor].close / assets[symbol][origin].close - 1.0
        for symbol in assets
    }
    ranking = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    winners = tuple(symbol for symbol, _ in ranking[:CS_TOP_N])
    losers = tuple(symbol for symbol, _ in ranking[-CS_TOP_N:])
    return {
        "index": index,
        "timestamp": assets[next(iter(assets))][index].timestamp,
        "scores": scores,
        "ranking": tuple(ranking),
        "winners": winners,
        "losers": losers,
        "winner_score_mean": mean(scores[s] for s in winners),
        "loser_score_mean": mean(scores[s] for s in losers),
        "winner_loser_score_spread": mean(scores[s] for s in winners) - mean(scores[s] for s in losers),
    }


def _build_selection_diagnosis(cs_assets: dict[str, tuple], research_end: int) -> tuple[list[dict], list[dict]]:
    symbols = tuple(cs_assets)
    cs_weights_path = base._cs_weights(cs_assets)
    rows: list[dict] = []
    rebalances: list[dict] = []
    previous_weights = {symbol: 0.0 for symbol in symbols}
    previous_winners: tuple[str, ...] = ()

    for index in range(research_end):
        asset_returns = {
            symbol: cs_assets[symbol][index + 2].open / cs_assets[symbol][index + 1].open - 1.0
            for symbol in symbols
        }
        weights = cs_weights_path[index]
        selected = tuple(symbol for symbol in symbols if weights.get(symbol, 0.0) > 0.0)
        selected_return = (
            sum(asset_returns[symbol] for symbol in selected) / len(selected)
            if selected else 0.0
        )
        equal_weight_return = mean(asset_returns.values())
        sorted_returns = sorted(asset_returns.items(), key=lambda item: item[1])
        bottom = tuple(symbol for symbol, _ in sorted_returns[:CS_TOP_N])
        top = tuple(symbol for symbol, _ in sorted_returns[-CS_TOP_N:])
        exact_turnover = sum(
            abs(weights.get(symbol, 0.0) - previous_weights[symbol])
            for symbol in symbols
        )
        previous_weights = dict(weights)

        snapshot = _rank_snapshot(cs_assets, index)
        rank_turnover = None
        if snapshot is not None:
            current_winners = snapshot["winners"]
            if previous_winners:
                rank_turnover = 1.0 - len(set(previous_winners) & set(current_winners)) / CS_TOP_N
            previous_winners = current_winners

            forward_end = min(index + CS_REBALANCE, research_end)
            if forward_end - index == CS_REBALANCE:
                forward_selected = []
                forward_equal = []
                forward_bottom = []
                for future_index in range(index, forward_end):
                    future_returns = {
                        symbol: cs_assets[symbol][future_index + 2].open / cs_assets[symbol][future_index + 1].open - 1.0
                        for symbol in symbols
                    }
                    forward_selected.append(mean(future_returns[symbol] for symbol in current_winners))
                    forward_equal.append(mean(future_returns.values()))
                    forward_bottom.append(mean(future_returns[symbol] for symbol in snapshot["losers"]))

                rebalances.append(
                    {
                        "index": index,
                        "timestamp": snapshot["timestamp"].isoformat(),
                        "winners": list(snapshot["winners"]),
                        "losers": list(snapshot["losers"]),
                        "ranking": [[symbol, score] for symbol, score in snapshot["ranking"]],
                        "winner_score_mean": snapshot["winner_score_mean"],
                        "loser_score_mean": snapshot["loser_score_mean"],
                        "winner_loser_score_spread": snapshot["winner_loser_score_spread"],
                        "rank_turnover": rank_turnover,
                        "cross_sectional_turnover": exact_turnover,
                        "forward_selection_spread": _period_return(forward_selected) - _period_return(forward_equal),
                        "forward_selected_vs_bottom": _period_return(forward_selected) - _period_return(forward_bottom),
                    }
                )

        rows.append(
            {
                "index": index,
                "timestamp": cs_assets[symbols[0]][index + 2].timestamp,
                "selected_return": selected_return,
                "equal_weight_return": equal_weight_return,
                "selection_spread": selected_return - equal_weight_return,
                "selected_vs_bottom_return": selected_return - mean(asset_returns[symbol] for symbol in bottom),
                "top_return": mean(asset_returns[symbol] for symbol in top),
                "bottom_return": mean(asset_returns[symbol] for symbol in bottom),
                "cross_sectional_dispersion": pstdev(asset_returns.values()),
                "cross_sectional_turnover": exact_turnover,
            }
        )

    return rows, rebalances


def _summary(rows: list[dict], rebalances: list[dict]) -> dict:
    if not rows:
        return {
            "day_count": 0,
            "selected_period_return": 0.0,
            "equal_weight_period_return": 0.0,
            "selection_spread_period_return": 0.0,
            "selection_positive_day_ratio": 0.0,
            "selected_beats_equal_weight_ratio": 0.0,
            "selected_beats_bottom_ratio": 0.0,
            "median_cross_sectional_dispersion": 0.0,
            "mean_cross_sectional_dispersion": 0.0,
            "mean_cross_sectional_turnover": 0.0,
            "mean_rank_turnover": 0.0,
            "formation_count": 0,
            "negative_forward_spread_count": 0,
            "negative_forward_spread_ratio": 0.0,
            "positive_score_negative_forward_spread_count": 0,
            "positive_score_negative_forward_spread_ratio": 0.0,
            "score_forward_spread_correlation": 0.0,
            "mean_forward_selection_spread": 0.0,
        }

    selected = [row["selected_return"] for row in rows]
    equal_weight = [row["equal_weight_return"] for row in rows]
    rank_turnovers = [item["rank_turnover"] for item in rebalances if item["rank_turnover"] is not None]
    forward_spreads = [item["forward_selection_spread"] for item in rebalances]
    forward_scores = [item["winner_score_mean"] for item in rebalances]
    positive_score_negative = sum(
        item["winner_score_mean"] > 0.0 and item["forward_selection_spread"] < 0.0
        for item in rebalances
    )

    return {
        "day_count": len(rows),
        "selected_period_return": _period_return(selected),
        "equal_weight_period_return": _period_return(equal_weight),
        "selection_spread_period_return": _period_return(selected) - _period_return(equal_weight),
        "selection_positive_day_ratio": sum(value > 0.0 for value in selected) / len(selected),
        "selected_beats_equal_weight_ratio": sum(a > b for a, b in zip(selected, equal_weight)) / len(selected),
        "selected_beats_bottom_ratio": sum(row["selected_vs_bottom_return"] > 0.0 for row in rows) / len(rows),
        "median_cross_sectional_dispersion": sorted(row["cross_sectional_dispersion"] for row in rows)[len(rows) // 2],
        "mean_cross_sectional_dispersion": mean(row["cross_sectional_dispersion"] for row in rows),
        "mean_cross_sectional_turnover": mean(row["cross_sectional_turnover"] for row in rows),
        "mean_rank_turnover": mean(rank_turnovers) if rank_turnovers else 0.0,
        "formation_count": len(rebalances),
        "negative_forward_spread_count": sum(value < 0.0 for value in forward_spreads),
        "negative_forward_spread_ratio": (
            sum(value < 0.0 for value in forward_spreads) / len(forward_spreads)
            if forward_spreads else 0.0
        ),
        "positive_score_negative_forward_spread_count": positive_score_negative,
        "positive_score_negative_forward_spread_ratio": (
            positive_score_negative / len(rebalances)
            if rebalances else 0.0
        ),
        "score_forward_spread_correlation": _correlation(forward_scores, forward_spreads),
        "mean_forward_selection_spread": mean(forward_spreads) if forward_spreads else 0.0,
    }


def _cost_and_interaction_summary(
    simulated: list[dict],
    portfolio_turnover: list[float],
    selection_rows: list[dict],
    start: int,
    end: int,
) -> dict:
    segment_sim = simulated[start:end]
    segment_selection = selection_rows[start:end]
    gross = [item["gross_return"] for item in segment_sim]
    net = [item["net_return"] for item in segment_sim]
    total_turnover = sum(portfolio_turnover[start:end])
    cs_turnover = sum(item["cross_sectional_turnover"] for item in segment_selection)

    return {
        "portfolio_gross_period_return": _period_return(gross),
        "portfolio_net_period_return": _period_return(net),
        "portfolio_cost_drag_compounded_difference": _period_return(gross) - _period_return(net),
        "cross_sectional_turnover_share": (
            (0.5 * cs_turnover) / total_turnover
            if total_turnover > 0.0
            else 0.0
        ),
    }


def run_diagnosis(artifact_root: Path, output_path: Path) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only-Sicherheitsvertrag verletzt.")

    report_path = artifact_root / "research/independent_validation_2026_09_23/report.json"
    trend_manifest_path = artifact_root / "research/independent_validation_2026_09_23/data_trend_manifest.json"
    cs_manifest_path = artifact_root / "research/independent_validation_2026_09_23/data_cs_manifest.json"
    data_dir = artifact_root / "data/market_data"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    stored_report_fingerprint = report.pop("report_fingerprint")
    if _fingerprint(report) != stored_report_fingerprint:
        raise ValueError("Report-Fingerprint ungültig.")
    if report["candidate_status"] != "BLOCKED":
        raise ValueError("Diagnose erwartet den archivierten BLOCKED-Report.")

    trend_manifest = _manifest(trend_manifest_path, TREND_UNIVERSE)
    cs_manifest = _manifest(cs_manifest_path, CS_UNIVERSE)
    trend = base._assets(data_dir, trend_manifest)
    cs = base._assets(data_dir, cs_manifest)
    if set(trend) & set(cs):
        raise ValueError("Universen sind nicht disjunkt.")

    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    selection_rows, research_rebalances = _build_selection_diagnosis(cs, RESEARCH_COUNT)

    all_assets = {**trend, **cs}
    close_proxy = {
        symbol: {bar.timestamp: bar.close for bar in bars}
        for symbol, bars in all_assets.items()
    }
    rows = base._align(
        trend,
        trend_weights,
        {symbol: close_proxy[symbol] for symbol in trend},
        cs,
        base._cs_weights(cs),
        {symbol: close_proxy[symbol] for symbol in cs},
    )
    simulated = base._simulate(rows, 1.0, True, False)
    reference = report["scenarios"]["base"]["vol_budget_10pct"]["price_only"]
    expected_count = reference["research"]["day_count"] + reference["holdout"]["day_count"]
    if len(simulated) != expected_count:
        raise ValueError("Simulation und archivierter Report haben unterschiedliche Längen.")

    recomputed = _period_return([item["net_return"] for item in simulated[:RESEARCH_COUNT]])
    if abs(recomputed - reference["research"]["period_return"]) > 1e-12:
        raise ValueError("Research-Return-Reproduktion fehlgeschlagen.")

    portfolio_turnover = []
    previous_scale = 1.0
    for row, sim in zip(rows, simulated):
        turnover = sim["scale"] * row["turnover"] + abs(sim["scale"] - previous_scale)
        portfolio_turnover.append(turnover)
        previous_scale = sim["scale"]

    if len(portfolio_turnover) != len(simulated):
        raise ValueError("Turnover-Rekonstruktion hat eine unerwartete Länge.")

    timestamp_mismatches = [
        index
        for index, (selection_row, portfolio_row) in enumerate(
            zip(selection_rows, rows[:RESEARCH_COUNT])
        )
        if selection_row["timestamp"] != portfolio_row["timestamp"]
    ]
    if timestamp_mismatches:
        raise ValueError(
            "Cross-Sectional- und Portfolio-Zeitachse sind nicht identisch."
        )

    windows = []
    for index, start, end in WINDOWS:
        window_rebalances = [
            item
            for item in research_rebalances
            if start <= item["index"] < end
        ]
        windows.append(
            {
                "window_index": index,
                "start_timestamp": selection_rows[start]["timestamp"].isoformat(),
                "end_timestamp": selection_rows[end - 1]["timestamp"].isoformat(),
                "selection": _summary(selection_rows[start:end], window_rebalances),
                "cost_and_interaction": _cost_and_interaction_summary(
                    simulated,
                    portfolio_turnover,
                    selection_rows,
                    start,
                    end,
                ),
            }
        )

    output = {
        "schema_version": 1,
        "diagnostic_type": "cross_sectional_mechanism_diagnosis_2026_09_23",
        "status": "COMPLETED",
        "input": {
            "source_report_fingerprint": stored_report_fingerprint,
            "source_candidate_status": report["candidate_status"],
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "cross_sectional_universe": list(get_universe(CS_UNIVERSE).symbols),
            "trend_universe": list(get_universe(TREND_UNIVERSE).symbols),
            "selection_rule": "fixed 12-1 momentum, 252-session lookback, 21-session skip, 21-session rebalance, top-2 long-only",
        },
        "research": _summary(selection_rows, research_rebalances),
        "rebalances": research_rebalances,
        "windows": windows,
        "interpretation_constraints": [
            "diagnostic only",
            "no parameter selection",
            "no asset replacement",
            "no signal change",
            "no sleeve-weight change",
            "no gate change",
            "no production change",
            "portfolio cost drag is reported but not causally allocated to a sleeve",
        ],
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    output["diagnostic_fingerprint"] = _fingerprint(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_diagnosis(Path(args.artifact_root), Path(args.output))
    print("CS_MECHANISM_DIAGNOSIS_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    print("RESEARCH_SELECTION_SPREAD:", result["research"]["selection_spread_period_return"])
    print("RESEARCH_SCORE_FORWARD_CORRELATION:", result["research"]["score_forward_spread_correlation"])
    print("RESEARCH_REVERSAL_RATIO:", result["research"]["positive_score_negative_forward_spread_ratio"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
