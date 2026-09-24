import pytest

from portfolio.capital_account import CapitalAccount, CapitalAccountingError


def test_initial_capital_is_500_eur():
    account = CapitalAccount()
    snapshot = account.snapshot()

    assert snapshot.contributed_capital_eur == pytest.approx(500.0)
    assert snapshot.equity_eur == pytest.approx(500.0)
    assert snapshot.distributable_profit_eur == pytest.approx(0.0)


def test_only_realized_profit_above_capital_base_is_distributable():
    account = CapitalAccount()
    account.record_realized_pnl(100.0)
    account.update_equity(600.0)

    assert account.distributable_profit_eur == pytest.approx(100.0)

    account.record_profit_withdrawal(60.0)

    assert account.snapshot().equity_eur == pytest.approx(540.0)
    assert account.distributable_profit_eur == pytest.approx(40.0)


def test_unrealized_equity_gain_does_not_create_distributable_profit():
    account = CapitalAccount()
    account.update_equity(600.0)

    assert account.distributable_profit_eur == pytest.approx(0.0)


def test_contribution_increases_protected_capital():
    account = CapitalAccount()
    account.record_contribution(250.0)
    account.record_realized_pnl(50.0)
    account.update_equity(800.0)

    assert account.snapshot().contributed_capital_eur == pytest.approx(750.0)
    assert account.snapshot().equity_eur == pytest.approx(800.0)
    assert account.distributable_profit_eur == pytest.approx(50.0)


def test_withdrawal_cannot_reduce_protected_capital():
    account = CapitalAccount()
    account.record_realized_pnl(100.0)

    with pytest.raises(CapitalAccountingError):
        account.record_profit_withdrawal(101.0)


def test_realized_loss_reduces_distributable_profit():
    account = CapitalAccount()
    account.record_realized_pnl(100.0)
    account.record_realized_pnl(-80.0)
    account.update_equity(520.0)

    assert account.snapshot().net_realized_pnl_eur == pytest.approx(20.0)
    assert account.distributable_profit_eur == pytest.approx(20.0)
