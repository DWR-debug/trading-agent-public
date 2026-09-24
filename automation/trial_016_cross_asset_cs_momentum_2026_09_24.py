"""Pre-registered Trial 016: cross-asset 12-1 cross-sectional momentum.

Research only. No optimization, no holdout selection, no leverage, no shorting,
and no broker/order path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from backtesting.models import Candle
from config import settings
from data.market_store import MarketDataStore

UNIVERSE = "validation_2026_09_24_sixteenth_cross_asset_cs"
ASSETS = ("DBA", "DBB", "FXA", "FXY", "MUB", "SHV", "EMB", "BWX")
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700

LOOKBACK = 252
SKIP = 21
REBALANCE_DAYS = 21
TOP_N = 2

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
BASE_COST = FEE_RATE + SLIPPAGE_RATE
STRESS_MULTIPLIER = 2.0


def _fingerprint(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("universe") != UNIVERSE:
        raise ValueError("Unexpected Trial 016 universe.")
    if manifest.get("target_count") != TARGET_COUNT:
        raise ValueError("Unexpected Trial 016 target count.")
    if tuple(item["symbol"] for item in manifest.get("datasets", [])) != ASSETS:
        raise ValueError("Manifest symbols do not match Trial 016 preregistration.")
    if not all(item["candle_count"] == TARGET_COUNT for item in manifest["datasets"]):
        raise ValueError("Trial 016 requires 3500 candles per symbol.")
    if manifest.get("calendar_alignment", {}).get("mode") != "timestamp_intersection_tail":
        raise ValueError("Trial 016 requires timestamp intersection alignment.")
    if manifest.get("calendar_alignment", {}).get("aligned_candle_count") != TARGET_COUNT:
        raise ValueError("Trial 016 common calendar is not 3500 candles.")
    if manifest.get("safety", {}).get("paper_only") is not True:
        raise ValueError("Paper-only safety contract missing.")
    if manifest.get("safety", {}).get("live_trading_enabled") is not False:
        raise ValueError("Live-trading safety contract missing.")
    return manifest


def _load_assets(data_dir: Path, manifest: dict) -> dict[str, list[Candle]]:
    store = MarketDataStore(data_dir)
    assets: dict[str, list[Candle]] = {}

    for item in manifest["datasets"]:
        symbol = item["symbol"]
        candles = store.load(symbol, "1d")
        if len(candles) != TARGET_COUNT:
            raise ValueError(f"{symbol}: expected {TARGET_COUNT} candles.")
        assets[symbol] = candles

    common = set(c.timestamp for c in assets[ASSETS[0]])
    for symbol in ASSETS[1:]:
        common &= {c.timestamp for c in assets[symbol]}
    common_tail = sorted(common)[-TARGET_COUNT:]
    if len(common_tail) != TARGET_COUNT:
        raise ValueError("Trial 016 common timestamp intersection is too short.")

    for symbol in ASSETS:
        by_ts = {c.timestamp: c for c in assets[symbol]}
        assets[symbol] = [by_ts[ts] for ts in common_tail]

    return assets


def _weights(
    assets: dict[str, list[Candle]],
    strategy: str,
    decision_index: int,
) -> dict[str, float]:
    if strategy == "equal_weight_buy_and_hold":
        return {symbol: 1.0 / len(ASSETS) for symbol in ASSETS}

    if decision_index < LOOKBACK + SKIP:
        return {symbol: 0.0 for symbol in ASSETS}

    if strategy == "cs_momentum_252_long_only_top2":
        anchor = decision_index - SKIP
        origin = anchor - LOOKBACK
        scores = {
            symbol: (
                assets[symbol][anchor].close
                / assets[symbol][origin].close
                - 1.0
            )
            for symbol in ASSETS
        }
        ranking = sorted(scores, key=scores.get, reverse=True)
        winners = set(ranking[:TOP_N])
        return {
            symbol: 1.0 / TOP_N if symbol in winners else 0.0
            for symbol in ASSETS
        }

    if strategy == "sma_50_200_reference":
        if decision_index < 199:
            return {symbol: 0.0 for symbol in ASSETS}
        raw = {}
        for symbol in ASSETS:
            bars = assets[symbol]
            fast = sum(
                bars[i].close
                for i in range(decision_index - 49, decision_index + 1)
            ) / 50.0
            slow = sum(
                bars[i].close
                for i in range(decision_index - 199, decision_index + 1)
            ) / 200.0
            raw[symbol] = 1.0 if fast > slow else 0.0
        active = sum(raw.values())
        return {
            symbol: raw[symbol] / active if active else 0.0
            for symbol in ASSETS
        }

    raise ValueError(f"Unknown strategy: {strategy}")


def _daily_returns(
    assets: dict[str, list[Candle]],
    strategy: str,
    cost_multiplier: float,
) -> list[float]:
    previous = {symbol: 0.0 for symbol in ASSETS}
    current = {symbol: 0.0 for symbol in ASSETS}
    returns: list[float] = []

    for decision_index in range(TARGET_COUNT - 2):
        if strategy == "equal_weight_buy_and_hold" or decision_index % REBALANCE_DAYS == 0:
            current = _weights(assets, strategy, decision_index)

        portfolio_return = 0.0
        turnover = 0.0

        for symbol in ASSETS:
            target = current[symbol]
            bars = assets[symbol]
            market_return = (
                bars[decision_index + 2].open
                / bars[decision_index + 1].open
                - 1.0
            )
            portfolio_return += target * market_return
            turnover += abs(target - previous[symbol])
            previous[symbol] = target

        returns.append(portfolio_return - BASE_COST * cost_multiplier * turnover)

    return returns


def _stats(values: list[float]) -> dict:
    if not values:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "positive_return_ratio": 0.0,
            "count": 0,
        }

    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    gross_profit = 0.0
    gross_loss = 0.0

    for value in values:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak)
        if value > 0.0:
            gross_profit += value
        elif value < 0.0:
            gross_loss -= value

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "positive_return_ratio": sum(v > 0.0 for v in values) / len(values),
        "count": len(values),
    }


def _metrics(returns: list[float]) -> dict:
    boundaries = [round(i * RESEARCH_COUNT / 5) for i in range(6)]
    rolling = [
        _stats(returns[boundaries[i] : boundaries[i + 1]])
        for i in range(5)
    ]
    return {
        "research": _stats(returns[:RESEARCH_COUNT]),
        "holdout": _stats(returns[RESEARCH_COUNT : RESEARCH_COUNT + HOLDOUT_COUNT]),
        "rolling_research": rolling,
        "rolling_positive_window_count": sum(x["period_return"] > 0.0 for x in rolling),
        "rolling_positive_window_ratio": sum(
            x["period_return"] > 0.0 for x in rolling
        ) / len(rolling),
    }


def run(data_dir: Path, manifest_path: Path, output_path: Path) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    manifest = _load_manifest(manifest_path)
    assets = _load_assets(data_dir, manifest)

    strategies = {
        "cs_momentum_252_long_only_top2",
        "sma_50_200_reference",
        "equal_weight_buy_and_hold",
    }
    scenarios = {
        "base": 1.0,
        "stress_2x_cost": STRESS_MULTIPLIER,
    }

    results: dict[str, dict[str, dict]] = {}
    for scenario, multiplier in scenarios.items():
        scenario_results: dict[str, dict] = {}
        returns_by_strategy: dict[str, list[float]] = {}
        for strategy in strategies:
            returns = _daily_returns(assets, strategy, multiplier)
            returns_by_strategy[strategy] = returns
            scenario_results[strategy] = _metrics(returns)

        blend = [
            (a + b) / 2.0
            for a, b in zip(
                returns_by_strategy["cs_momentum_252_long_only_top2"],
                returns_by_strategy["sma_50_200_reference"],
            )
        ]
        scenario_results["blend_50_50"] = _metrics(blend)
        results[scenario] = scenario_results

    report = {
        "schema_version": 1,
        "trial_id": "T-2026-09-24-016",
        "diagnostic_type": "trial_016_cross_asset_cs_momentum",
        "status": "COMPLETED",
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "preregistration": {
            "document": "docs/trial_016_cross_asset_cs_momentum_preregistration_2026_09_24.md",
            "selection_after_results": False,
            "parameter_optimization": False,
            "holdout_selection": False,
        },
        "source": {
            "universe": UNIVERSE,
            "symbols": list(ASSETS),
            "target_candles": TARGET_COUNT,
            "common_returns": TARGET_COUNT - 2,
            "research_count": RESEARCH_COUNT,
            "holdout_count": HOLDOUT_COUNT,
            "fully_symbol_disjoint_from_master_universes": True,
            "manifest_fingerprint": manifest["manifest_fingerprint"],
        },
        "methodology": {
            "formation_sessions": LOOKBACK,
            "skip_sessions": SKIP,
            "rebalance_sessions": REBALANCE_DAYS,
            "top_n": TOP_N,
            "long_only": True,
            "leverage": 1.0,
            "base_cost_rate": BASE_COST,
            "stress_multiplier": STRESS_MULTIPLIER,
            "blend_weight_cs": 0.50,
            "blend_weight_sma": 0.50,
            "optimization_used": False,
            "holdout_selection_used": False,
        },
        "results": results,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    report["report_fingerprint"] = _fingerprint(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run(Path(args.data_dir), Path(args.manifest), Path(args.output))
    print("TRIAL_016_STATUS:", report["status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    for scenario, values in report["results"].items():
        for strategy, metrics in values.items():
            print(
                scenario,
                strategy,
                "RESEARCH_RETURN=",
                metrics["research"]["period_return"],
                "RESEARCH_DD=",
                metrics["research"]["max_drawdown_percent"],
                "HOLDOUT_RETURN=",
                metrics["holdout"]["period_return"],
                "HOLDOUT_DD=",
                metrics["holdout"]["max_drawdown_percent"],
                "ROLLING_POSITIVE_RATIO=",
                metrics["rolling_positive_window_ratio"],
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
