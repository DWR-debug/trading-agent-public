from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from backtesting.models import Candle
from config import settings
from config.parameter_space import ParameterSpace
from validation.walk_forward import WalkForwardValidator


def make_candles(count=10):
    start = datetime(2026, 1, 1)

    return tuple(
        Candle(
            timestamp=start + timedelta(minutes=i),
            open=100.0 + i,
            high=100.0 + i,
            low=100.0 + i,
            close=100.0 + i,
            volume=1000.0,
        )
        for i in range(count)
    )


def test_walk_forward_requires_candles():
    try:
        WalkForwardValidator(
            candles=(),
            symbol="TEST",
        )
    except ValueError:
        return

    raise AssertionError("Leere Candles wurden akzeptiert.")


def test_walk_forward_requires_symbol():
    try:
        WalkForwardValidator(
            candles=make_candles(),
            symbol="",
        )
    except ValueError:
        return

    raise AssertionError("Leeres Symbol wurde akzeptiert.")


def test_walk_forward_rejects_invalid_train_ratio():
    for ratio in (0.49, 1.0, 1.5):
        try:
            WalkForwardValidator(
                candles=make_candles(10),
                symbol="TEST",
                train_ratio=ratio,
            )
        except ValueError:
            continue

        raise AssertionError(
            f"Ungültiger train_ratio {ratio} wurde akzeptiert."
        )


def test_walk_forward_splits_data():
    validator = WalkForwardValidator(
        candles=make_candles(10),
        symbol="TEST",
        train_ratio=0.7,
    )

    assert len(validator.train_candles) == 7
    assert len(validator.test_candles) == 3

    assert (
        validator.train_candles[-1].timestamp
        < validator.test_candles[0].timestamp
    )


def test_walk_forward_preserves_order():
    candles = make_candles(20)

    validator = WalkForwardValidator(
        candles=candles,
        symbol="TEST",
        train_ratio=0.7,
    )

    combined = validator.train_candles + validator.test_candles

    assert combined == candles


def test_walk_forward_accepts_parameter_space():
    space = ParameterSpace(
        momentum_lookbacks=[2],
        mean_reversion_windows=[4],
        mean_reversion_thresholds=[0.02],
        risk_per_trade_values=[0.01],
        leverage_values=[1.0],
    )

    validator = WalkForwardValidator(
        candles=make_candles(10),
        symbol="TEST",
        parameter_space=space,
    )

    assert validator.parameter_space is space


def test_walk_forward_uses_configured_initial_capital():
    candidate = next(
        ParameterSpace(
            momentum_lookbacks=[2],
            mean_reversion_windows=[4],
            mean_reversion_thresholds=[0.02],
            risk_per_trade_values=[0.01],
            leverage_values=[1.0],
        ).candidates()
    )
    captured = {}

    class FakeOptimizer:
        def __init__(self, candles, symbol, parameter_space=None):
            pass

        def optimize(self, top_n=1):
            return [SimpleNamespace(candidate=candidate)]

    class FakeBacktestEngine:
        def __init__(
            self,
            initial_capital,
            risk_per_trade,
            leverage,
            parameters,
        ):
            captured["initial_capital"] = initial_capital

        def run(self, symbol, candles):
            return SimpleNamespace(
                metrics={
                    "net_profit_eur": 0.0,
                    "return_percent": 0.0,
                    "win_rate_percent": 0.0,
                    "profit_factor": 0.0,
                    "max_drawdown_percent": 0.0,
                    "sharpe_ratio": 0.0,
                    "trade_count": 0,
                    "average_trade_eur": 0.0,
                }
            )

    expected_capital = 1234.56

    with patch.object(
        settings,
        "INITIAL_CAPITAL_EUR",
        expected_capital,
    ), patch(
        "validation.walk_forward.Optimizer",
        FakeOptimizer,
    ), patch(
        "validation.walk_forward.BacktestEngine",
        FakeBacktestEngine,
    ):
        WalkForwardValidator(
            candles=make_candles(10),
            symbol="TEST",
        ).validate()

    assert captured["initial_capital"] == expected_capital


def run_test(name, test):
    try:
        test()
        print(f"PASS: {name}")
        return True
    except Exception as exc:
        print(f"FAIL: {name}")
        print(f"      {type(exc).__name__}: {exc}")
        return False


tests = [
    ("test_walk_forward_requires_candles", test_walk_forward_requires_candles),
    ("test_walk_forward_requires_symbol", test_walk_forward_requires_symbol),
    (
        "test_walk_forward_rejects_invalid_train_ratio",
        test_walk_forward_rejects_invalid_train_ratio,
    ),
    ("test_walk_forward_splits_data", test_walk_forward_splits_data),
    ("test_walk_forward_preserves_order", test_walk_forward_preserves_order),
    (
        "test_walk_forward_accepts_parameter_space",
        test_walk_forward_accepts_parameter_space,
    ),
    (
        "test_walk_forward_uses_configured_initial_capital",
        test_walk_forward_uses_configured_initial_capital,
    ),
]

passed = sum(run_test(name, test) for name, test in tests)

print()
print(f"{passed}/{len(tests)} Walk-Forward Tests bestanden.")

if passed != len(tests):
    raise SystemExit(1)
