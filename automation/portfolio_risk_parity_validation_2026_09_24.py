"""Research-only validation of fixed sleeve risk-parity allocation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from automation.candidate_validation_50_50_vol_budget import (
    _assets,
    _manifest,
    _return_rows,
    _cs_weights,
    _yahoo_adjclose,
)
from automation.cross_asset_trend_replication import _build_weight_path
from config import settings
from portfolio.allocator import FixedPortfolioAllocator
from research.asset_universes import get_universe
from research.fixed_sleeve_risk_parity import lagged_inverse_vol_weights
from validation.research_gates import ResearchGateConfig

TREND_UNIVERSE = "validation_2026_09_24_portfolio_risk_parity_trend"
CS_UNIVERSE = "validation_2026_09_24_portfolio_risk_parity_cs"
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
VOL_WINDOW = 63
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_SCENARIOS = (
    ("base", 1.0),
    ("stress_1_5x_cost", 1.5),
    ("stress_2x_cost", 2.0),
)
TREND_ASSETS = ("IBM", "GE", "CAT", "MMM", "HD", "LOW", "UNP", "NKE")
CS_ASSETS = ("BAC", "JPM", "GS", "MS", "C")


def _canon(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _pf(value: float | str) -> float:
    return float("inf") if value == "inf" else float(value)


def _prepare(
    trend_data_dir: Path,
    trend_manifest_path: Path,
    cs_data_dir: Path,
    cs_manifest_path: Path,
):
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    trend_manifest = _manifest(trend_manifest_path, TREND_UNIVERSE)
    cs_manifest = _manifest(cs_manifest_path, CS_UNIVERSE)
    trend = _assets(trend_data_dir, trend_manifest)
    cs = _assets(cs_data_dir, cs_manifest)

    if set(trend) & set(cs):
        raise ValueError("Trend and CS universes are not symbol-disjoint.")

    if tuple(get_universe(TREND_UNIVERSE).symbols) != TREND_ASSETS:
        raise ValueError("Trend universe registration mismatch.")
    if tuple(get_universe(CS_UNIVERSE).symbols) != CS_ASSETS:
        raise ValueError("CS universe registration mismatch.")

    trend_weights = _build_weight_path(trend, "sma_50_200_inverse_vol")
    cs_weights = _cs_weights(cs)

    all_assets = {**trend, **cs}
    adjusted = {
        symbol: _yahoo_adjclose(symbol, bars[0].timestamp, bars[-1].timestamp)
        for symbol, bars in all_assets.items()
    }

    trend_adj = {symbol: adjusted[symbol] for symbol in trend}
    cs_adj = {symbol: adjusted[symbol] for symbol in cs}

    trend_rows = {
        row["timestamp"]: row
        for row in _return_rows(trend, trend_weights, trend_adj)
    }
    cs_rows = {
        row["timestamp"]: row
        for row in _return_rows(cs, cs_weights, cs_adj)
    }
    common = sorted(set(trend_rows) & set(cs_rows))
    if len(common) != RESEARCH_COUNT + HOLDOUT_COUNT:
        raise ValueError(f"Unexpected common return count: {len(common)}")

    rows = []
    for timestamp in common:
        trend_row = trend_rows[timestamp]
        cs_row = cs_rows[timestamp]
        rows.append(
            {
                "timestamp": timestamp,
                "trend_gross_return": float(trend_row["gross_open"]),
                "trend_total_return": float(
                    trend_row["gross_open"]
                    + trend_row["gross_adjusted_close"]
                    - trend_row["gross_close"]
                ),
                "trend_turnover": float(trend_row["turnover"]),
                "cs_gross_return": float(cs_row["gross_open"]),
                "cs_total_return": float(
                    cs_row["gross_open"]
                    + cs_row["gross_adjusted_close"]
                    - cs_row["gross_close"]
                ),
                "cs_turnover": float(cs_row["turnover"]),
            }
        )

    return trend_manifest, cs_manifest, tuple(rows)


def _simulate(
    rows: tuple[dict, ...],
    multiplier: float,
    dynamic: bool,
) -> list[dict]:
    trend_returns = tuple(row["trend_gross_return"] for row in rows)
    cs_returns = tuple(row["cs_gross_return"] for row in rows)
    allocations = (
        lagged_inverse_vol_weights(trend_returns, cs_returns)
        if dynamic
        else tuple(
            {"trend": 0.5, "cross_sectional": 0.5}
            for _ in rows
        )
    )

    previous = {"trend": 0.5, "cross_sectional": 0.5}
    cost_rate = (FEE_RATE + SLIPPAGE_RATE) * multiplier
    allocator = FixedPortfolioAllocator()
    output = []

    for index, row in enumerate(rows):
        weights = allocations[index]
        allocator.validate(weights)

        trend_weight = weights["trend"]
        cs_weight = weights["cross_sectional"]
        strategy_gross = (
            trend_weight * row["trend_gross_return"]
            + cs_weight * row["cs_gross_return"]
        )
        sleeve_turnover = (
            trend_weight * row["trend_turnover"]
            + cs_weight * row["cs_turnover"]
        )
        allocation_turnover = (
            abs(trend_weight - previous["trend"])
            + abs(cs_weight - previous["cross_sectional"])
            if dynamic
            else 0.0
        )
        total_turnover = sleeve_turnover + allocation_turnover
        net_return = strategy_gross - cost_rate * total_turnover
        strategy_total = (
            trend_weight * row["trend_total_return"]
            + cs_weight * row["cs_total_return"]
        )

        output.append(
            {
                "timestamp": row["timestamp"],
                "trend_weight": trend_weight,
                "cross_sectional_weight": cs_weight,
                "strategy_gross_return": strategy_gross,
                "strategy_total_return": strategy_total,
                "sleeve_turnover": sleeve_turnover,
                "allocation_turnover": allocation_turnover,
                "total_turnover": total_turnover,
                "net_return": net_return,
            }
        )
        previous = weights

    return output


def _stats(rows: list[dict]) -> dict:
    if not rows:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "day_count": 0,
            "turnover": 0.0,
            "allocation_turnover": 0.0,
            "average_trend_weight": 0.0,
            "average_cross_sectional_weight": 0.0,
        }

    equity = peak = 1.0
    gross_profit = gross_loss = 0.0
    max_drawdown = 0.0
    turnover = allocation_turnover = 0.0
    trend_weights = []
    cs_weights = []

    for row in rows:
        value = float(row["net_return"])
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_drawdown = max(
            max_drawdown,
            1.0 - equity / peak if equity > 0.0 else 1.0,
        )
        if value > 0.0:
            gross_profit += value
        elif value < 0.0:
            gross_loss -= value
        turnover += float(row["total_turnover"])
        allocation_turnover += float(row["allocation_turnover"])
        trend_weights.append(float(row["trend_weight"]))
        cs_weights.append(float(row["cross_sectional_weight"]))

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0.0
        else ("inf" if gross_profit > 0.0 else 0.0)
    )
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_drawdown * 100.0,
        "profit_factor": profit_factor,
        "day_count": len(rows),
        "turnover": turnover,
        "allocation_turnover": allocation_turnover,
        "average_trend_weight": sum(trend_weights) / len(trend_weights),
        "average_cross_sectional_weight": sum(cs_weights) / len(cs_weights),
    }


def _rolling(rows: list[dict]) -> list[dict]:
    width = RESEARCH_COUNT // 5
    windows = []
    start = 0
    for index in range(5):
        end = RESEARCH_COUNT if index == 4 else start + width
        windows.append(
            {"window_index": index + 1, **_stats(rows[start:end])}
        )
        start = end
    return windows


def _scenario(rows: tuple[dict, ...], multiplier: float) -> dict:
    simulations = {
        "fixed_50_50": _simulate(rows, multiplier, False),
        "dynamic_inverse_vol_63": _simulate(rows, multiplier, True),
    }
    result = {}
    for name, simulated in simulations.items():
        research = _stats(simulated[:RESEARCH_COUNT])
        holdout = _stats(simulated[RESEARCH_COUNT:])
        rolling = _rolling(simulated)
        result[name] = {
            "research": research,
            "holdout": holdout,
            "rolling_windows": rolling,
            "rolling_summary": {
                "window_count": len(rolling),
                "profitable_windows": sum(
                    item["period_return"] > 0.0 for item in rolling
                ),
                "profitable_window_ratio": (
                    sum(item["period_return"] > 0.0 for item in rolling)
                    / len(rolling)
                ),
            },
            "oos_to_is_return_ratio": (
                holdout["period_return"] / research["period_return"]
                if research["period_return"] > 0.0
                else 0.0
            ),
        }
    return result


def _gates(scenarios: dict) -> dict:
    cfg = ResearchGateConfig()
    candidate = scenarios["base"]["dynamic_inverse_vol_63"]
    baseline = scenarios["base"]["fixed_50_50"]
    stress15 = scenarios["stress_1_5x_cost"]["dynamic_inverse_vol_63"]["holdout"]
    stress2 = scenarios["stress_2x_cost"]["dynamic_inverse_vol_63"]["holdout"]

    checks = {
        "research_return_positive": candidate["research"]["period_return"] > 0.0,
        "research_drawdown": candidate["research"]["max_drawdown_percent"] <= cfg.maximum_drawdown_percent,
        "research_profit_factor": _pf(candidate["research"]["profit_factor"]) >= cfg.minimum_profit_factor,
        "rolling_profitable_window_ratio": candidate["rolling_summary"]["profitable_window_ratio"] >= cfg.minimum_profitable_window_ratio,
        "oos_to_is_return_ratio": candidate["oos_to_is_return_ratio"] >= cfg.minimum_oos_to_is_return_ratio,
        "holdout_return_positive": candidate["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor": _pf(candidate["holdout"]["profit_factor"]) >= cfg.minimum_profit_factor,
        "holdout_drawdown": candidate["holdout"]["max_drawdown_percent"] <= cfg.maximum_drawdown_percent,
        "stress_1_5x_nonnegative": stress15["period_return"] >= 0.0,
        "stress_2x_nonnegative": stress2["period_return"] >= 0.0,
        "research_return_not_below_50_50": candidate["research"]["period_return"] >= baseline["research"]["period_return"],
        "research_drawdown_not_above_50_50": candidate["research"]["max_drawdown_percent"] <= baseline["research"]["max_drawdown_percent"],
        "research_profit_factor_not_below_50_50": _pf(candidate["research"]["profit_factor"]) >= _pf(baseline["research"]["profit_factor"]),
        "holdout_return_not_below_50_50": candidate["holdout"]["period_return"] >= baseline["holdout"]["period_return"],
        "holdout_drawdown_not_above_50_50": candidate["holdout"]["max_drawdown_percent"] <= baseline["holdout"]["max_drawdown_percent"],
        "holdout_profit_factor_not_below_50_50": _pf(candidate["holdout"]["profit_factor"]) >= _pf(baseline["holdout"]["profit_factor"]),
    }
    return {
        "thresholds": {
            "minimum_profit_factor": cfg.minimum_profit_factor,
            "maximum_drawdown_percent": cfg.maximum_drawdown_percent,
            "minimum_profitable_window_ratio": cfg.minimum_profitable_window_ratio,
            "minimum_oos_to_is_return_ratio": cfg.minimum_oos_to_is_return_ratio,
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }


def run_validation(
    *,
    trend_data_dir: Path,
    trend_manifest_path: Path,
    cs_data_dir: Path,
    cs_manifest_path: Path,
    output: Path,
) -> dict:
    trend_manifest, cs_manifest, rows = _prepare(
        trend_data_dir,
        trend_manifest_path,
        cs_data_dir,
        cs_manifest_path,
    )

    scenarios = {
        name: _scenario(rows, multiplier)
        for name, multiplier in COST_SCENARIOS
    }
    gates = _gates(scenarios)
    report = {
        "schema_version": 1,
        "trial_id": "T-2026-09-24-022",
        "status": "COMPLETED",
        "research_only": True,
        "selection_used": False,
        "parameter_search_used": False,
        "data_scope": {
            "trend_universe": TREND_UNIVERSE,
            "trend_symbols": list(get_universe(TREND_UNIVERSE).symbols),
            "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
            "cs_universe": CS_UNIVERSE,
            "cs_symbols": list(get_universe(CS_UNIVERSE).symbols),
            "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
            "market_candles_per_asset": TARGET_COUNT,
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "common_return_count": len(rows),
            "fully_symbol_disjoint_validation_sets": True,
        },
        "allocator": {
            "method": "lagged inverse realized volatility",
            "lookback_sessions": VOL_WINDOW,
            "fallback_weights": {"trend": 0.5, "cross_sectional": 0.5},
            "gross_exposure": 1.0,
            "optimization": False,
            "selection": False,
        },
        "methodology": {
            "fixed_signal_architecture": "SMA 50/200 inverse-vol Trend + 12-1 Top-2 Cross-Sectional Momentum",
            "portfolio_reference": "fixed 50/50",
            "execution": "existing sleeve point-in-time return path",
            "cost_scenarios": [name for name, _ in COST_SCENARIOS],
            "holdout_used_for_selection": False,
            "strategy_variants": 1,
            "parameter_search": False,
            "orders_enabled": False,
        },
        "scenarios": scenarios,
        "decision": gates,
        "safety": {
            "paper_only": settings.PAPER_ONLY,
            "live_trading_enabled": settings.LIVE_TRADING_ENABLED,
            "orders_enabled": False,
        },
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
    }
    report["report_fingerprint"] = _fp(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend-data-dir", required=True)
    parser.add_argument("--trend-manifest", required=True)
    parser.add_argument("--cs-data-dir", required=True)
    parser.add_argument("--cs-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_validation(
        trend_data_dir=Path(args.trend_data_dir),
        trend_manifest_path=Path(args.trend_manifest),
        cs_data_dir=Path(args.cs_data_dir),
        cs_manifest_path=Path(args.cs_manifest),
        output=Path(args.output),
    )
    print("PORTFOLIO_RISK_PARITY_STATUS:", report["status"])
    print("PORTFOLIO_RISK_PARITY_DECISION:", json.dumps(report["decision"], sort_keys=True))
    print("PORTFOLIO_RISK_PARITY_SCENARIOS:", json.dumps(report["scenarios"], sort_keys=True))
    print("PORTFOLIO_RISK_PARITY_REPORT_FINGERPRINT:", report["report_fingerprint"])


if __name__ == "__main__":
    main()
