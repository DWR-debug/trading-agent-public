from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from automation.trial_026_common_market_momentum_gate_2026_09_24 import (
    MARKET_MOMENTUM_LOOKBACK,
    _checks,
    _market_gate,
)
from validation.research_gates import ResearchGateConfig


def _scenario(*, holdout_return=0.10):
    mode = {
        "research": {"period_return": 0.20, "max_drawdown_percent": 5.0, "profit_factor": 1.2},
        "rolling_summary": {
            "overall_profit_factor": 1.2,
            "profitable_window_ratio": 0.6,
            "average_drawdown_percent": 5.0,
        },
        "oos_to_is_return_ratio": 0.5,
        "holdout": {"period_return": holdout_return, "max_drawdown_percent": 5.0, "profit_factor": 1.2},
    }
    return {
        "base": {"baseline": mode, "market_momentum_gate": mode},
        "stress_1_5x_cost": {"baseline": mode, "market_momentum_gate": mode},
        "stress_2x_cost": {"baseline": mode, "market_momentum_gate": mode},
    }


def test_market_gate_is_positive_after_lookback():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = tuple(SimpleNamespace(timestamp=base + timedelta(days=i)) for i in range(MARKET_MOMENTUM_LOOKBACK + 1))
    adjusted = {bar.timestamp: float(i + 1) for i, bar in enumerate(bars)}
    result = _market_gate(bars, adjusted, {bars[-1].timestamp})
    assert result[bars[-1].timestamp] is True


def test_market_gate_is_off_for_negative_momentum():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = tuple(SimpleNamespace(timestamp=base + timedelta(days=i)) for i in range(MARKET_MOMENTUM_LOOKBACK + 1))
    adjusted = {bar.timestamp: 100.0 for bar in bars}
    adjusted[bars[-1].timestamp] = 90.0
    result = _market_gate(bars, adjusted, {bars[-1].timestamp})
    assert result[bars[-1].timestamp] is False


def test_market_gate_warmup_is_open():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = tuple(SimpleNamespace(timestamp=base + timedelta(days=i)) for i in range(MARKET_MOMENTUM_LOOKBACK))
    adjusted = {bar.timestamp: 100.0 for bar in bars}
    result = _market_gate(bars, adjusted, {bars[-1].timestamp})
    assert result[bars[-1].timestamp] is True


def test_checks_require_absolute_and_non_worsening_contract():
    config = ResearchGateConfig()
    result = _checks(_scenario(), config)
    assert result["all_absolute_passed"] is True
    assert result["all_non_worsening_passed"] is True
    assert result["all_checks_passed"] is True


def test_checks_block_when_holdout_return_worsens():
    config = ResearchGateConfig()
    scenario = _scenario()
    scenario["base"]["market_momentum_gate"] = {
        **scenario["base"]["market_momentum_gate"],
        "holdout": {
            **scenario["base"]["market_momentum_gate"]["holdout"],
            "period_return": 0.05,
        },
    }
    result = _checks(scenario, config)
    assert result["non_worsening_vs_fixed_candidate"]["holdout_return_not_worse"] is False
    assert result["all_checks_passed"] is False
