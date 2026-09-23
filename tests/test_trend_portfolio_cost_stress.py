from automation.trend_portfolio_cost_stress import (
    SCENARIOS,
    STRATEGIES,
    _stats,
)


def test_cost_scenarios_are_fixed_and_non_optimized():
    assert SCENARIOS == (
        ("base", 0.0015),
        ("stress_2x_cost", 0.003),
    )
    assert STRATEGIES == (
        "tsm_ensemble_risk_normalized",
        "sma_50_200_risk_normalized",
    )


def test_stats_is_empty_safe():
    result = _stats([], 0, 10)
    assert result["day_count"] == 0
    assert result["period_return"] == 0.0
    assert result["profit_factor"] == 0.0


def test_cost_stress_does_not_change_day_count():
    returns = [0.01, -0.01, 0.02, 0.0, 0.01]
    base = _stats(returns, 0, 5)
    stress = _stats(returns, 0, 5)

    assert base["day_count"] == stress["day_count"]
