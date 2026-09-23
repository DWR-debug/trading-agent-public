from datetime import datetime, timezone

from backtesting.models import Candle, BacktestTrade


def test_valid_candle():
    candle = Candle(
        timestamp=datetime.now(timezone.utc),
        open=100.0,
        high=105.0,
        low=98.0,
        close=103.0,
        volume=1000.0,
    )

    assert candle.close == 103.0


def test_invalid_candle_price():
    try:
        Candle(
            timestamp=datetime.now(timezone.utc),
            open=0.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000.0,
        )
    except ValueError:
        return

    raise AssertionError(
        "Ungültiger Candle-Preis wurde akzeptiert."
    )


def test_invalid_candle_ohlc_relationship():
    try:
        Candle(
            timestamp=datetime.now(timezone.utc),
            open=100.0,
            high=99.0,
            low=98.0,
            close=103.0,
            volume=1000.0,
        )
    except ValueError:
        return

    raise AssertionError(
        "Ungültige OHLC-Beziehung wurde akzeptiert."
    )


def test_valid_backtest_trade():
    trade = BacktestTrade(
        symbol="TEST",
        side="BUY",
        entry_price=100.0,
        exit_price=105.0,
        quantity=1.0,
        entry_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        exit_timestamp=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        pnl_eur=5.0,
        fees_eur=0.10,
    )

    assert trade.pnl_eur == 5.0


def test_invalid_trade_side():
    try:
        BacktestTrade(
            symbol="TEST",
            side="INVALID",
            entry_price=100.0,
            exit_price=105.0,
            quantity=1.0,
            entry_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            exit_timestamp=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
            pnl_eur=5.0,
            fees_eur=0.10,
        )
    except ValueError:
        return

    raise AssertionError(
        "Ungültige Trade-Seite wurde akzeptiert."
    )


def run_all_tests():
    tests = [
        test_valid_candle,
        test_invalid_candle_price,
        test_invalid_candle_ohlc_relationship,
        test_valid_backtest_trade,
        test_invalid_trade_side,
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
        passed += 1

    print()
    print(f"{passed}/{len(tests)} Backtesting-Modelltests bestanden.")


if __name__ == "__main__":
    run_all_tests()
