"""Harte Research-Gates für kontrollierte Offline-Strategieforschung.

Ein Kandidat kann nur PASSED erhalten, wenn alle Gates bestanden sind.

Keine Orderausführung.
Kein Echtgeldhandel.
"""

import math

from dataclasses import dataclass
from typing import Any

from backtesting.engine import BacktestEngine
from config import settings
from config.parameter_space import ParameterCandidate
from config.parameters import (
    MeanReversionParameters,
    MomentumParameters,
    StrategyParameters,
)
from data.quality import validate_candles
from research.protocol import ResearchProtocol, split_holdout


@dataclass(frozen=True)
class ResearchGateConfig:
    minimum_candles: int = 500
    minimum_baseline_trades: int = 2
    minimum_wfo_trades: int = 10
    minimum_rolling_trades: int = 30
    minimum_holdout_trades: int = 10
    minimum_profit_factor: float = 1.10
    maximum_drawdown_percent: float = settings.MAX_DRAWDOWN_PERCENT
    minimum_profitable_window_ratio: float = 0.50
    maximum_zero_trade_window_ratio: float = 0.25
    minimum_robust_variants: int = 4
    minimum_robust_profitable_ratio: float = 0.50
    stress_cost_multiplier: float = 1.50
    minimum_oos_to_is_return_ratio: float = 0.25
    holdout_ratio: float = 0.10
    fee_rate: float = 0.001
    slippage_rate: float = 0.0005


def _finite_value(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _finite_metrics(metrics: dict[str, Any]) -> bool:
    numeric_keys = (
        "net_profit_eur",
        "return_percent",
        "win_rate_percent",
        "max_drawdown_percent",
        "sharpe_ratio",
        "average_trade_eur",
    )

    if any(
        not _finite_value(metrics.get(key))
        for key in numeric_keys
    ):
        return False

    trade_count = metrics.get("trade_count")
    if not isinstance(trade_count, int) or trade_count < 0:
        return False

    profit_factor = metrics.get("profit_factor")
    return (
        profit_factor == "inf"
        or (
            isinstance(profit_factor, (int, float))
            and not math.isnan(profit_factor)
        )
    )


def _finite_wfo_metrics(metrics: dict[str, Any]) -> bool:
    mapped = {
        "net_profit_eur": metrics.get("test_net_profit_eur"),
        "return_percent": metrics.get("test_return_percent"),
        "win_rate_percent": metrics.get("test_win_rate_percent"),
        "profit_factor": metrics.get("test_profit_factor"),
        "max_drawdown_percent": metrics.get(
            "test_max_drawdown_percent"
        ),
        "sharpe_ratio": metrics.get("test_sharpe_ratio"),
        "trade_count": metrics.get("test_trade_count"),
        "average_trade_eur": metrics.get(
            "test_average_trade_eur"
        ),
    }
    return _finite_metrics(
        {
            **mapped,
            "profit_factor": (
                0.0
                if mapped["profit_factor"] == "inf"
                else mapped["profit_factor"]
            ),
        }
    )


def _gate(
    name: str,
    passed: bool,
    details: dict[str, Any],
    *,
    scope: str,
):
    return {
        "name": name,
        "scope": scope,
        "passed": bool(passed),
        "details": details,
    }


def check_data_quality(candles, config):
    try:
        validate_candles(candles)
    except (TypeError, ValueError) as exc:
        return _gate(
            "data_quality",
            False,
            {"error": f"{type(exc).__name__}: {exc}"},
            scope="dataset_input",
        )

    return _gate(
        "data_quality",
        len(candles) >= config.minimum_candles,
        {
            "candle_count": len(candles),
            "minimum_candles": config.minimum_candles,
        },
        scope="dataset_input",
    )


def check_backtest(metrics, config, initial_capital=settings.INITIAL_CAPITAL_EUR):
    metrics_valid = _finite_metrics(metrics)
    final_capital = initial_capital + metrics.get(
        "net_profit_eur",
        0.0,
    )

    passed = (
        metrics_valid
        and metrics["trade_count"] >= config.minimum_baseline_trades
        and final_capital > 0.0
        and metrics["max_drawdown_percent"]
        <= config.maximum_drawdown_percent
    )

    return _gate(
        "backtest",
        passed,
        {
            "metrics_valid": metrics_valid,
            "trade_count": metrics.get("trade_count"),
            "minimum_trades": config.minimum_baseline_trades,
            "final_capital_eur": final_capital,
            "max_drawdown_percent": metrics.get("max_drawdown_percent"),
            "maximum_drawdown_percent": config.maximum_drawdown_percent,
        },
        scope="baseline_sanity",
    )


def check_walk_forward(metrics, config):
    profit_factor = metrics.get("test_profit_factor", 0.0)
    numeric_profit_factor = (
        float("inf")
        if profit_factor == "inf"
        else profit_factor
    )
    metrics_valid = _finite_wfo_metrics(metrics)

    passed = (
        metrics_valid
        and metrics["test_trade_count"] >= config.minimum_wfo_trades
        and metrics["test_net_profit_eur"] > 0.0
        and numeric_profit_factor >= config.minimum_profit_factor
        and metrics["test_max_drawdown_percent"]
        <= config.maximum_drawdown_percent
    )

    return _gate(
        "walk_forward",
        passed,
        {
            "metrics_valid": metrics_valid,
            "oos_trade_count": metrics.get("test_trade_count"),
            "minimum_oos_trades": config.minimum_wfo_trades,
            "oos_net_profit_eur": metrics.get("test_net_profit_eur"),
            "profit_factor": profit_factor,
            "minimum_profit_factor": config.minimum_profit_factor,
            "oos_max_drawdown_percent": metrics.get(
                "test_max_drawdown_percent"
            ),
            "maximum_drawdown_percent": config.maximum_drawdown_percent,
        },
        scope="selected_candidate_oos",
    )


def check_rolling_walk_forward(summary, config):
    window_count = summary.get("window_count", 0)
    profitable_windows = summary.get("profitable_windows", 0)
    zero_trade_windows = summary.get("zero_trade_windows", 0)

    profitable_ratio = (
        profitable_windows / window_count
        if window_count
        else 0.0
    )
    zero_trade_ratio = (
        zero_trade_windows / window_count
        if window_count
        else 1.0
    )

    profit_factor = summary.get("overall_profit_factor", 0.0)
    numeric_profit_factor = (
        float("inf")
        if profit_factor == "inf"
        else profit_factor
    )
    metrics_valid = (
        _finite_value(summary.get("total_net_profit_eur"))
        and _finite_value(summary.get("overall_win_rate_percent"))
        and _finite_value(summary.get("average_trade_eur"))
        and _finite_value(summary.get("average_drawdown_percent"))
        and _finite_value(summary.get("average_sharpe_ratio"))
        and isinstance(profit_factor, (int, float))
        and not math.isnan(profit_factor)
    )

    passed = (
        window_count > 0
        and metrics_valid
        and summary.get("total_trade_count", 0)
        >= config.minimum_rolling_trades
        and summary.get("total_net_profit_eur", 0.0) > 0.0
        and numeric_profit_factor >= config.minimum_profit_factor
        and profitable_ratio >= config.minimum_profitable_window_ratio
        and zero_trade_ratio <= config.maximum_zero_trade_window_ratio
        and summary.get("average_drawdown_percent", 0.0)
        <= config.maximum_drawdown_percent
    )

    return _gate(
        "rolling_walk_forward",
        passed,
        {
            "window_count": window_count,
            "total_trade_count": summary.get("total_trade_count"),
            "minimum_total_trades": config.minimum_rolling_trades,
            "total_net_profit_eur": summary.get("total_net_profit_eur"),
            "overall_profit_factor": profit_factor,
            "minimum_profit_factor": config.minimum_profit_factor,
            "profitable_window_ratio": profitable_ratio,
            "minimum_profitable_window_ratio": config.minimum_profitable_window_ratio,
            "zero_trade_window_ratio": zero_trade_ratio,
            "maximum_zero_trade_window_ratio": config.maximum_zero_trade_window_ratio,
            "average_drawdown_percent": summary.get(
                "average_drawdown_percent"
            ),
            "maximum_drawdown_percent": config.maximum_drawdown_percent,
        },
        scope="rolling_selected_candidate_oos",
    )


def _candidate_from_dict(data):
    strategy = data["strategy"]
    return ParameterCandidate(
        strategy=StrategyParameters(
            momentum=MomentumParameters(
                lookback=int(strategy["momentum"]["lookback"])
            ),
            mean_reversion=MeanReversionParameters(
                window=int(strategy["mean_reversion"]["window"]),
                threshold=float(
                    strategy["mean_reversion"]["threshold"]
                ),
            ),
        ),
        risk_per_trade=float(data["risk_per_trade"]),
        leverage=float(data["leverage"]),
    )


def _run_candidate(
    candidate,
    candles,
    symbol,
    *,
    fee_rate,
    slippage_rate,
):
    engine = BacktestEngine(
        initial_capital=settings.INITIAL_CAPITAL_EUR,
        risk_per_trade=candidate.risk_per_trade,
        leverage=candidate.leverage,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        parameters=candidate.strategy,
    )
    return engine.run(
        symbol=symbol,
        candles=candles,
    )


def _variant_candidates(candidate):
    momentum = candidate.strategy.momentum.lookback
    window = candidate.strategy.mean_reversion.window
    threshold = candidate.strategy.mean_reversion.threshold

    specs = (
        ("momentum", max(1, math.floor(momentum * 0.8))),
        ("momentum", max(1, math.ceil(momentum * 1.2))),
        ("window", max(2, math.floor(window * 0.8))),
        ("window", max(2, math.ceil(window * 1.2))),
        ("threshold", threshold * 0.8),
        ("threshold", threshold * 1.2),
    )

    variants = []

    for parameter, value in specs:
        if parameter == "momentum" and value != momentum:
            strategy = StrategyParameters(
                momentum=MomentumParameters(lookback=value),
                mean_reversion=candidate.strategy.mean_reversion,
            )
        elif parameter == "window" and value != window:
            strategy = StrategyParameters(
                momentum=candidate.strategy.momentum,
                mean_reversion=MeanReversionParameters(
                    window=value,
                    threshold=threshold,
                ),
            )
        elif parameter == "threshold":
            strategy = StrategyParameters(
                momentum=candidate.strategy.momentum,
                mean_reversion=MeanReversionParameters(
                    window=window,
                    threshold=value,
                ),
            )
        else:
            continue

        variants.append(
            ParameterCandidate(
                strategy=strategy,
                risk_per_trade=candidate.risk_per_trade,
                leverage=candidate.leverage,
            )
        )

    unique = []
    seen = set()

    for variant in variants:
        key = (
            variant.strategy.momentum.lookback,
            variant.strategy.mean_reversion.window,
            variant.strategy.mean_reversion.threshold,
        )
        if key not in seen:
            seen.add(key)
            unique.append(variant)

    return tuple(unique)


def check_robustness(
    candidate,
    test_candles,
    symbol,
    config,
    *,
    fee_rate,
    slippage_rate,
):
    variants = _variant_candidates(candidate)

    if len(variants) < config.minimum_robust_variants:
        return _gate(
            "robustness",
            False,
            {
                "variant_count": len(variants),
                "minimum_variants": config.minimum_robust_variants,
                "profitable_variant_ratio": 0.0,
                "minimum_profitable_variant_ratio": (
                    config.minimum_robust_profitable_ratio
                ),
            },
            scope="selected_candidate_robustness",
        )

    variant_results = [
        _run_candidate(
            variant,
            test_candles,
            symbol,
            fee_rate=fee_rate,
            slippage_rate=slippage_rate,
        )
        for variant in variants
    ]

    profitable = sum(
        1
        for result in variant_results
        if result.metrics["net_profit_eur"] > 0.0
    )
    profitable_ratio = profitable / len(variant_results)

    stress_factor = config.stress_cost_multiplier
    stressed = _run_candidate(
        candidate,
        test_candles,
        symbol,
        fee_rate=fee_rate * stress_factor,
        slippage_rate=slippage_rate * stress_factor,
    )

    passed = (
        profitable_ratio >= config.minimum_robust_profitable_ratio
        and stressed.metrics["net_profit_eur"] >= 0.0
    )

    return _gate(
        "robustness",
        passed,
        {
            "variant_count": len(variants),
            "profitable_variant_count": profitable,
            "profitable_variant_ratio": profitable_ratio,
            "minimum_profitable_variant_ratio": (
                config.minimum_robust_profitable_ratio
            ),
            "stress_cost_multiplier": stress_factor,
            "stressed_net_profit_eur": stressed.metrics[
                "net_profit_eur"
            ],
        },
        scope="selected_candidate_robustness",
    )


def check_overfit(train_metrics, test_metrics, config):
    train_return = train_metrics.get("return_percent", 0.0)
    test_return = test_metrics.get("test_return_percent", 0.0)

    valid = (
        _finite_metrics(train_metrics)
        and _finite_value(test_return)
        and train_return > 0.0
    )
    ratio = test_return / train_return if valid else 0.0

    return _gate(
        "overfit",
        valid and ratio >= config.minimum_oos_to_is_return_ratio,
        {
            "train_return_percent": train_return,
            "oos_return_percent": test_return,
            "oos_to_is_return_ratio": ratio,
            "minimum_oos_to_is_return_ratio": (
                config.minimum_oos_to_is_return_ratio
            ),
        },
        scope="selected_candidate_train_vs_oos",
    )


def check_holdout(metrics, config):
    metrics_valid = _finite_metrics(metrics)
    profit_factor = metrics.get("profit_factor", 0.0)
    numeric_profit_factor = (
        float("inf")
        if profit_factor == "inf"
        else profit_factor
    )

    passed = (
        metrics_valid
        and metrics["trade_count"] >= config.minimum_holdout_trades
        and metrics["net_profit_eur"] > 0.0
        and numeric_profit_factor >= config.minimum_profit_factor
        and metrics["max_drawdown_percent"]
        <= config.maximum_drawdown_percent
    )

    return _gate(
        "holdout",
        passed,
        {
            "trade_count": metrics.get("trade_count"),
            "minimum_holdout_trades": config.minimum_holdout_trades,
            "net_profit_eur": metrics.get("net_profit_eur"),
            "profit_factor": profit_factor,
            "minimum_profit_factor": config.minimum_profit_factor,
            "max_drawdown_percent": metrics.get(
                "max_drawdown_percent"
            ),
            "maximum_drawdown_percent": config.maximum_drawdown_percent,
        },
        scope="selected_candidate_holdout",
    )


def evaluate_research_gates(
    result,
    candles,
    *,
    train_ratio=0.7,
    config=None,
):
    config = config or ResearchGateConfig()

    protocol = ResearchProtocol(
        holdout_ratio=config.holdout_ratio,
        fee_rate=config.fee_rate,
        slippage_rate=config.slippage_rate,
    )
    research_candles, holdout_candles = split_holdout(
        tuple(candles),
        protocol,
    )

    gates = [
        check_data_quality(candles, config),
        check_backtest(result["baseline"], config),
        check_walk_forward(result["walk_forward"], config),
        check_rolling_walk_forward(
            result["rolling_walk_forward"]["summary"],
            config,
        ),
    ]

    candidate = _candidate_from_dict(
        result["walk_forward"]["selected_candidate"]
    )
    symbol = result.get("symbol", "RESEARCH")

    train_size = result["walk_forward"]["train_candles"]
    test_size = result["walk_forward"]["test_candles"]

    wfo_test_candles = research_candles[
        train_size:train_size + test_size
    ]

    gates.append(
        check_robustness(
            candidate,
            wfo_test_candles,
            symbol,
            config,
            fee_rate=protocol.fee_rate,
            slippage_rate=protocol.slippage_rate,
        )
    )

    train_candles = research_candles[:train_size]
    train_result = _run_candidate(
        candidate,
        train_candles,
        symbol,
        fee_rate=protocol.fee_rate,
        slippage_rate=protocol.slippage_rate,
    )

    gates.append(
        check_overfit(
            train_result.metrics,
            result["walk_forward"],
            config,
        )
    )

    gates.append(
        check_holdout(
            result["holdout"],
            config,
        )
    )

    failed = [
        gate["name"]
        for gate in gates
        if not gate["passed"]
    ]

    return {
        "passed": not failed,
        "status": "PASSED" if not failed else "BLOCKED",
        "gate_count": len(gates),
        "passed_count": sum(
            1
            for gate in gates
            if gate["passed"]
        ),
        "failed_gates": failed,
        "gates": gates,
    }
