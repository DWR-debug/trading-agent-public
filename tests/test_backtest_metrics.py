from datetime import datetime, timedelta, timezone

from backtesting.metrics import (
    calculate_average_trade,
    calculate_max_drawdown_percent,
    calculate_metrics,
    calculate_net_profit,
    calculate_profit_factor,
    calculate_return_percent,
    calculate_sharpe_ratio,
    calculate_win_rate,
)
from backtesting.models import BacktestTrade


def make_trade(pnl, index):
    start = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    return BacktestTrade(
        symbol="TEST",
        side="BUY",
        entry_price=100.0,
        exit_price=105.0,
        quantity=1.0,
        entry_timestamp=start + timedelta(hours=index),
        exit_timestamp=start + timedelta(hours=index, minutes=30),
        pnl_eur=pnl,
        fees_eur=0.10,
    )


def test_net_profit():
    trades = (
        make_trade(10.0, 0),
        make_trade(-4.0, 1),
        make_trade(6.0, 2),
    )

    assert calculate_net_profit(trades) == 12.0


def test_return_percent():
    trades = (
        make_trade(10.0, 0),
        make_trade(-5.0, 1),
    )

    result = calculate_return_percent(
        500.0,
        trades,
    )

    assert result == 1.0


def test_win_rate():
    trades = (
        make_trade(10.0, 0),
        make_trade(-5.0, 1),
        make_trade(5.0, 2),
        make_trade(-2.0, 3),
    )

    assert calculate_win_rate(trades) == 50.0


def test_profit_factor():
    trades = (
        make_trade(10.0, 0),
        make_trade(5.0, 1),
        make_trade(-5.0, 2),
    )

    assert calculate_profit_factor(trades) == 3.0


def test_max_drawdown():
    trades = (
        make_trade(10.0, 0),
        make_trade(-20.0, 1),
        make_trade(5.0, 2),
    )

    result = calculate_max_drawdown_percent(
        500.0,
        trades,
    )

    expected = (20.0 / 510.0) * 100.0

    assert abs(result - expected) < 1e-9


def test_sharpe_ratio():
    trades = (
        make_trade(10.0, 0),
        make_trade(-5.0, 1),
        make_trade(10.0, 2),
    )

    result = calculate_sharpe_ratio(
        500.0,
        trades,
    )

    assert result > 0


def test_average_trade():
    trades = (
        make_trade(10.0, 0),
        make_trade(-4.0, 1),
        make_trade(6.0, 2),
    )

    assert calculate_average_trade(trades) == 4.0


def test_empty_trades():
    trades = ()

    metrics = calculate_metrics(
        500.0,
        trades,
    )

    assert metrics["net_profit_eur"] == 0.0
    assert metrics["return_percent"] == 0.0
    assert metrics["win_rate_percent"] == 0.0
    assert metrics["profit_factor"] == 0.0
    assert metrics["max_drawdown_percent"] == 0.0
    assert metrics["sharpe_ratio"] == 0.0
    assert metrics["trade_count"] == 0
    assert metrics["average_trade_eur"] == 0.0


def run_all_tests():
    tests = [
        test_net_profit,
        test_return_percent,
        test_win_rate,
        test_profit_factor,
        test_max_drawdown,
        test_sharpe_ratio,
        test_average_trade,
        test_empty_trades,
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
        passed += 1

    print()
    print(
        f"{passed}/{len(tests)} "
        "Backtesting-Metrics-Tests bestanden."
    )


if __name__ == "__main__":
    run_all_tests()
