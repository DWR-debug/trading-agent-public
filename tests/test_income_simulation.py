import pytest

from portfolio.income_simulation import (
    IncomePolicy,
    IncomeSimulationError,
    simulate_income,
)


def test_default_policy_protects_500_eur():
    result = simulate_income((0.10,))
    assert result.final_equity_eur == pytest.approx(550.0)
    assert result.total_payout_eur == pytest.approx(0.0)


def test_profit_is_paid_only_at_payout_interval_and_new_high():
    policy = IncomePolicy(payout_interval_periods=2)

    result = simulate_income((0.10, 0.0, 0.0, 0.10), policy)

    assert result.total_payout_eur == pytest.approx(55.0)
    assert result.payout_count == 2
    assert result.final_equity_eur == pytest.approx(550.0)


def test_temporary_gain_cannot_be_paid_after_drawdown():
    policy = IncomePolicy(payout_interval_periods=2)

    result = simulate_income((0.10, -0.10), policy)

    assert result.total_payout_eur == pytest.approx(0.0)
    assert result.final_equity_eur == pytest.approx(495.0)


def test_partial_payout_retains_profit_in_working_capital():
    policy = IncomePolicy(
        payout_fraction=0.5,
        payout_interval_periods=1,
    )

    result = simulate_income((0.10,), policy)

    assert result.total_payout_eur == pytest.approx(25.0)
    assert result.final_equity_eur == pytest.approx(525.0)


def test_reserve_reduces_payoutable_surplus():
    policy = IncomePolicy(
        reserve_eur=25.0,
        payout_interval_periods=1,
    )

    result = simulate_income((0.10,), policy)

    assert result.total_payout_eur == pytest.approx(25.0)
    assert result.final_equity_eur == pytest.approx(525.0)


def test_invalid_full_loss_is_rejected():
    with pytest.raises(IncomeSimulationError):
        simulate_income((-1.0,))


def test_payout_fraction_range_is_enforced():
    with pytest.raises(IncomeSimulationError):
        IncomePolicy(payout_fraction=1.1)
