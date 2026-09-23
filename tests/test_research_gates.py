from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from backtesting.models import Candle
from validation.research_gates import (
    ResearchGateConfig,
    check_backtest,
    check_data_quality,
    check_holdout,
    check_overfit,
    check_rolling_walk_forward,
    check_walk_forward,
    evaluate_research_gates,
)


def make_candles(count=600):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=start + timedelta(minutes=i),
            open=100.0 + i,
            high=100.0 + i,
            low=100.0 + i,
            close=100.0 + i,
            volume=1000.0,
        )
        for i in range(count)
    )


def base_baseline():
    return {
        "net_profit_eur": 10.0,
        "return_percent": 2.0,
        "win_rate_percent": 60.0,
        "profit_factor": 1.5,
        "max_drawdown_percent": 5.0,
        "sharpe_ratio": 1.0,
        "trade_count": 10,
        "average_trade_eur": 1.0,
    }


def base_wfo():
    return {
        "train_candles": 378,
        "test_candles": 162,
        "selected_candidate": {
            "risk_per_trade": 0.01,
            "leverage": 1.0,
            "strategy": {
                "momentum": {"lookback": 3},
                "mean_reversion": {
                    "window": 5,
                    "threshold": 0.02,
                },
            },
        },
        "test_net_profit_eur": 10.0,
        "test_return_percent": 2.0,
        "test_win_rate_percent": 60.0,
        "test_profit_factor": 1.5,
        "test_max_drawdown_percent": 5.0,
        "test_sharpe_ratio": 1.0,
        "test_trade_count": 20,
        "test_average_trade_eur": 0.5,
    }


def base_rolling():
    return {
        "window_count": 4,
        "total_test_candles": 400,
        "total_net_profit_eur": 20.0,
        "total_trade_count": 40,
        "overall_win_rate_percent": 57.5,
        "overall_profit_factor": 1.4,
        "average_trade_eur": 0.5,
        "average_drawdown_percent": 5.0,
        "average_sharpe_ratio": 1.1,
        "profitable_windows": 3,
        "losing_windows": 1,
        "zero_trade_windows": 0,
        "minimum_trades_required": 30,
        "statistically_sufficient": True,
    }


def base_holdout():
    return {
        "net_profit_eur": 10.0,
        "return_percent": 2.0,
        "win_rate_percent": 60.0,
        "profit_factor": 1.5,
        "max_drawdown_percent": 5.0,
        "sharpe_ratio": 1.0,
        "trade_count": 10,
        "average_trade_eur": 1.0,
    }


def test_data_quality_gate():
    gate = check_data_quality(
        make_candles(3),
        ResearchGateConfig(minimum_candles=3),
    )
    assert gate["passed"]
    assert gate["scope"] == "dataset_input"


def test_data_quality_gate_blocks_short_dataset():
    assert not check_data_quality(
        make_candles(3),
        ResearchGateConfig(),
    )["passed"]


def test_backtest_gate():
    gate = check_backtest(
        base_baseline(),
        ResearchGateConfig(),
    )
    assert gate["passed"]
    assert gate["scope"] == "baseline_sanity"


def test_backtest_gate_blocks_drawdown():
    metrics = base_baseline()
    metrics["max_drawdown_percent"] = 10.01
    assert not check_backtest(
        metrics,
        ResearchGateConfig(),
    )["passed"]


def test_walk_forward_gate():
    gate = check_walk_forward(
        base_wfo(),
        ResearchGateConfig(),
    )
    assert gate["passed"]
    assert gate["scope"] == "selected_candidate_oos"


def test_walk_forward_gate_blocks_weak_profit_factor():
    metrics = base_wfo()
    metrics["test_profit_factor"] = 1.09
    assert not check_walk_forward(
        metrics,
        ResearchGateConfig(),
    )["passed"]


def test_rolling_gate():
    gate = check_rolling_walk_forward(
        base_rolling(),
        ResearchGateConfig(),
    )
    assert gate["passed"]
    assert gate["scope"] == "rolling_selected_candidate_oos"


def test_rolling_gate_blocks_insufficient_trades():
    summary = base_rolling()
    summary["total_trade_count"] = 29
    assert not check_rolling_walk_forward(
        summary,
        ResearchGateConfig(),
    )["passed"]


def test_overfit_gate():
    gate = check_overfit(
        base_baseline(),
        base_wfo(),
        ResearchGateConfig(),
    )
    assert gate["passed"]
    assert gate["scope"] == "selected_candidate_train_vs_oos"


def test_overfit_gate_blocks_large_train_test_gap():
    test = base_wfo()
    test["test_return_percent"] = 0.49
    assert not check_overfit(
        base_baseline(),
        test,
        ResearchGateConfig(),
    )["passed"]


def test_holdout_gate():
    gate = check_holdout(
        base_holdout(),
        ResearchGateConfig(),
    )
    assert gate["passed"]
    assert gate["scope"] == "selected_candidate_holdout"


def test_holdout_gate_blocks_weak_result():
    metrics = base_holdout()
    metrics["trade_count"] = 9
    assert not check_holdout(
        metrics,
        ResearchGateConfig(),
    )["passed"]


def test_full_gate_report_passes():
    candles = make_candles()
    result = {
        "symbol": "TEST",
        "baseline": base_baseline(),
        "walk_forward": base_wfo(),
        "rolling_walk_forward": {
            "summary": base_rolling(),
        },
        "holdout": base_holdout(),
    }

    fake_metrics = base_baseline()

    with patch(
        "validation.research_gates._run_candidate",
        return_value=type(
            "Result",
            (),
            {"metrics": fake_metrics},
        )(),
    ):
        report = evaluate_research_gates(
            result,
            candles,
            train_ratio=0.7,
        )

    assert report["status"] == "PASSED"
    assert report["passed"] is True
    assert report["gate_count"] == 7
    assert report["passed_count"] == 7
    assert {gate["scope"] for gate in report["gates"]} == {
        "dataset_input",
        "baseline_sanity",
        "selected_candidate_oos",
        "rolling_selected_candidate_oos",
        "selected_candidate_robustness",
        "selected_candidate_train_vs_oos",
        "selected_candidate_holdout",
    }
