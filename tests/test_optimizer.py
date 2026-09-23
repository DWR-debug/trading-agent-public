from datetime import datetime, timedelta

from backtesting.models import Candle
from config.parameter_space import ParameterCandidate, ParameterSpace
from config.parameters import MomentumParameters, MeanReversionParameters, StrategyParameters
from optimization.optimizer import Optimizer


def make_candles():
    prices = [130, 90, 90, 90, 95, 100, 100, 100, 95]

    return tuple(
        Candle(
            timestamp=datetime(2026, 1, 1) + timedelta(minutes=i),
            open=price,
            high=price * 1.005,
            low=price * 0.995,
            close=price,
            volume=1000,
        )
        for i, price in enumerate(prices)
    )


def make_candidate(
    risk_per_trade=0.01,
    leverage=1.0,
):
    strategy = StrategyParameters(
        momentum=MomentumParameters(lookback=3),
        mean_reversion=MeanReversionParameters(
            window=5,
            threshold=0.02,
        ),
    )

    return ParameterCandidate(
        strategy=strategy,
        risk_per_trade=risk_per_trade,
        leverage=leverage,
    )


def test_optimizer_requires_candles():
    try:
        Optimizer(
            candles=(),
            symbol="TEST",
        )
    except ValueError:
        return

    raise AssertionError("Leere Candles wurden akzeptiert.")


def test_optimizer_requires_symbol():
    try:
        Optimizer(
            candles=make_candles(),
            symbol="",
        )
    except ValueError:
        return

    raise AssertionError("Leeres Symbol wurde akzeptiert.")


def test_optimizer_evaluates_candidate():
    optimizer = Optimizer(
        candles=make_candles(),
        symbol="TEST",
    )

    result = optimizer.evaluate_candidate(
        make_candidate()
    )

    assert result.candidate.risk_per_trade == 0.01
    assert result.candidate.leverage == 1.0
    assert isinstance(result.score, float)


def test_optimizer_rejects_excessive_risk():
    try:
        make_candidate(risk_per_trade=0.02)
    except ValueError:
        return
    raise AssertionError("Zu hohes Risiko wurde akzeptiert.")


def test_optimizer_rejects_excessive_leverage():
    try:
        make_candidate(leverage=4.0)
    except ValueError:
        return
    raise AssertionError("Zu hoher Hebel wurde akzeptiert.")


def test_optimizer_runs_small_space():
    parameter_space = ParameterSpace(
        momentum_lookbacks=[3],
        mean_reversion_windows=[5],
        mean_reversion_thresholds=[0.02],
        risk_per_trade_values=[0.01],
        leverage_values=[1.0],
    )

    optimizer = Optimizer(
        candles=make_candles(),
        symbol="TEST",
        parameter_space=parameter_space,
    )

    results = optimizer.optimize(top_n=1)

    assert parameter_space.size() == 1
    assert len(results) == 1


def test_optimizer_rejects_invalid_top_n():
    optimizer = Optimizer(
        candles=make_candles(),
        symbol="TEST",
    )

    try:
        optimizer.optimize(top_n=0)
    except ValueError:
        return

    raise AssertionError("Ungültiges top_n wurde akzeptiert.")


def run_all_tests():
    tests = [
        test_optimizer_requires_candles,
        test_optimizer_requires_symbol,
        test_optimizer_evaluates_candidate,
        test_optimizer_rejects_excessive_risk,
        test_optimizer_rejects_excessive_leverage,
        test_optimizer_runs_small_space,
        test_optimizer_rejects_invalid_top_n,
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
        passed += 1

    print()
    print(f"{passed}/{len(tests)} Optimizer-Tests bestanden.")


if __name__ == "__main__":
    run_all_tests()
