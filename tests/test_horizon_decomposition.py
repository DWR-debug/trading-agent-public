from automation.horizon_decomposition import (
    HOLDOUT_START,
    LONG_HOLDOUT_END,
    SHORT_HOLDOUT_END,
    _failed_criteria,
    _factorial_summary,
)


def test_control_indices():
    assert HOLDOUT_START == 4500
    assert SHORT_HOLDOUT_END == 4750
    assert LONG_HOLDOUT_END == 5000


def test_rolling_failure_criteria_are_explicit():
    gate = {
        "name": "rolling_walk_forward",
        "passed": False,
        "details": {
            "window_count": 5,
            "total_trade_count": 12,
            "minimum_total_trades": 30,
            "total_net_profit_eur": -4.0,
            "overall_profit_factor": 0.8,
            "minimum_profit_factor": 1.1,
            "profitable_window_ratio": 0.2,
            "minimum_profitable_window_ratio": 0.5,
            "zero_trade_window_ratio": 0.4,
            "maximum_zero_trade_window_ratio": 0.25,
            "average_drawdown_percent": 12.0,
            "maximum_drawdown_percent": 10.0,
        },
    }
    assert _failed_criteria(gate) == [
        "insufficient_total_trades",
        "nonpositive_total_profit",
        "profit_factor",
        "profitable_window_ratio",
        "zero_trade_window_ratio",
        "drawdown_limit",
    ]


def test_factorial_main_effects():
    rows = []
    for train, holdout, passed in (
        ("short_2250", "holdout_250", False),
        ("short_2250", "holdout_500", True),
        ("long_4500", "holdout_250", True),
        ("long_4500", "holdout_500", True),
    ):
        rows.append({
            "training_condition": train,
            "holdout_condition": holdout,
            "all_gates": {"holdout": {"passed": passed}},
        })
    summary = _factorial_summary(rows)["holdout"]
    assert summary["training_history_main_effect_pass_rate"] == 0.5
    assert summary["holdout_size_main_effect_pass_rate"] == 0.5
    assert summary["training_holdout_interaction"] == -1.0
