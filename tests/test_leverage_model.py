import pytest

from research.leverage_model import (
    LeverageConfig,
    LeverageMode,
    LeverageModelError,
    period_return,
    portfolio_period_return,
    simulate_portfolio_path,
    simulate_leveraged_path,
)


def test_margin_leverage_scales_signed_return():
    config = LeverageConfig(multiple=2.0)
    assert period_return(0.05, 1.0, config) == pytest.approx(0.10)
    assert period_return(0.05, -1.0, config) == pytest.approx(-0.10)


def test_margin_financing_and_short_borrow_are_separate_costs():
    config = LeverageConfig(
        multiple=2.0,
        financing_rate_annual=0.10,
        short_borrow_rate_annual=0.20,
    )
    value = period_return(-0.01, -1.0, config)
    expected = 0.02 - (0.10 / 252.0) - (0.40 / 252.0)
    assert value == pytest.approx(expected)


def test_portfolio_model_separates_gross_and_short_exposure():
    config = LeverageConfig(
        multiple=2.0,
        financing_rate_annual=0.05,
        short_borrow_rate_annual=0.10,
    )
    value = portfolio_period_return(0.01, 1.0, 0.5, config)
    expected = 0.02 - (0.05 / 252.0) - (0.10 / 252.0)
    assert value == pytest.approx(expected)


def test_daily_reset_product_is_path_dependent():
    config = LeverageConfig(multiple=2.0, mode=LeverageMode.DAILY_RESET_PRODUCT)
    path = simulate_leveraged_path((0.10, -0.10), (1.0, 1.0), config)
    assert path.final_equity == pytest.approx(0.96)


def test_short_can_lose_more_than_basis_notional_but_simulation_fails_closed():
    config = LeverageConfig(multiple=1.0)
    result = simulate_leveraged_path((2.0,), (-1.0,), config)
    assert result.ruined is True
    assert result.final_equity == pytest.approx(0.0)


def test_leveraged_path_fails_closed_at_zero_equity():
    config = LeverageConfig(multiple=3.0)
    path = simulate_leveraged_path((-0.40,), (1.0,), config)
    assert path.ruined is True
    assert path.final_equity == pytest.approx(0.0)
    assert path.maximum_drawdown == pytest.approx(1.0)


def test_lengths_must_match():
    with pytest.raises(LeverageModelError):
        simulate_leveraged_path((0.01,), ())

def test_portfolio_path_supports_simultaneous_long_and_short_exposure():
    config = LeverageConfig(multiple=1.5)
    result = simulate_portfolio_path(
        (0.01, -0.01),
        (1.0, 1.0),
        (0.5, 0.5),
        config,
    )

    assert result.final_equity > 0.0
    assert result.ruined is False
