from automation.trial_028_per_sleeve_vol_budget_2026_09_24 import (
    TARGET_VOL,
    VOL_WINDOW,
    _gates,
    _vol,
)
from validation.research_gates import ResearchGateConfig


def _mode(
    research_return=0.20,
    research_dd=5.0,
    research_pf=1.2,
    rolling_pf=1.2,
    rolling_ratio=0.6,
    rolling_dd=5.0,
    oos_ratio=0.5,
    holdout_return=0.10,
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
            "profitable_window_ratio": rolling_ratio,
            "average_drawdown_percent": rolling_dd,
        },
        "oos_to_is_return_ratio": oos_ratio,
        "holdout": {
            "period_return": holdout_return,
            "max_drawdown_percent": holdout_dd,
            "profit_factor": holdout_pf,
        },
    }


def _scenario():
    mode = _mode()
    return {
        "base": {
            "fixed_candidate": mode,
            "per_sleeve_vol_budget": mode,
            "total_return_sensitivity": mode,
        },
        "stress_1_5x_cost": {
            "fixed_candidate": mode,
            "per_sleeve_vol_budget": mode,
            "total_return_sensitivity": mode,
        },
        "stress_2x_cost": {
            "fixed_candidate": mode,
            "per_sleeve_vol_budget": mode,
            "total_return_sensitivity": mode,
        },
    }


def test_vol_window_is_fixed():
    assert VOL_WINDOW == 63
    assert TARGET_VOL == 0.10


def test_vol_returns_none_before_warmup():
    assert _vol([0.0] * (VOL_WINDOW - 1)) is None


def test_vol_is_positive_after_warmup():
    history = [0.001 if i % 2 else -0.001 for i in range(VOL_WINDOW)]
    assert _vol(history) > 0.0


def test_gate_contract_passes_for_equal_strong_candidate():
    result = _gates(_scenario(), ResearchGateConfig())
    assert result["all_absolute_passed"] is True
    assert result["all_non_worsening_passed"] is True
    assert result["all_checks_passed"] is True


def test_gate_contract_blocks_holdout_deterioration():
    scenario = _scenario()
    scenario["base"]["per_sleeve_vol_budget"]["holdout"]["period_return"] = 0.05
    result = _gates(scenario, ResearchGateConfig())
    assert result["non_worsening_vs_fixed_candidate"]["holdout_return_not_below_fixed"] is False
    assert result["all_checks_passed"] is False
