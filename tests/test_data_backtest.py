from data.csv_loader import load_candles
from backtesting.engine import BacktestEngine


def test_csv_data_runs_through_backtest():
    candles = load_candles(
        "tests/sample_candles_utc.csv"
    )

    engine = BacktestEngine(
        initial_capital=500.0,
        risk_per_trade=0.01,
        leverage=1.0,
    )

    result = engine.run(
        symbol="TEST",
        candles=candles,
    )

    assert result is not None
    assert result.initial_capital == 500.0
    assert result.final_capital > 0
