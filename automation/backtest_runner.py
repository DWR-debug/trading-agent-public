"""
Automatisierter Offline-Analyse-Runner mit Checkpoint/Resume.

Keine Orderausführung.
Kein Echtgeldhandel.
Keine API-Schlüssel.
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from automation.checkpoint import (
    ResearchCheckpointStore,
    checkpoint_key,
)
from backtesting.engine import BacktestEngine
from config import settings
from data.market_store import MarketDataStore
from optimization.optimizer import Optimizer
from research.protocol import (
    ResearchProtocol,
    dataset_fingerprint,
    permutation_positive_tail_probability,
    split_holdout,
)
from validation.rolling_walk_forward import RollingWalkForwardValidator
from validation.walk_forward import WalkForwardValidator


def _candidate_dict(candidate):
    return {
        "risk_per_trade": candidate.risk_per_trade,
        "leverage": candidate.leverage,
        "strategy": asdict(candidate.strategy),
    }


def _json_safe(value):
    if isinstance(value, float) and value == float("inf"):
        return "inf"
    return value


def _optimization_result_dict(result):
    data = asdict(result)
    data["candidate"] = _candidate_dict(result.candidate)
    return {
        key: _json_safe(value)
        for key, value in data.items()
    }


def _metrics_dict(metrics):
    return {
        key: _json_safe(value)
        for key, value in metrics.items()
    }


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
    return engine.run(symbol=symbol, candles=candles)


def _rolling_window_sizes(
    candle_count,
    *,
    train_ratio=0.5,
    test_ratio=0.1,
    step_ratio=0.1,
):
    if candle_count < 4:
        raise ValueError("Zu wenige Research-Candles für Rolling Walk-Forward.")

    for name, ratio in (
        ("train_ratio", train_ratio),
        ("test_ratio", test_ratio),
        ("step_ratio", step_ratio),
    ):
        if not 0.0 < ratio <= 1.0:
            raise ValueError(f"{name} muss zwischen 0 und 1 liegen.")

    train_size = max(2, int(candle_count * train_ratio))
    test_size = max(2, int(candle_count * test_ratio))
    step_size = max(1, int(candle_count * step_ratio))

    if train_size + test_size > candle_count:
        raise ValueError(
            "Rolling-Walk-Forward-Konfiguration passt nicht zur "
            "Research-Historie."
        )

    return train_size, test_size, step_size


def run_dataset(
    symbol,
    interval,
    *,
    store=None,
    parameter_space=None,
    optimizer_top_n=5,
    train_ratio=0.7,
    selection_profile="score_max",
    rolling_train_ratio=0.5,
    rolling_test_ratio=0.1,
    rolling_step_ratio=0.1,
    minimum_trades_required=30,
    protocol=None,
    rolling_train_size=None,
    rolling_test_size=None,
    rolling_step_size=None,
):
    if not symbol or not symbol.strip():
        raise ValueError("Symbol darf nicht leer sein.")
    if not interval or not interval.strip():
        raise ValueError("Intervall darf nicht leer sein.")
    if optimizer_top_n < 1:
        raise ValueError("optimizer_top_n muss mindestens 1 sein.")

    store = store or MarketDataStore()
    candles = tuple(store.load(symbol, interval))
    if not candles:
        raise ValueError(
            f"Keine Marktdaten vorhanden: {symbol} {interval}"
        )

    protocol = protocol or ResearchProtocol()
    research_candles, holdout_candles = split_holdout(
        candles,
        protocol,
    )

    fixed_window_sizes = (
        rolling_train_size is not None
        or rolling_test_size is not None
        or rolling_step_size is not None
    )
    if fixed_window_sizes:
        if not all(
            value is not None
            for value in (
                rolling_train_size,
                rolling_test_size,
                rolling_step_size,
            )
        ):
            raise ValueError(
                "Rolling-WF-Fenstergrößen müssen gemeinsam gesetzt werden."
            )
        if (
            rolling_train_size < 2
            or rolling_test_size < 2
            or rolling_step_size < 1
        ):
            raise ValueError("Ungültige Rolling-WF-Fenstergrößen.")
    else:
        rolling_train_size, rolling_test_size, rolling_step_size = (
            _rolling_window_sizes(
                len(research_candles),
                train_ratio=rolling_train_ratio,
                test_ratio=rolling_test_ratio,
                step_ratio=rolling_step_ratio,
            )
        )

    baseline = BacktestEngine(
        fee_rate=protocol.fee_rate,
        slippage_rate=protocol.slippage_rate,
    ).run(
        symbol=symbol,
        candles=research_candles,
    )

    optimizer = Optimizer(
        candles=research_candles,
        symbol=symbol,
        parameter_space=parameter_space,
    )
    optimization_results = optimizer.optimize(
        top_n=optimizer_top_n,
        selection_profile=selection_profile,
    )

    walk_forward = WalkForwardValidator(
        candles=research_candles,
        symbol=symbol,
        parameter_space=parameter_space,
        train_ratio=train_ratio,
        selection_profile=selection_profile,
    ).validate()

    rolling_validator = RollingWalkForwardValidator(
        candles=research_candles,
        symbol=symbol,
        parameter_space=parameter_space,
        train_size=rolling_train_size,
        test_size=rolling_test_size,
        step_size=rolling_step_size,
        minimum_trades_required=minimum_trades_required,
        selection_profile=selection_profile,
    )
    rolling_results = rolling_validator.validate()
    rolling_summary = rolling_validator.summarize(rolling_results)

    holdout_candidate = walk_forward.selected_candidate
    holdout_result = _run_candidate(
        holdout_candidate,
        holdout_candles,
        symbol,
        fee_rate=protocol.fee_rate,
        slippage_rate=protocol.slippage_rate,
    )

    holdout_pnls = tuple(
        trade.pnl_eur
        for trade in holdout_result.trades
    )

    return {
        "symbol": symbol,
        "interval": interval,
        "candle_count": len(candles),
        "research_candle_count": len(research_candles),
        "holdout_candle_count": len(holdout_candles),
        "data_start": candles[0].timestamp.isoformat(),
        "data_end": candles[-1].timestamp.isoformat(),
        "research_end": research_candles[-1].timestamp.isoformat(),
        "holdout_start": holdout_candles[0].timestamp.isoformat(),
        "dataset_fingerprint": dataset_fingerprint(candles),
        "research_dataset_fingerprint": dataset_fingerprint(
            research_candles
        ),
        "holdout_dataset_fingerprint": dataset_fingerprint(
            holdout_candles
        ),
        "protocol": {
            "holdout_ratio": protocol.holdout_ratio,
            "fee_rate": protocol.fee_rate,
            "slippage_rate": protocol.slippage_rate,
            "permutation_trials": protocol.permutation_trials,
            "permutation_seed": protocol.permutation_seed,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
        },
        "baseline": _metrics_dict(baseline.metrics),
        "optimization_candidate_count": parameter_space.size(),
        "optimization_reported_top_n": len(optimization_results),
        "optimization": [
            _optimization_result_dict(result)
            for result in optimization_results
        ],
        "walk_forward": {
            "selection_profile": selection_profile,
            "train_candles": walk_forward.train_candles,
            "test_candles": walk_forward.test_candles,
            "selected_candidate": _candidate_dict(
                walk_forward.selected_candidate
            ),
            "test_net_profit_eur": walk_forward.test_net_profit_eur,
            "test_return_percent": walk_forward.test_return_percent,
            "test_win_rate_percent": walk_forward.test_win_rate_percent,
            "test_profit_factor": _json_safe(
                walk_forward.test_profit_factor
            ),
            "test_max_drawdown_percent": walk_forward.test_max_drawdown_percent,
            "test_sharpe_ratio": walk_forward.test_sharpe_ratio,
            "test_trade_count": walk_forward.test_trade_count,
            "test_average_trade_eur": walk_forward.test_average_trade_eur,
        },
        "rolling_walk_forward": {
            "configuration": {
                "selection_profile": selection_profile,
                "train_ratio": rolling_train_ratio,
                "test_ratio": rolling_test_ratio,
                "step_ratio": rolling_step_ratio,
                "train_candles": rolling_train_size,
                "test_candles": rolling_test_size,
                "step_candles": rolling_step_size,
                "mode": "fixed" if fixed_window_sizes else "ratio",
                "minimum_trades_required": minimum_trades_required,
            },
            "summary": {
                key: _json_safe(value)
                for key, value in asdict(rolling_summary).items()
            },
            "windows": [
                {
                    "window_index": result.window_index,
                    "train_candles": result.train_candles,
                    "test_candles": result.test_candles,
                    "selected_candidate": _candidate_dict(
                        result.selected_candidate
                    ),
                    "test_net_profit_eur": result.test_net_profit_eur,
                    "test_return_percent": result.test_return_percent,
                    "test_win_rate_percent": result.test_win_rate_percent,
                    "test_profit_factor": _json_safe(
                        result.test_profit_factor
                    ),
                    "test_max_drawdown_percent": result.test_max_drawdown_percent,
                    "test_sharpe_ratio": result.test_sharpe_ratio,
                    "test_trade_count": result.test_trade_count,
                    "test_average_trade_eur": result.test_average_trade_eur,
                }
                for result in rolling_results
            ],
        },
        "holdout": {
            "selected_candidate": _candidate_dict(holdout_candidate),
            **_metrics_dict(holdout_result.metrics),
            "permutation_positive_tail_probability": (
                permutation_positive_tail_probability(
                    holdout_pnls,
                    trials=protocol.permutation_trials,
                    seed=protocol.permutation_seed,
                )
            ),
        },
    }


def _write_report(path: Path, started_at: str, results: list[dict]) -> None:
    report = {
        "generated_at": started_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
        },
        "datasets": results,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(
            report,
            handle,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
    temp.replace(path)


def run_all(
    datasets,
    *,
    store=None,
    parameter_space=None,
    optimizer_top_n=5,
    train_ratio=0.7,
    selection_profile="score_max",
    rolling_train_ratio=0.5,
    rolling_test_ratio=0.1,
    rolling_step_ratio=0.1,
    minimum_trades_required=30,
    output_dir="reports",
    protocol=None,
    checkpoint_path="research/checkpoints/latest.json",
    resume=False,
    run_fingerprint=None,
    rolling_train_size=None,
    rolling_test_size=None,
    rolling_step_size=None,
):
    if not datasets:
        raise ValueError("datasets dürfen nicht leer sein.")

    store = store or MarketDataStore()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    checkpoint = ResearchCheckpointStore(checkpoint_path)
    state = checkpoint.load() if resume else None
    started_at = (
        state["started_at"]
        if state is not None
        else datetime.now(timezone.utc).isoformat()
    )
    report_path = (
        Path(state["report_path"])
        if state is not None
        else output_path / (
            "analysis_"
            + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            + ".json"
        )
    )

    results_by_key = {}

    if state is not None:
        if "checkpoint_fingerprint" not in state:
            raise RuntimeError(
                "Research-Checkpoint besitzt keine Integritätsprüfung für die Run-Identität. "
                "Resume wurde aus Sicherheitsgründen verweigert."
            )
        if run_fingerprint is None:
            raise RuntimeError(
                "Resume erfordert eine verifizierte Research-Run-Identität."
            )
        stored_run_fingerprint = state.get("run_fingerprint")
        if not isinstance(stored_run_fingerprint, str):
            raise RuntimeError(
                "Research-Checkpoint besitzt keine gültige Research-Run-Identität. "
                "Resume wurde aus Sicherheitsgründen verweigert."
            )
        if stored_run_fingerprint != run_fingerprint:
            raise RuntimeError(
                "Research-Checkpoint gehört zu einer anderen "
                "Run-Identität. Resume wurde aus Sicherheitsgründen "
                "verweigert."
            )

        results_by_key = {
            checkpoint_key(item["symbol"], item["interval"]): item
            for item in state.get("results", [])
        }
        if state.get("status") == "COMPLETED":
            return {
                "generated_at": started_at,
                "updated_at": state.get("updated_at"),
                "safety": {
                    "paper_only": True,
                    "live_trading_enabled": False,
                },
                "datasets": list(results_by_key.values()),
                "run_fingerprint": state.get("run_fingerprint"),
            }, report_path

    completed = set(results_by_key)

    for index, (symbol, interval) in enumerate(datasets):
        key = checkpoint_key(symbol, interval)
        if key in completed:
            continue

        checkpoint.save(
            {
                "run_type": "multi_dataset_research",
                "started_at": started_at,
                "status": "RUNNING",
                "current_index": index,
                "current_dataset": key,
                "completed": sorted(completed),
                "results": list(results_by_key.values()),
                "report_path": str(report_path),
                "run_fingerprint": run_fingerprint,
            }
        )

        try:
            result = run_dataset(
                symbol,
                interval,
                store=store,
                parameter_space=parameter_space,
                optimizer_top_n=optimizer_top_n,
                train_ratio=train_ratio,
                selection_profile=selection_profile,
                rolling_train_ratio=rolling_train_ratio,
                rolling_test_ratio=rolling_test_ratio,
                rolling_step_ratio=rolling_step_ratio,
                minimum_trades_required=minimum_trades_required,
                rolling_train_size=rolling_train_size,
                rolling_test_size=rolling_test_size,
                rolling_step_size=rolling_step_size,
                protocol=protocol,
            )
        except Exception as exc:
            checkpoint.save(
                {
                    "run_type": "multi_dataset_research",
                    "started_at": started_at,
                    "status": "FAILED",
                    "current_index": index,
                    "current_dataset": key,
                    "completed": sorted(completed),
                    "results": list(results_by_key.values()),
                    "report_path": str(report_path),
                    "run_fingerprint": run_fingerprint,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            raise

        results_by_key[key] = result
        completed.add(key)

        ordered_results = [
            results_by_key[checkpoint_key(s, i)]
            for s, i in datasets
            if checkpoint_key(s, i) in results_by_key
        ]

        _write_report(
            report_path,
            started_at,
            ordered_results,
        )

        checkpoint.save(
            {
                "run_type": "multi_dataset_research",
                "started_at": started_at,
                "status": "RUNNING",
                "current_index": index,
                "current_dataset": key,
                "completed": sorted(completed),
                "results": ordered_results,
                "report_path": str(report_path),
                "run_fingerprint": run_fingerprint,
            }
        )

    final_results = [
        results_by_key[checkpoint_key(s, i)]
        for s, i in datasets
        if checkpoint_key(s, i) in results_by_key
    ]

    checkpoint.save(
        {
            "run_type": "multi_dataset_research",
            "started_at": started_at,
            "status": "COMPLETED",
            "current_index": len(datasets),
            "current_dataset": None,
            "completed": sorted(completed),
            "results": final_results,
            "report_path": str(report_path),
            "run_fingerprint": run_fingerprint,
        }
    )

    return {
        "generated_at": started_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
        },
        "datasets": final_results,
        "run_fingerprint": run_fingerprint,
    }, report_path
