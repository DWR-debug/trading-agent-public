import pytest

from automation.multi_asset_trend_portfolio_control import (
    ASSETS,
    PORTFOLIO_STRATEGIES,
    _stats,
)


def test_portfolio_control_uses_fixed_assets():
    assert ASSETS == ("SPY", "QQQ", "IWM")


def test_portfolio_strategy_set_is_pre_registered():
    assert PORTFOLIO_STRATEGIES == (
        "buy_and_hold",
        "tsm_ensemble",
        "sma_50_200_long_flat",
        "blend_tsm_sma",
    )


def test_stats_has_expected_research_and_holdout_segments():
    returns = [0.01] * 10
    research = _stats(returns, 0, 10)
    holdout = _stats(returns, 5, 10)

    assert research["day_count"] == 8
    assert holdout["day_count"] == 3
    assert research["period_return"] > holdout["period_return"] > 0


def test_stats_calculates_profit_factor():
    result = _stats([0.10, -0.05, 0.05], 0, 6)
    assert result["profit_factor"] == pytest.approx(3.0)


def test_stats_is_empty_safe():
    result = _stats([], 0, 10)
    assert result["day_count"] == 0
    assert result["period_return"] == 0.0
    assert result["profit_factor"] == 0.0
