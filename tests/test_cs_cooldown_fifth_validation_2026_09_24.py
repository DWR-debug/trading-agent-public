from datetime import datetime, timezone

from automation.cs_cooldown_fifth_validation_2026_09_24 import (
    COOLDOWN_SESSIONS,
    CS_REBALANCE,
    CS_TOP_N,
    HOLDOUT_COUNT,
    RESEARCH_COUNT,
    TARGET_COUNT,
    _holdout_confirmation,
    _research_hypothesis_check,
)


def test_fixed_validation_contract():
    assert TARGET_COUNT == 3500
    assert RESEARCH_COUNT == 2798
    assert HOLDOUT_COUNT == 700
    assert COOLDOWN_SESSIONS == 1
    assert CS_REBALANCE == 21
    assert CS_TOP_N == 2


def test_research_hypothesis_requires_all_fixed_directions():
    def scenario(dd, pf, avg_dd, ret):
        return {
            "base": {
                "vol_budget_10pct": {
                    "price_only": {
                        "research": {"max_drawdown_percent": dd},
                        "rolling_summary": {
                            "overall_profit_factor": pf,
                            "average_drawdown_percent": avg_dd,
                            "total_net_return": ret,
                        },
                    }
                }
            }
        }

    baseline = scenario(20.0, 1.05, 15.0, 0.10)
    improved = scenario(19.0, 1.06, 14.0, 0.11)
    mixed = scenario(19.0, 1.04, 14.0, 0.11)

    assert _research_hypothesis_check(
        baseline,
        improved,
    )["all_checks_passed"] is True
    assert _research_hypothesis_check(
        baseline,
        mixed,
    )["all_checks_passed"] is False


def test_holdout_confirmation_is_non_worsening_only():
    def scenario(ret, dd, pf):
        return {
            "base": {
                "vol_budget_10pct": {
                    "price_only": {
                        "holdout": {
                            "period_return": ret,
                            "max_drawdown_percent": dd,
                            "profit_factor": pf,
                        }
                    }
                }
            }
        }

    baseline = scenario(0.10, 12.0, 1.10)
    cooldown = scenario(0.10, 11.0, 1.10)
    assert _holdout_confirmation(
        baseline,
        cooldown,
    )["all_checks_passed"] is True

    worse = scenario(0.09, 11.0, 1.10)
    assert _holdout_confirmation(
        baseline,
        worse,
    )["all_checks_passed"] is False
