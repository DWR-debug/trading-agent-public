from __future__ import annotations
import json
from pathlib import Path

from automation import h06_p2_performance as perf
from automation import h06_p2_signal as signal

def test_h06_p2_gate_set_is_exactly_13():
    assert len(perf.GATES) == 13
    assert tuple(perf.GATES) == (
        "research_return_positive","research_drawdown_lte_10pct","research_profit_factor_gte_1_10",
        "rolling_profit_factor_gte_1_10","rolling_profitable_window_ratio_gte_0_50",
        "rolling_average_drawdown_lte_10pct","oos_to_is_return_ratio_gte_0_25",
        "holdout_return_positive","holdout_profit_factor_gte_1_10","holdout_drawdown_lte_10pct",
        "stress_1_5x_holdout_nonnegative","stress_2x_holdout_nonnegative",
        "total_return_sensitivity_holdout_nonnegative"
    )

def test_h06_p2_fixed_signal_contract():
    assert perf.ARM_IDS == ("H06-P2-RESIDUAL-GLOBAL-T5/B5","H06-P2-RAW-GLOBAL-T5/B5")
    assert signal.LOOKBACK == 252
    assert signal.SKIP == 21
    assert signal.TOP_K == 5
    assert signal.WEIGHT == 0.10

def test_h06_p2_zero_bootstrap_then_fixed_exposure():
    for arm_id in perf.ARM_IDS:
        weights = {s: 0.0 for s in signal.SYMBOLS}
        assert perf.gross_exposure(weights) == 0.0
        assert perf.net_exposure(weights) == 0.0

def test_h06_p2_safety_contract():
    assert perf.SAFETY == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
