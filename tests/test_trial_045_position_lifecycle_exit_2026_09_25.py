from datetime import datetime, timedelta, timezone

from backtesting.models import Candle
from validation.research_gates import ResearchGateConfig

from automation.trial_045_position_lifecycle_exit_2026_09_25 import (
    ATR_MULTIPLE,
    ATR_WINDOW,
    _atr_value,
    _gates,
    _stop_triggered,
)


def _bars(count: int, high: float = 102.0, low: float = 98.0) -> tuple[Candle, ...]:
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=start + timedelta(days=index),
            open=100.0,
            high=high,
            low=low,
            close=100.0,
            volume=1.0,
        )
        for index in range(count)
    )


def test_atr_requires_warmup():
    bars = _bars(ATR_WINDOW)
    assert _atr_value(bars, ATR_WINDOW - 1) is None


def test_atr_uses_simple_true_range_average():
    bars = _bars(ATR_WINDOW + 1)
    assert _atr_value(bars, ATR_WINDOW) == 4.0


def test_trailing_stop_threshold_is_strict():
    assert _stop_triggered(110.0, 94.9, 5.0)
    assert not _stop_triggered(110.0, 95.0, 5.0)
    assert not _stop_triggered(110.0, 95.1, 5.0)


def test_trailing_stop_ignores_missing_or_zero_atr():
    assert not _stop_triggered(110.0, 90.0, None)
    assert not _stop_triggered(110.0, 90.0, 0.0)


def test_fixed_exit_definition():
    assert ATR_WINDOW == 20
    assert ATR_MULTIPLE == 3.0


def _mode(
    research_return=0.2,
    research_dd=5.0,
    research_pf=1.2,
    rolling_pf=1.2,
    profitable_ratio=0.6,
    rolling_dd=5.0,
    oos_is=0.5,
    holdout_return=0.1,
    holdout_dd=5.0,
    holdout_pf=1.2,
):
    return {
        "research": {
            "period_return": research_return,
            "max_drawdown_percent": research_dd,
            "profit_factor": research_pf,
        },
        "rolling_summary": {
            "overall_profit_factor": rolling_pf,
            "profitable_window_ratio": profitable_ratio,
            "average_drawdown_percent": rolling_dd,
        },
        "oos_to_is_return_ratio": oos_is,
        "holdout": {
            "period_return": holdout_return,
            "max_drawdown_percent": holdout_dd,
            "profit_factor": holdout_pf,
        },
    }


def _scenario():
    fixed = _mode()
    challenger = _mode()
    return {
        "base": {
            "fixed_candidate": {"price_only": fixed},
            "exit_challenger": {
                "price_only": challenger,
                "total_return_sensitivity": challenger,
            },
        },
        "stress_1_5x_cost": {
            "fixed_candidate": {"price_only": fixed},
            "exit_challenger": {"price_only": challenger},
        },
        "stress_2x_cost": {
            "fixed_candidate": {"price_only": fixed},
            "exit_challenger": {"price_only": challenger},
        },
    }


def test_gate_contract_passes_for_equal_strong_candidate():
    result = _gates(_scenario(), ResearchGateConfig())
    assert result["all_absolute_passed"]
    assert result["all_non_worsening_passed"]
    assert result["all_checks_passed"]


def test_gate_contract_blocks_deterioration_vs_fixed():
    scenario = _scenario()
    scenario["base"]["exit_challenger"]["price_only"] = {
        **_mode(research_return=0.1),
    }
    result = _gates(scenario, ResearchGateConfig())
    assert not result["non_worsening_vs_fixed_candidate"]["research_return_not_below_fixed"]
    assert not result["all_checks_passed"]
