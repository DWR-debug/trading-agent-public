import pytest

from portfolio.capital_account import CapitalAccount, CapitalAccountingError
from portfolio.income_stress import (
    CapitalIncomePolicy,
    IncomePolicyError,
    sequence_sensitivity,
    simulate_capital_withdrawals,
)


def test_later_loss_reduces_future_distributable_profit():
    policy = CapitalIncomePolicy(
        payout_interval_periods=1,
        payout_fraction=1.0,
        capitalization_fraction=0.0,
    )

    result = simulate_capital_withdrawals((0.10, -0.05), policy)

    assert result.observations[0].payout_eur == pytest.approx(50.0)
    assert result.observations[1].payout_eur == pytest.approx(0.0)
    assert result.final_equity_eur == pytest.approx(475.0)
    assert result.total_payout_eur == pytest.approx(50.0)


def test_profit_can_be_capitalized_without_increasing_cash_payout():
    policy = CapitalIncomePolicy(
        payout_interval_periods=1,
        payout_fraction=0.0,
        capitalization_fraction=1.0,
    )

    result = simulate_capital_withdrawals((0.10,), policy)

    assert result.total_payout_eur == pytest.approx(0.0)
    assert result.total_capitalized_eur == pytest.approx(50.0)
    assert result.ending_protected_capital_eur == pytest.approx(550.0)
    assert result.final_equity_eur == pytest.approx(550.0)


def test_payout_and_capitalization_leave_unallocated_profit_working():
    policy = CapitalIncomePolicy(
        payout_interval_periods=1,
        payout_fraction=0.50,
        capitalization_fraction=0.25,
    )

    result = simulate_capital_withdrawals((0.10,), policy)

    assert result.total_payout_eur == pytest.approx(25.0)
    assert result.total_capitalized_eur == pytest.approx(12.5)
    assert result.final_equity_eur == pytest.approx(525.0)
    assert result.ending_protected_capital_eur == pytest.approx(512.5)


def test_reserve_blocks_part_of_profit_from_payout():
    policy = CapitalIncomePolicy(
        reserve_eur=25.0,
        payout_interval_periods=1,
        payout_fraction=1.0,
        capitalization_fraction=0.0,
    )

    result = simulate_capital_withdrawals((0.10,), policy)

    assert result.total_payout_eur == pytest.approx(25.0)
    assert result.final_equity_eur == pytest.approx(525.0)


def test_maximum_payout_cap_limits_interval_payment():
    policy = CapitalIncomePolicy(
        payout_interval_periods=1,
        payout_fraction=1.0,
        capitalization_fraction=0.0,
        maximum_payout_eur=10.0,
    )

    result = simulate_capital_withdrawals((0.10,), policy)

    assert result.total_payout_eur == pytest.approx(10.0)
    assert result.final_equity_eur == pytest.approx(540.0)


def test_sequence_sensitivity_is_deterministic_and_reports_both_orders():
    policy = CapitalIncomePolicy(
        payout_interval_periods=2,
        payout_fraction=1.0,
        capitalization_fraction=0.0,
    )

    sensitivity = sequence_sensitivity((0.20, -0.15, 0.10, 0.0), policy)

    assert len(sensitivity.chronological.observations) == 4
    assert len(sensitivity.reversed.observations) == 4
    assert sensitivity.chronological.total_payout_eur >= 0.0
    assert sensitivity.reversed.total_payout_eur >= 0.0


def test_policy_rejects_over_allocation():
    with pytest.raises(IncomePolicyError):
        CapitalIncomePolicy(
            payout_fraction=0.75,
            capitalization_fraction=0.50,
        )


def test_full_loss_is_rejected():
    with pytest.raises(IncomePolicyError):
        simulate_capital_withdrawals((-1.0,))



def test_capital_account_can_promote_distributable_profit():
    account = CapitalAccount(500.0)
    account.update_equity(550.0)
    account.record_realized_pnl(50.0)
    account.capitalize_profit(20.0)
    assert account.contributed_capital_eur == pytest.approx(520.0)
    assert account.equity_eur == pytest.approx(550.0)
    assert account.distributable_profit_eur == pytest.approx(30.0)


def test_capitalization_cannot_exceed_distributable_profit():
    account = CapitalAccount(500.0)
    account.update_equity(505.0)
    with pytest.raises(CapitalAccountingError):
        account.capitalize_profit(10.0)
