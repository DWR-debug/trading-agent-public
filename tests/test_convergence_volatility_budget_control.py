from automation.convergence_volatility_budget_control import (
    MAX_SCALE,
    TARGET_VOL,
    VOL_WINDOW,
    RESULTS,
    SCENARIOS,
    _rolling_vol,
    _stats,
)


def test_volatility_budget_is_fixed_and_deleveraging_only():
    assert TARGET_VOL == 0.10
    assert VOL_WINDOW == 63
    assert MAX_SCALE == 1.0
    assert RESULTS == (
        "unscaled_baseline",
        "vol_budget_10pct",
    )


def test_cost_scenarios_are_pre_registered():
    assert SCENARIOS == (
        ("base", 1.0),
        ("stress_2x_cost", 2.0),
    )


def test_rolling_vol_uses_only_prior_history():
    history = [
        0.01 if index % 2 == 0 else -0.005
        for index in range(VOL_WINDOW)
    ]
    value = _rolling_vol(history)
    assert value > 0.0

    assert _rolling_vol(history[:-1]) is None


def test_stats_handles_empty_input():
    result = _stats([], 0, 0)
    assert result["day_count"] == 0
    assert result["period_return"] == 0.0
