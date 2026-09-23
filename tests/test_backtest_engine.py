from datetime import datetime, timedelta, timezone

from backtesting.engine import BacktestEngine
from backtesting.models import Candle


def make_candle(timestamp, price):
    return Candle(
        timestamp=timestamp,
        open=price,
        high=price * 1.005,
        low=price * 0.995,
        close=price,
        volume=1000.0,
    )


def test_backtest_requires_candles():
    engine = BacktestEngine()

    try:
        engine.run("TEST", [])
    except ValueError:
        return

    raise AssertionError(
        "Backtest darf keine leeren Daten akzeptieren."
    )


def test_backtest_requires_valid_symbol():
    engine = BacktestEngine()

    candles = [
        make_candle(
            datetime.now(timezone.utc),
            100.0,
        )
    ]

    try:
        engine.run("", candles)
    except ValueError:
        return

    raise AssertionError(
        "Backtest darf kein leeres Symbol akzeptieren."
    )


def test_backtest_runs_without_crashing():
    engine = BacktestEngine()

    start = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    candles = []

    prices = [
        100,
        101,
        102,
        103,
        104,
        103,
        102,
        101,
        100,
        99,
        98,
        99,
        100,
    ]

    for index, price in enumerate(prices):
        candles.append(
            make_candle(
                start + timedelta(minutes=index),
                price,
            )
        )

    result = engine.run(
        "TEST",
        candles,
    )

    assert result.initial_capital == 500.0
    assert result.final_capital > 0
    assert isinstance(result.trades, tuple)


def test_backtest_rejects_excessive_risk():
    try:
        BacktestEngine(
            risk_per_trade=0.02
        )
    except ValueError:
        return

    raise AssertionError(
        "Backtest darf 2% Risiko nicht akzeptieren."
    )


def test_backtest_rejects_excessive_leverage():
    try:
        BacktestEngine(
            leverage=4.0
        )
    except ValueError:
        return

    raise AssertionError(
        "Backtest darf 4x Hebel nicht akzeptieren."
    )


def run_all_tests():
    tests = [
        test_backtest_requires_candles,
        test_backtest_requires_valid_symbol,
        test_backtest_runs_without_crashing,
        test_backtest_rejects_excessive_risk,
        test_backtest_rejects_excessive_leverage,
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
        passed += 1

    print()
    print(
        f"{passed}/{len(tests)} "
        "Backtest-Engine-Tests bestanden."
    )


if __name__ == "__main__":
    run_all_tests()
