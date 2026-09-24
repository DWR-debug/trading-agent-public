"""Pre-registered Trial 015: fixed long-only short-horizon mean reversion.

Research-only. No optimization, selection, leverage, shorting, production mutation,
or order execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from backtesting.models import Candle
from data.market_store import MarketDataStore
from config import settings
from strategies.mean_reversion import MeanReversionStrategy
from strategies.signals import SignalType

UNIVERSE = "validation_2026_09_24_fifteenth_mean_reversion"
SYMBOLS = ("EWC", "EWH", "EWI", "EWK", "EWN", "EWP", "EWY", "EWT")
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
WINDOW = 5
THRESHOLD = 0.02
BASE_COST = 0.0015
STRESS_MULTIPLIER = 2.0


def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("universe") != UNIVERSE:
        raise ValueError("Unexpected Trial 015 universe.")
    if manifest.get("target_count") != TARGET_COUNT:
        raise ValueError("Unexpected Trial 015 target count.")
    datasets = manifest.get("datasets") or []
    if tuple(item["symbol"] for item in datasets) != SYMBOLS:
        raise ValueError("Manifest symbols do not match preregistration.")
    if not all(item["candle_count"] == TARGET_COUNT for item in datasets):
        raise ValueError("Not every Trial 015 asset has the target candle count.")
    alignment = manifest.get("calendar_alignment", {})
    if alignment.get("mode") != "timestamp_intersection_tail":
        raise ValueError("Trial 015 requires timestamp-intersection alignment.")
    if alignment.get("aligned_candle_count") != TARGET_COUNT:
        raise ValueError("Trial 015 common calendar length is not 3500.")
    if manifest.get("safety", {}).get("paper_only") is not True:
        raise ValueError("Paper-only safety contract missing from manifest.")
    if manifest.get("safety", {}).get("live_trading_enabled") is not False:
        raise ValueError("Live-trading safety contract missing from manifest.")
    return manifest


def _load_assets(data_dir: Path, manifest: dict) -> dict[str, list[Candle]]:
    assets: dict[str, list[Candle]] = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        store = MarketDataStore(data_dir)
        candles = store.load(symbol, "1d")
        if len(candles) != TARGET_COUNT:
            raise ValueError(f"{symbol}: expected {TARGET_COUNT} candles.")
        assets[symbol] = candles
    common = set(c.timestamp for c in assets[SYMBOLS[0]])
    for symbol in SYMBOLS[1:]:
        common &= {c.timestamp for c in assets[symbol]}
    common_tail = sorted(common)[-TARGET_COUNT:]
    if len(common_tail) != TARGET_COUNT:
        raise ValueError("Trial 015 common timestamp intersection is too short.")
    for symbol in SYMBOLS:
        by_ts = {c.timestamp: c for c in assets[symbol]}
        assets[symbol] = [by_ts[ts] for ts in common_tail]
    return assets


def _target_path(prices: list[float], strategy: MeanReversionStrategy) -> list[float]:
    state = 0.0
    targets = [0.0] * len(prices)
    for i in range(len(prices)):
        if i + 1 >= strategy.window:
            signal = strategy.generate_signal_validated("asset", prices[: i + 1])
            if signal.signal is SignalType.BUY:
                state = 1.0
            elif signal.signal is SignalType.SELL:
                state = 0.0
        targets[i] = state
    return targets


def _portfolio_returns(
    assets: dict[str, list[Candle]],
    targets: dict[str, list[float]],
    cost_rate: float,
) -> list[float]:
    rows: list[float] = []
    previous = {symbol: 0.0 for symbol in SYMBOLS}
    for i in range(TARGET_COUNT - 2):
        active = {symbol: targets[symbol][i] for symbol in SYMBOLS}
        n_active = sum(value > 0.0 for value in active.values())
        portfolio = 0.0
        for symbol in SYMBOLS:
            weight = active[symbol] / n_active if n_active else 0.0
            asset_return = (
                assets[symbol][i + 2].open / assets[symbol][i + 1].open - 1.0
            )
            portfolio += weight * asset_return
        turnover = sum(
            abs((active[symbol] / n_active if n_active else 0.0) - previous[symbol])
            for symbol in SYMBOLS
        )
        rows.append(portfolio - cost_rate * turnover)
        previous = {
            symbol: active[symbol] / n_active if n_active else 0.0
            for symbol in SYMBOLS
        }
    return rows


def _metrics(returns: list[float], split: int) -> dict:
    def segment(values: list[float]) -> dict:
        equity = 1.0
        peak = 1.0
        max_dd = 0.0
        gains = 0.0
        losses = 0.0
        for value in values:
            equity *= 1.0 + value
            peak = max(peak, equity)
            max_dd = max(max_dd, 1.0 - equity / peak)
            if value > 0.0:
                gains += value
            elif value < 0.0:
                losses += -value
        return {
            "return": equity - 1.0,
            "max_drawdown_percent": max_dd * 100.0,
            "profit_factor": gains / losses if losses else None,
            "positive_return_ratio": (
                sum(v > 0.0 for v in values) / len(values) if values else 0.0
            ),
            "count": len(values),
        }

    boundaries = [round(i * split / 5) for i in range(6)]
    rolling = [
        segment(returns[boundaries[i] : boundaries[i + 1]])
        for i in range(5)
    ]
    return {
        "research": segment(returns[:split]),
        "holdout": segment(returns[split : split + HOLDOUT_COUNT]),
        "rolling_research": rolling,
    }


def run(data_dir: Path, manifest_path: Path, output_path: Path) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    manifest = _load_manifest(manifest_path)
    assets = _load_assets(data_dir, manifest)
    strategy = MeanReversionStrategy(window=WINDOW, threshold=THRESHOLD)
    mr_targets = {
        symbol: _target_path([c.close for c in assets[symbol]], strategy)
        for symbol in SYMBOLS
    }

    trend_targets: dict[str, list[float]] = {}
    for symbol in SYMBOLS:
        prices = [c.close for c in assets[symbol]]
        state = 0.0
        targets = [0.0] * len(prices)
        for i in range(len(prices)):
            if i + 1 >= 200:
                fast = sum(prices[i - 49 : i + 1]) / 50.0
                slow = sum(prices[i - 199 : i + 1]) / 200.0
                state = 1.0 if fast > slow else 0.0
            targets[i] = state
        trend_targets[symbol] = targets

    scenarios: dict[str, dict] = {}
    for name, multiplier in (("base", 1.0), ("realistic_stress", STRESS_MULTIPLIER)):
        mr = _portfolio_returns(assets, mr_targets, BASE_COST * multiplier)
        trend = _portfolio_returns(assets, trend_targets, BASE_COST * multiplier)
        scenarios[name] = {
            "mean_reversion": _metrics(mr, RESEARCH_COUNT),
            "sma_50_200_reference": _metrics(trend, RESEARCH_COUNT),
            "blend_50_50": _metrics(
                [(a + b) / 2.0 for a, b in zip(mr, trend)],
                RESEARCH_COUNT,
            ),
        }

    report = {
        "schema_version": 1,
        "trial_id": "T-2026-09-24-015",
        "diagnostic_type": "trial_015_mean_reversion_global_etf",
        "status": "COMPLETED",
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "preregistration": {
            "document": "docs/trial_015_mean_reversion_global_etf_preregistration_2026_09_24.md",
            "selection_after_results": False,
            "parameter_optimization": False,
            "holdout_selection": False,
        },
        "source": {
            "universe": UNIVERSE,
            "symbols": list(SYMBOLS),
            "target_candles": TARGET_COUNT,
            "common_returns": TARGET_COUNT - 2,
            "research_count": RESEARCH_COUNT,
            "holdout_count": HOLDOUT_COUNT,
            "fully_symbol_disjoint_from_master_universes": True,
            "historical_prior_closed_pr79_symbols_excluded": True,
            "manifest_fingerprint": manifest["manifest_fingerprint"],
        },
        "methodology": {
            "mean_reversion_window": WINDOW,
            "mean_reversion_threshold": THRESHOLD,
            "mean_reversion_long_only": True,
            "trend_reference": "SMA 50/200 Long/Flat",
            "blend_weight_mean_reversion": 0.50,
            "blend_weight_trend": 0.50,
            "execution_model": "close(t) decision -> open(t+1) -> open(t+2)",
            "base_cost_rate": BASE_COST,
            "stress_multiplier": STRESS_MULTIPLIER,
            "optimization_used": False,
            "rolling_research_windows_cover_full_research_span": True,
        },
        "scenarios": scenarios,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    report["report_fingerprint"] = _fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
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
    print("TRIAL_015_STATUS:", report["status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
