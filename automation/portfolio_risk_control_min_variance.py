"""Formal T041 portfolio risk-control experiment.

The strategy sleeves remain unchanged:
- Trend: fixed SMA-50/200 inverse-volatility sleeve.
- Cross-sectional: fixed 12-1 top-2 long-only momentum sleeve.

Only the allocation between the two sleeves changes. The challenger uses a
fixed 63-session covariance-aware minimum-variance allocation, long-only and
uncapped above 100% gross exposure. The baseline stays fixed 50/50.

This module is research-only. It never places orders and never promotes a
candidate automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from automation.cross_asset_trend_replication import _build_weight_path
from automation.literature_strategy_lab import load_bars
from config import settings
from research.asset_universes import get_universe
from research.protocol import dataset_fingerprint


ROOT = Path(__file__).resolve().parents[1]

TRIAL_ID = "T-2026-09-24-041"
TREND_UNIVERSE = "validation_2026_09_24_portfolio_risk_control_trend"
CS_UNIVERSE = "validation_2026_09_24_portfolio_risk_control_cs"

TARGET_COUNT = 3500
RESEARCH_SHARE = 0.80
COVARIANCE_WINDOW = 63
CS_LOOKBACK = 252
CS_SKIP = 21
CS_REBALANCE = 21
CS_TOP_N = 2

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_SCENARIOS = (
    ("base", 1.0),
    ("stress_1_5x_cost", 1.5),
    ("stress_2x_cost", 2.0),
)

SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


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


def _verify_preregistration(path: Path, expected_universe: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("trial_id") != TRIAL_ID:
        raise ValueError("Unexpected trial id in preregistration.")
    if payload.get("universe") != expected_universe:
        raise ValueError("Unexpected universe in preregistration.")
    if payload.get("requested_candles") != TARGET_COUNT:
        raise ValueError("Unexpected requested candle count.")
    if payload.get("search_scope", {}).get("parameter_search") is not False:
        raise ValueError("Parameter search must remain disabled.")
    if payload.get("search_scope", {}).get("holdout_used_for_selection") is not False:
        raise ValueError("Holdout selection must remain disabled.")
    if payload.get("safety") != SAFETY:
        raise ValueError("Safety contract in preregistration is invalid.")

    universe = get_universe(expected_universe)
    if tuple(payload.get("symbols", [])) != tuple(universe.symbols):
        raise ValueError("Preregistered symbols do not match the reserved universe.")
    if universe.interval != payload.get("interval"):
        raise ValueError("Preregistered interval does not match the universe.")

    return payload


def _load_coverage(
    coverage_path: Path,
    preregistration: dict,
) -> tuple[dict, dict[str, tuple]]:
    payload = json.loads(coverage_path.read_text(encoding="utf-8"))
    if payload.get("trial_id") != TRIAL_ID:
        raise ValueError("Coverage artifact belongs to another trial.")
    if payload.get("status") != "coverage_passed":
        raise ValueError("T041 formal research requires a passed coverage preflight.")
    if payload.get("universe") != preregistration["universe"]:
        raise ValueError("Coverage universe does not match preregistration.")
    if payload.get("per_symbol_counts") and any(
        value != TARGET_COUNT
        for value in payload["per_symbol_counts"].values()
    ):
        raise ValueError("Coverage contains a symbol below target history.")

    snapshots = payload.get("data_snapshot", {}).get("datasets", [])
    if len(snapshots) != len(preregistration["symbols"]):
        raise ValueError("Coverage snapshot is incomplete.")

    assets: dict[str, tuple] = {}
    for item in snapshots:
        symbol = item["symbol"]
        if symbol not in preregistration["symbols"]:
            raise ValueError(f"Unexpected snapshot symbol: {symbol}.")
        path = Path(item["path"])
        if not path.is_absolute():
            path = ROOT / path
        bars = tuple(
            load_bars(
                path,
                expected_count=TARGET_COUNT,
            )
        )
        if dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"Dataset fingerprint mismatch for {symbol}.")
        assets[symbol] = bars

    if tuple(assets) != tuple(preregistration["symbols"]):
        raise ValueError("Snapshot symbol order does not match preregistration.")

    return payload, assets


def _cs_weights(assets: dict[str, tuple]) -> tuple[dict[str, float], ...]:
    length = min(len(bars) for bars in assets.values())
    symbols = tuple(assets)
    current = {symbol: 0.0 for symbol in symbols}
    output = []

    for decision_index in range(length):
        if decision_index % CS_REBALANCE == 0:
            if decision_index < CS_LOOKBACK + CS_SKIP:
                current = {symbol: 0.0 for symbol in symbols}
            else:
                anchor = decision_index - CS_SKIP
                origin = anchor - CS_LOOKBACK
                scores = {
                    symbol: (
                        assets[symbol][anchor].close
                        / assets[symbol][origin].close
                        - 1.0
                    )
                    for symbol in symbols
                }
                winners = set(
                    sorted(
                        scores,
                        key=scores.get,
                        reverse=True,
                    )[:CS_TOP_N]
                )
                current = {
                    symbol: (
                        1.0 / CS_TOP_N
                        if symbol in winners
                        else 0.0
                    )
                    for symbol in symbols
                }
        output.append(dict(current))

    return tuple(output)


def _sleeve_rows(
    assets: dict[str, tuple],
    weights: tuple[dict[str, float], ...],
) -> tuple[dict, ...]:
    length = min(len(bars) for bars in assets.values())
    symbols = tuple(assets)
    if len(weights) != length:
        raise ValueError("Weight path length does not match asset history.")

    previous = {symbol: 0.0 for symbol in symbols}
    output = []

    for decision_index in range(length - 2):
        gross_return = 0.0
        turnover = 0.0
        target = weights[decision_index]

        for symbol in symbols:
            bars = assets[symbol]
            market_return = (
                bars[decision_index + 2].open
                / bars[decision_index + 1].open
                - 1.0
            )
            target_weight = float(target.get(symbol, 0.0))
            gross_return += target_weight * market_return
            turnover += abs(target_weight - previous[symbol])
            previous[symbol] = target_weight

        output.append(
            {
                "timestamp": next(
                    bars[decision_index + 2].timestamp
                    for bars in assets.values()
                ),
                "gross_return": gross_return,
                "turnover": turnover,
            }
        )

    return tuple(output)


def min_variance_weight(
    trend_returns: list[float],
    cs_returns: list[float],
) -> float:
    """Return the fixed long-only minimum-variance trend weight."""

    n = min(len(trend_returns), len(cs_returns))
    if n < COVARIANCE_WINDOW:
        return 0.5

    trend = trend_returns[-COVARIANCE_WINDOW:]
    cross = cs_returns[-COVARIANCE_WINDOW:]

    mt = sum(trend) / len(trend)
    mc = sum(cross) / len(cross)

    denominator = len(trend) - 1
    if denominator <= 0:
        return 0.5

    var_trend = sum((value - mt) ** 2 for value in trend) / denominator
    var_cs = sum((value - mc) ** 2 for value in cross) / denominator
    covariance = sum(
        (left - mt) * (right - mc)
        for left, right in zip(trend, cross)
    ) / denominator

    denominator = var_trend + var_cs - 2.0 * covariance
    if denominator <= 0.0:
        return 0.5

    raw = (var_cs - covariance) / denominator
    return min(1.0, max(0.0, raw))


def _allocation_path(
    rows: tuple[dict, ...],
) -> tuple[float, ...]:
    trend_history: list[float] = []
    cs_history: list[float] = []
    output = []

    previous_month = None
    current = 0.5

    for row in rows:
        month = (
            row["timestamp"].year,
            row["timestamp"].month,
        )
        if month != previous_month:
            current = min_variance_weight(
                trend_history,
                cs_history,
            )
            previous_month = month

        output.append(current)
        trend_history.append(row["trend_gross"])
        cs_history.append(row["cs_gross"])

    return tuple(output)


def _stats(values: list[float], start: int, end: int) -> dict:
    segment = values[start:end]
    if not segment:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "day_count": 0,
        }

    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    gross_profit = 0.0
    gross_loss = 0.0

    for value in segment:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_drawdown = max(
            max_drawdown,
            1.0 - equity / peak if peak > 0.0 else 1.0,
        )
        if value > 0.0:
            gross_profit += value
        elif value < 0.0:
            gross_loss -= value

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0.0
        else ("inf" if gross_profit > 0.0 else 0.0)
    )

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_drawdown * 100.0,
        "profit_factor": profit_factor,
        "day_count": len(segment),
    }


def _rolling(values: list[float], research_end: int) -> list[dict]:
    width = research_end // 5
    windows = []
    start = 0

    for index in range(5):
        end = (
            research_end
            if index == 4
            else start + width
        )
        stats = _stats(values, start, end)
        windows.append(
            {
                "window_index": index + 1,
                **stats,
            }
        )
        start = end

    return windows


def _summary(
    values: list[float],
    research_end: int,
) -> dict:
    development_end = max(
        1,
        int(research_end * 0.80),
    )
    research = _stats(values, 0, research_end)
    development = _stats(values, 0, development_end)
    oos = _stats(values, development_end, research_end)
    holdout = _stats(values, research_end, len(values))
    rolling = _rolling(values, research_end)

    return {
        "research": research,
        "development": development,
        "oos": oos,
        "holdout": holdout,
        "oos_to_is_return_ratio": (
            oos["period_return"] / development["period_return"]
            if development["period_return"] > 0.0
            else 0.0
        ),
        "rolling": rolling,
        "rolling_min_profit_factor": min(
            (
                float("inf")
                if item["profit_factor"] == "inf"
                else float(item["profit_factor"])
            )
            for item in rolling
        ),
        "rolling_profitable_window_ratio": (
            sum(
                item["period_return"] > 0.0
                for item in rolling
            )
            / len(rolling)
        ),
        "rolling_average_drawdown_percent": (
            sum(
                item["max_drawdown_percent"]
                for item in rolling
            )
            / len(rolling)
        ),
    }


def _simulate(
    rows: tuple[dict, ...],
    challenger: bool,
    cost_multiplier: float,
) -> list[dict]:
    allocation = (
        _allocation_path(rows)
        if challenger
        else tuple(0.5 for _ in rows)
    )

    previous_trend_weight = 0.5
    output = []

    for index, row in enumerate(rows):
        trend_weight = allocation[index]
        cs_weight = 1.0 - trend_weight

        turnover = (
            trend_weight * row["trend_turnover"]
            + cs_weight * row["cs_turnover"]
            + 2.0 * abs(
                trend_weight - previous_trend_weight
            )
        )

        gross = (
            trend_weight * row["trend_gross"]
            + cs_weight * row["cs_gross"]
        )
        net = gross - (
            FEE_RATE + SLIPPAGE_RATE
        ) * cost_multiplier * turnover

        output.append(
            {
                "timestamp": row["timestamp"],
                "trend_weight": trend_weight,
                "cs_weight": cs_weight,
                "turnover": turnover,
                "gross_return": gross,
                "net_return": net,
            }
        )
        previous_trend_weight = trend_weight

    return output


def _gates(
    result: dict,
    control: dict,
) -> dict:
    base = result["base"]
    stress15 = result["stress_1_5x_cost"]
    stress2 = result["stress_2x_cost"]

    research = base["research"]
    holdout = base["holdout"]
    rolling = base["rolling_summary"]

    challenger_gates = {
        "positive_research_return": research["period_return"] > 0.0,
        "research_drawdown_lte_10pct": (
            research["max_drawdown_percent"] <= 10.0
        ),
        "research_profit_factor_gte_1_10": (
            (
                math.inf
                if research["profit_factor"] == "inf"
                else float(research["profit_factor"])
            ) >= 1.10
        ),
        "rolling_profit_factor_gte_1_10": (
            rolling["rolling_min_profit_factor"] >= 1.10
        ),
        "profitable_rolling_windows_gte_50pct": (
            rolling["rolling_profitable_window_ratio"] >= 0.50
        ),
        "average_rolling_drawdown_lte_10pct": (
            rolling["rolling_average_drawdown_percent"] <= 10.0
        ),
        "oos_to_is_return_ratio_gte_0_25": (
            base["oos_to_is_return_ratio"] >= 0.25
        ),
        "positive_holdout_return": holdout["period_return"] > 0.0,
        "holdout_profit_factor_gte_1_10": (
            (
                math.inf
                if holdout["profit_factor"] == "inf"
                else float(holdout["profit_factor"])
            ) >= 1.10
        ),
        "holdout_drawdown_lte_10pct": (
            holdout["max_drawdown_percent"] <= 10.0
        ),
        "holdout_stress_1_5x_nonnegative": (
            stress15["holdout"]["period_return"] >= 0.0
        ),
        "holdout_stress_2x_nonnegative": (
            stress2["holdout"]["period_return"] >= 0.0
        ),
    }

    control_checks = {
        "research_return_not_below_fixed": (
            research["period_return"]
            >= control["research"]["period_return"]
        ),
        "research_drawdown_not_worse_vs_fixed": (
            research["max_drawdown_percent"]
            <= control["research"]["max_drawdown_percent"]
        ),
        "research_profit_factor_not_below_fixed": (
            (
                math.inf
                if research["profit_factor"] == "inf"
                else float(research["profit_factor"])
            )
            >= (
                math.inf
                if control["research"]["profit_factor"] == "inf"
                else float(control["research"]["profit_factor"])
            )
        ),
        "rolling_pf_not_below_fixed": (
            rolling["rolling_min_profit_factor"]
            >= control["rolling_summary"]["rolling_min_profit_factor"]
        ),
        "rolling_profitable_ratio_not_below_fixed": (
            rolling["rolling_profitable_window_ratio"]
            >= control["rolling_summary"]["rolling_profitable_window_ratio"]
        ),
        "rolling_average_drawdown_not_worse_vs_fixed": (
            rolling["rolling_average_drawdown_percent"]
            <= control["rolling_summary"]["rolling_average_drawdown_percent"]
        ),
        "oos_to_is_not_below_fixed": (
            base["oos_to_is_return_ratio"]
            >= control["oos_to_is_return_ratio"]
        ),
        "holdout_return_not_below_fixed": (
            holdout["period_return"]
            >= control["holdout"]["period_return"]
        ),
        "holdout_profit_factor_not_below_fixed": (
            (
                math.inf
                if holdout["profit_factor"] == "inf"
                else float(holdout["profit_factor"])
            )
            >= (
                math.inf
                if control["holdout"]["profit_factor"] == "inf"
                else float(control["holdout"]["profit_factor"])
            )
        ),
        "holdout_drawdown_not_worse_vs_fixed": (
            holdout["max_drawdown_percent"]
            <= control["holdout"]["max_drawdown_percent"]
        ),
    }

    return {
        "absolute": challenger_gates,
        "non_deterioration_vs_fixed_50_50": control_checks,
        "all_absolute_passed": all(challenger_gates.values()),
        "all_non_deterioration_passed": all(control_checks.values()),
        "all_passed": (
            all(challenger_gates.values())
            and all(control_checks.values())
        ),
    }


def _evaluate_scenario(
    challenger_rows: list[dict],
    control_rows: list[dict],
    research_end: int,
) -> tuple[dict, dict]:
    challenger_values = [row["net_return"] for row in challenger_rows]
    control_values = [row["net_return"] for row in control_rows]

    challenger_summary = _summary(
        challenger_values,
        research_end,
    )
    control_summary = _summary(
        control_values,
        research_end,
    )

    return challenger_summary, control_summary


def run_trial(
    trend_coverage_path: str | Path,
    cs_coverage_path: str | Path,
    trend_preregistration_path: str | Path,
    cs_preregistration_path: str | Path,
    output_path: str | Path,
) -> dict:
    if settings.PAPER_ONLY is not True:
        raise RuntimeError("T041 requires PAPER_ONLY=True.")
    if settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("T041 requires LIVE_TRADING_ENABLED=False.")

    trend_prereg = _verify_preregistration(
        Path(trend_preregistration_path),
        TREND_UNIVERSE,
    )
    cs_prereg = _verify_preregistration(
        Path(cs_preregistration_path),
        CS_UNIVERSE,
    )

    if set(trend_prereg["symbols"]).intersection(cs_prereg["symbols"]):
        raise ValueError("T041 trend and cross-sectional universes overlap.")

    trend_coverage, trend_assets = _load_coverage(
        Path(trend_coverage_path),
        trend_prereg,
    )
    cs_coverage, cs_assets = _load_coverage(
        Path(cs_coverage_path),
        cs_prereg,
    )

    if (
        trend_coverage["common_calendar_count"] < TARGET_COUNT
        or cs_coverage["common_calendar_count"] < TARGET_COUNT
    ):
        raise ValueError("T041 coverage calendar is below the formal target.")

    trend_weights = _build_weight_path(
        trend_assets,
        "sma_50_200_inverse_vol",
    )
    cs_weights = _cs_weights(cs_assets)

    trend_rows = _sleeve_rows(trend_assets, trend_weights)
    cs_rows = _sleeve_rows(cs_assets, cs_weights)

    trend_by_time = {row["timestamp"]: row for row in trend_rows}
    cs_by_time = {row["timestamp"]: row for row in cs_rows}
    common = sorted(
        set(trend_by_time).intersection(cs_by_time)
    )

    if len(common) < 3300:
        raise ValueError(f"T041 has too few common returns: {len(common)}")

    rows = tuple(
        {
            "timestamp": timestamp,
            "trend_gross": trend_by_time[timestamp]["gross_return"],
            "trend_turnover": trend_by_time[timestamp]["turnover"],
            "cs_gross": cs_by_time[timestamp]["gross_return"],
            "cs_turnover": cs_by_time[timestamp]["turnover"],
        }
        for timestamp in common
    )

    research_end = int(len(rows) * RESEARCH_SHARE)
    scenarios = {}
    baseline_reference = None

    for scenario, multiplier in COST_SCENARIOS:
        challenger_rows = _simulate(
            rows,
            challenger=True,
            cost_multiplier=multiplier,
        )
        control_rows = _simulate(
            rows,
            challenger=False,
            cost_multiplier=multiplier,
        )

        challenger_values = [row["net_return"] for row in challenger_rows]
        control_values = [row["net_return"] for row in control_rows]

        challenger_summary = _summary(
            challenger_values,
            research_end,
        )
        control_summary = _summary(
            control_values,
            research_end,
        )

        scenarios[scenario] = {
            "challenger": challenger_summary,
            "fixed_50_50_control": control_summary,
        }

        if scenario == "base":
            baseline_reference = (
                challenger_summary,
                control_summary,
            )

    challenger_base, control_base = baseline_reference
    gate_input = {
        "base": {
            **challenger_base,
            "rolling_summary": {
                "rolling_min_profit_factor": challenger_base[
                    "rolling_min_profit_factor"
                ],
                "rolling_profitable_window_ratio": challenger_base[
                    "rolling_profitable_window_ratio"
                ],
                "rolling_average_drawdown_percent": challenger_base[
                    "rolling_average_drawdown_percent"
                ],
            },
        },
        "stress_1_5x_cost": scenarios["stress_1_5x_cost"]["challenger"],
        "stress_2x_cost": scenarios["stress_2x_cost"]["challenger"],
    }
    control_input = {
        "research": control_base["research"],
        "holdout": control_base["holdout"],
        "oos_to_is_return_ratio": control_base[
            "oos_to_is_return_ratio"
        ],
        "rolling_summary": {
            "rolling_min_profit_factor": control_base[
                "rolling_min_profit_factor"
            ],
            "rolling_profitable_window_ratio": control_base[
                "rolling_profitable_window_ratio"
            ],
            "rolling_average_drawdown_percent": control_base[
                "rolling_average_drawdown_percent"
            ],
        },
    }

    evaluation = _gates(
        gate_input,
        control_input,
    )

    report = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "status": (
            "PASSED_NO_AUTO_PROMOTION"
            if evaluation["all_passed"]
            else "BLOCKED"
        ),
        "scientific_outcome": (
            "EVIDENCE_GATED_PASS"
            if evaluation["all_passed"]
            else "NO_PROMOTION_EVIDENCE"
        ),
        "source": {
            "trend_universe": TREND_UNIVERSE,
            "cs_universe": CS_UNIVERSE,
            "trend_coverage_fingerprint": trend_coverage[
                "coverage_fingerprint"
            ],
            "cs_coverage_fingerprint": cs_coverage[
                "coverage_fingerprint"
            ],
            "common_return_count": len(rows),
            "research_return_count": research_end,
            "holdout_return_count": len(rows) - research_end,
        },
        "methodology": {
            "trend_signal": "sma_50_200_inverse_vol",
            "cs_signal": "12-1 momentum top-2 long-only",
            "baseline_allocation": "fixed_50_50",
            "challenger_allocation": "63-session covariance-aware minimum variance",
            "covariance_window_sessions": COVARIANCE_WINDOW,
            "rebalance": "first realization row of each calendar month",
            "minimum_variance_clamp": [0.0, 1.0],
            "initial_allocation_before_63_sessions": 0.5,
            "parameter_search": False,
            "weight_search": False,
            "holdout_used_for_selection": False,
            "point_in_time": True,
            "costs": {
                "fee_rate": FEE_RATE,
                "slippage_rate": SLIPPAGE_RATE,
                "scenarios": [name for name, _ in COST_SCENARIOS],
                "allocation_turnover_charged": True,
            },
        },
        "scenarios": scenarios,
        "evaluation": evaluation,
        "safety": SAFETY,
    }

    report["report_fingerprint"] = _fingerprint(report)

    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend-coverage", required=True)
    parser.add_argument("--cs-coverage", required=True)
    parser.add_argument("--trend-preregistration", required=True)
    parser.add_argument("--cs-preregistration", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_trial(
        args.trend_coverage,
        args.cs_coverage,
        args.trend_preregistration,
        args.cs_preregistration,
        args.output,
    )

    print("T041_STATUS:", report["status"])
    print("T041_REPORT_FINGERPRINT:", report["report_fingerprint"])
    print("T041_RESEARCH_RETURN:", report["scenarios"]["base"]["challenger"]["research"]["period_return"])
    print("T041_HOLDOUT_RETURN:", report["scenarios"]["base"]["challenger"]["holdout"]["period_return"])
    print("T041_HOLDOUT_MAX_DD:", report["scenarios"]["base"]["challenger"]["holdout"]["max_drawdown_percent"])
    print("T041_PAPER_ONLY:", report["safety"]["paper_only"])
    print("T041_LIVE_TRADING_ENABLED:", report["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
