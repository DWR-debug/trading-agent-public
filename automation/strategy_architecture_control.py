"""Controlled strategy-architecture ablation on immutable research data.

Diagnostic only:
- compares the current combined signal architecture against each component alone
- keeps strategy parameter space, selection rule, costs, stop model and risk
  handling otherwise unchanged
- fixes risk_per_trade and leverage to isolate signal architecture
- evaluates rolling OOS windows and a blind final holdout
- includes a small exposure control for the baseline-sanctioned 1% risk level

No gate, selection rule, production strategy or live execution is changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from statistics import median

from backtesting.engine import BacktestEngine
from config.parameter_space import ParameterCandidate, ParameterSpace
from config.parameters import (
    MeanReversionParameters,
    MomentumParameters,
    StrategyParameters,
)
from data.csv_loader import load_candles
from optimization.optimizer import Optimizer
from research.protocol import dataset_fingerprint
from strategies.mean_reversion import MeanReversionStrategy
from strategies.momentum import MomentumStrategy
from strategies.strategy_engine import StrategyEngine


ASSETS = ("SPY", "QQQ", "IWM")
INTERVAL = "1d"
TARGET_COUNT = 5000
RESEARCH_COUNT = 4500
HOLDOUT_COUNT = 500
ROLLING_TRAIN = 2250
ROLLING_TEST = 450
ROLLING_STEP = 450

FIXED_RISK_PER_TRADE = 0.0025
FIXED_LEVERAGE = 1.0

MODES = ("combined", "momentum_only", "mean_reversion_only")
EXPOSURE_LEVELS = (0.01, 0.005, 0.0025)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


def _candidate_payload(candidate: ParameterCandidate) -> dict:
    return {
        "risk_per_trade": candidate.risk_per_trade,
        "leverage": candidate.leverage,
        "strategy": asdict(candidate.strategy),
    }


def _build_mode_signals(
    candles,
    symbol: str,
    candidate: ParameterCandidate,
    mode: str,
):
    strategy_engine = StrategyEngine(parameters=candidate.strategy)
    momentum = MomentumStrategy(
        lookback=candidate.strategy.momentum.lookback
    )
    mean_reversion = MeanReversionStrategy(
        window=candidate.strategy.mean_reversion.window,
        threshold=candidate.strategy.mean_reversion.threshold,
    )

    prices: list[float] = []
    signals = []

    for candle in candles:
        prices.append(candle.close)

        try:
            if mode == "combined":
                signal = strategy_engine.generate_signal_validated(
                    symbol,
                    prices,
                )
            elif mode == "momentum_only":
                signal = momentum.generate_signal_validated(
                    symbol,
                    prices,
                )
            elif mode == "mean_reversion_only":
                signal = mean_reversion.generate_signal_validated(
                    symbol,
                    prices,
                )
            else:
                raise ValueError(f"Unbekannter Strategie-Modus: {mode}")
        except ValueError:
            signal = None

        signals.append(signal)

    return tuple(signals)


def _run_candidate(
    candles,
    symbol: str,
    candidate: ParameterCandidate,
    mode: str,
):
    signals = _build_mode_signals(candles, symbol, candidate, mode)
    engine = BacktestEngine(
        initial_capital=500.0,
        risk_per_trade=candidate.risk_per_trade,
        leverage=candidate.leverage,
        parameters=candidate.strategy,
        fee_rate=0.001,
        slippage_rate=0.0005,
    )
    return engine.run(
        symbol=symbol,
        candles=candles,
        signals=signals,
    )


def _candidate_pool() -> tuple[ParameterCandidate, ...]:
    space = ParameterSpace(
        risk_per_trade_values=[FIXED_RISK_PER_TRADE],
        leverage_values=[FIXED_LEVERAGE],
    )
    return tuple(space.candidates())


def _score(metrics: dict) -> float:
    return Optimizer.calculate_score(metrics)


def _select_on_train(
    candles,
    symbol: str,
    candidates: tuple[ParameterCandidate, ...],
    mode: str,
):
    scored = []

    for candidate in candidates:
        result = _run_candidate(candles, symbol, candidate, mode)
        metrics = result.metrics
        scored.append(
            (
                _score(metrics),
                _candidate_payload(candidate),
                candidate,
            )
        )

    scored.sort(key=lambda item: (item[0], _canonical_json(item[1])), reverse=True)
    best = scored[0]
    return best[2], best[0]


def _metrics(result) -> dict:
    data = dict(result.metrics)
    profit_factor = data["profit_factor"]
    if profit_factor == float("inf"):
        data["profit_factor"] = "inf"
    return data


def _rolling_control(candles, symbol: str, mode: str):
    candidates = _candidate_pool()
    windows = []

    for index, start in enumerate(
        range(
            0,
            len(candles) - ROLLING_TRAIN - ROLLING_TEST + 1,
            ROLLING_STEP,
        ),
        start=1,
    ):
        train = candles[start : start + ROLLING_TRAIN]
        test = candles[
            start + ROLLING_TRAIN :
            start + ROLLING_TRAIN + ROLLING_TEST
        ]

        candidate, selection_score = _select_on_train(
            train,
            symbol,
            candidates,
            mode,
        )
        test_result = _run_candidate(test, symbol, candidate, mode)
        metrics = _metrics(test_result)

        windows.append(
            {
                "window_index": index,
                "selected_candidate": _candidate_payload(candidate),
                "selection_score": selection_score,
                "test": metrics,
            }
        )

    total_profit = sum(
        item["test"]["net_profit_eur"]
        for item in windows
    )
    total_trades = sum(
        item["test"]["trade_count"]
        for item in windows
    )
    profitable_windows = sum(
        item["test"]["net_profit_eur"] > 0
        for item in windows
    )
    gross_profit = sum(
        max(item["test"]["net_profit_eur"], 0.0)
        for item in windows
    )
    gross_loss = sum(
        -min(item["test"]["net_profit_eur"], 0.0)
        for item in windows
    )
    overall_pf = (
        gross_profit / gross_loss
        if gross_loss > 0
        else ("inf" if gross_profit > 0 else 0.0)
    )

    return {
        "mode": mode,
        "window_count": len(windows),
        "total_test_candles": len(windows) * ROLLING_TEST,
        "total_net_profit_eur": total_profit,
        "total_trade_count": total_trades,
        "profitable_windows": profitable_windows,
        "profitable_window_ratio": (
            profitable_windows / len(windows)
            if windows
            else 0.0
        ),
        "overall_profit_factor": overall_pf,
        "median_window_profit_factor": median(
            [
                item["test"]["profit_factor"]
                for item in windows
                if item["test"]["profit_factor"] != "inf"
            ]
        ) if any(
            item["test"]["profit_factor"] != "inf"
            for item in windows
        ) else "inf",
        "average_drawdown_percent": (
            sum(
                item["test"]["max_drawdown_percent"]
                for item in windows
            ) / len(windows)
            if windows
            else 0.0
        ),
        "windows": windows,
    }


def _holdout_control(candles, symbol: str, mode: str):
    candidates = _candidate_pool()
    research = candles[:RESEARCH_COUNT]
    holdout = candles[RESEARCH_COUNT:]
    candidate, score = _select_on_train(
        research,
        symbol,
        candidates,
        mode,
    )
    result = _run_candidate(holdout, symbol, candidate, mode)
    return {
        "mode": mode,
        "selected_candidate": _candidate_payload(candidate),
        "selection_score": score,
        "holdout": _metrics(result),
    }


def _baseline_exposure_control(candles, symbol: str):
    strategy = StrategyParameters()
    results = []

    for risk in EXPOSURE_LEVELS:
        candidate = ParameterCandidate(
            strategy=strategy,
            risk_per_trade=risk,
            leverage=1.0,
        )
        result = _run_candidate(
            candles[:RESEARCH_COUNT],
            symbol,
            candidate,
            "combined",
        )
        metrics = _metrics(result)
        results.append(
            {
                "risk_per_trade": risk,
                "leverage": 1.0,
                "net_profit_eur": metrics["net_profit_eur"],
                "max_drawdown_percent": metrics["max_drawdown_percent"],
                "trade_count": metrics["trade_count"],
                "profit_factor": metrics["profit_factor"],
                "passes_10pct_drawdown": (
                    metrics["max_drawdown_percent"] <= 10.0
                ),
            }
        )

    return {
        "symbol": symbol,
        "strategy": asdict(strategy),
        "results": results,
        "interpretation": (
            "Kontrolle der Baseline-Exposure: gleicher aktueller Combiner "
            "und gleiche Strategieparameter, nur risk_per_trade variiert. "
            "Dies ist diagnostisch und ändert das Backtest-Gate nicht."
        ),
    }


def _load_manifest(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest muss ein JSON-Objekt sein.")
    return payload


def _verify_source(
    data_dir: Path,
    manifest: dict,
):
    by_symbol = {
        item["symbol"]: item
        for item in manifest.get("datasets", [])
        if isinstance(item, dict) and "symbol" in item
    }

    verified = []

    for symbol in ASSETS:
        if symbol not in by_symbol:
            raise ValueError(f"Manifest enthält {symbol} nicht.")

        candles = tuple(
            load_candles(
                data_dir / symbol / f"{INTERVAL}.csv"
            )
        )
        item = by_symbol[symbol]

        if len(candles) != TARGET_COUNT:
            raise ValueError(
                f"{symbol}: {len(candles)} Candles statt {TARGET_COUNT}."
            )

        actual = dataset_fingerprint(candles)
        if actual != item.get("fingerprint"):
            raise ValueError(
                f"{symbol}: Dataset-Fingerprint stimmt nicht mit dem "
                "archivierten Manifest überein."
            )

        verified.append((symbol, candles))

    return verified


def run_control(data_dir: Path, manifest_path: Path, output_path: Path):
    manifest = _load_manifest(manifest_path)
    datasets = _verify_source(data_dir, manifest)

    by_asset = {}
    for symbol, candles in datasets:
        by_asset[symbol] = {
            "candle_count": len(candles),
            "data_start": candles[0].timestamp.isoformat(),
            "data_end": candles[-1].timestamp.isoformat(),
            "dataset_fingerprint": dataset_fingerprint(candles),
            "rolling": {
                mode: _rolling_control(
                    candles[:RESEARCH_COUNT],
                    symbol,
                    mode,
                )
                for mode in MODES
            },
            "holdout": {
                mode: _holdout_control(
                    candles,
                    symbol,
                    mode,
                )
                for mode in MODES
            },
            "baseline_exposure_control": _baseline_exposure_control(
                candles,
                symbol,
            ),
        }

    aggregate = {}
    for mode in MODES:
        rows = [
            by_asset[symbol]["rolling"][mode]
            for symbol in ASSETS
        ]
        holdouts = [
            by_asset[symbol]["holdout"][mode]["holdout"]
            for symbol in ASSETS
        ]
        aggregate[mode] = {
            "asset_count": len(rows),
            "total_oos_profit_eur": sum(
                row["total_net_profit_eur"] for row in rows
            ),
            "profitable_window_ratio_mean": (
                sum(row["profitable_window_ratio"] for row in rows)
                / len(rows)
            ),
            "overall_profit_factor_from_window_pnl": _aggregate_pf(rows),
            "holdout_total_profit_eur": sum(
                row["net_profit_eur"] for row in holdouts
            ),
            "holdout_positive_asset_count": sum(
                row["net_profit_eur"] > 0
                for row in holdouts
            ),
        }

    report = {
        "diagnostic_type": "strategy_architecture_ablation",
        "status": "COMPLETED",
        "source": {
            "target_count": TARGET_COUNT,
            "research_count": RESEARCH_COUNT,
            "holdout_count": HOLDOUT_COUNT,
            "manifest_fingerprint": manifest.get(
                "manifest_fingerprint"
            ),
            "manifest_provenance": manifest.get("provenance"),
        },
        "methodology": {
            "modes": MODES,
            "parameter_candidate_count": len(_candidate_pool()),
            "fixed_risk_per_trade": FIXED_RISK_PER_TRADE,
            "fixed_leverage": FIXED_LEVERAGE,
            "selection": "score_max_equivalent",
            "rolling_geometry": {
                "train_candles": ROLLING_TRAIN,
                "test_candles": ROLLING_TEST,
                "step_candles": ROLLING_STEP,
                "window_count_per_asset": 5,
            },
            "costs": {
                "fee_rate": 0.001,
                "slippage_rate": 0.0005,
            },
            "execution_model": (
                "existing_backtest_engine: signal uses current close and "
                "entry/exit are simulated at that close; gap-aware stop "
                "execution is not implemented"
            ),
        },
        "assets": by_asset,
        "aggregate": aggregate,
        "baseline_exposure_summary": [
            by_asset[symbol]["baseline_exposure_control"]
            for symbol in ASSETS
        ],
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    report["report_fingerprint"] = _fingerprint(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    return report


def _aggregate_pf(rows):
    gross_profit = sum(
        max(row["total_net_profit_eur"], 0.0)
        for row in rows
    )
    gross_loss = sum(
        -min(row["total_net_profit_eur"], 0.0)
        for row in rows
    )
    if gross_loss > 0:
        return gross_profit / gross_loss
    if gross_profit > 0:
        return "inf"
    return 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_control(
        Path(args.data_dir),
        Path(args.manifest),
        Path(args.output),
    )

    print("STRATEGY_ARCHITECTURE_STATUS:", report["status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    for mode, item in report["aggregate"].items():
        print(
            mode,
            "TOTAL_OOS_PROFIT_EUR=",
            item["total_oos_profit_eur"],
            "PROFITABLE_WINDOW_RATIO_MEAN=",
            item["profitable_window_ratio_mean"],
            "HOLDOUT_TOTAL_PROFIT_EUR=",
            item["holdout_total_profit_eur"],
        )


if __name__ == "__main__":
    main()
