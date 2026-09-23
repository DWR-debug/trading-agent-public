from types import SimpleNamespace
from datetime import datetime, timedelta

from backtesting.models import Candle, BacktestTrade
from config.parameter_space import ParameterSpace
from validation.rolling_walk_forward import (
    RollingWalkForwardResult,
    RollingWalkForwardValidator,
)


def make_candles(count=50):
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


def test_requires_candles():
    try:
        RollingWalkForwardValidator(
            candles=(),
            symbol="TEST",
        )
    except ValueError:
        return

    raise AssertionError("Leere Candles wurden akzeptiert.")


def test_requires_symbol():
    try:
        RollingWalkForwardValidator(
            candles=make_candles(),
            symbol="",
        )
    except ValueError:
        return

    raise AssertionError("Leeres Symbol wurde akzeptiert.")


def test_rejects_invalid_sizes():
    candles = make_candles()

    invalid = [
        {"train_size": 1},
        {"test_size": 1},
        {"step_size": 0},
        {"minimum_trades_required": 0},
    ]

    for values in invalid:
        try:
            RollingWalkForwardValidator(
                candles=candles,
                symbol="TEST",
                **values,
            )
        except ValueError:
            continue

        raise AssertionError(
            f"Ungültige Parameter wurden akzeptiert: {values}"
        )


def test_rejects_insufficient_data():
    try:
        RollingWalkForwardValidator(
            candles=make_candles(10),
            symbol="TEST",
            train_size=8,
            test_size=5,
        )
    except ValueError:
        return

    raise AssertionError(
        "Zu wenige Candles wurden akzeptiert."
    )


def test_window_configuration():
    validator = RollingWalkForwardValidator(
        candles=make_candles(50),
        symbol="TEST",
        train_size=20,
        test_size=10,
        step_size=10,
        minimum_trades_required=5,
    )

    assert validator.train_size == 20
    assert validator.test_size == 10
    assert validator.step_size == 10
    assert validator.minimum_trades_required == 5


def test_parameter_space_is_preserved():
    space = ParameterSpace(
        momentum_lookbacks=[2],
        mean_reversion_windows=[4],
        mean_reversion_thresholds=[0.02],
        risk_per_trade_values=[0.01],
        leverage_values=[1.0],
    )

    validator = RollingWalkForwardValidator(
        candles=make_candles(50),
        symbol="TEST",
        parameter_space=space,
    )

    assert validator.parameter_space is space


def make_result(
    profit,
    trades,
    winrate,
    profit_factor,
    drawdown=1.0,
    sharpe=1.0,
    trade_pnls=None,
):
    return RollingWalkForwardResult(
        window_index=1,
        train_candles=20,
        test_candles=10,
        selected_candidate=None,
        test_net_profit_eur=profit,
        test_return_percent=profit / 5.0,
        test_win_rate_percent=winrate,
        test_profit_factor=profit_factor,
        test_max_drawdown_percent=drawdown,
        test_sharpe_ratio=sharpe,
        test_trade_count=trades,
        test_average_trade_eur=profit / trades if trades else 0.0,
        test_trades=tuple(
            BacktestTrade(
                symbol="TEST",
                side="BUY",
                entry_price=100.0,
                exit_price=100.0,
                quantity=1.0,
                entry_timestamp=datetime(2026, 1, 1),
                exit_timestamp=datetime(2026, 1, 1),
                pnl_eur=pnl,
                fees_eur=0.0,
            )
            for pnl in (
                trade_pnls
                if trade_pnls is not None
                else ([profit] if trades == 1 else [profit / trades] * trades)
            )
        ),
    )



def test_selection_metadata_tracks_profile_and_raw_score_separation():
    results = [
        SimpleNamespace(
            score=4.0,
            net_profit_eur=8.0,
            return_percent=1.6,
            win_rate_percent=60.0,
            profit_factor=1.5,
            max_drawdown_percent=2.0,
            sharpe_ratio=1.1,
            trade_count=20,
            average_trade_eur=0.4,
        ),
        SimpleNamespace(
            score=5.0,
            net_profit_eur=10.0,
            return_percent=2.0,
            win_rate_percent=65.0,
            profit_factor=1.8,
            max_drawdown_percent=2.5,
            sharpe_ratio=1.2,
            trade_count=18,
            average_trade_eur=0.5,
        ),
        SimpleNamespace(
            score=3.0,
            net_profit_eur=7.0,
            return_percent=1.4,
            win_rate_percent=55.0,
            profit_factor=1.3,
            max_drawdown_percent=3.0,
            sharpe_ratio=0.9,
            trade_count=16,
            average_trade_eur=0.4375,
        ),
    ]

    from validation.rolling_walk_forward import _selection_metadata

    metadata = _selection_metadata(results)

    assert metadata["selection_rank"] == 1
    assert metadata["selection_candidate_count"] == 3
    assert metadata["selection_score"] == 4.0
    assert metadata["selection_runner_up_score_gap"] == -1.0
    assert metadata["raw_score_rank"] == 2
    assert metadata["selected_vs_best_raw_score_gap"] == -1.0
    assert metadata["training_net_profit_eur"] == 8.0
    assert metadata["training_trade_count"] == 20

def test_summary_aggregates_results():
    validator = RollingWalkForwardValidator(
        candles=make_candles(50),
        symbol="TEST",
        minimum_trades_required=3,
    )

    results = (
        make_result(
            20.0,
            2,
            50.0,
            2.0,
            trade_pnls=(30.0, -10.0),
        ),
        make_result(
            -5.0,
            1,
            0.0,
            0.0,
            trade_pnls=(-5.0,),
        ),
    )

    summary = validator.summarize(results)

    assert summary.window_count == 2
    assert summary.total_test_candles == 20
    assert summary.total_net_profit_eur == 15.0
    assert summary.total_trade_count == 3
    assert summary.profitable_windows == 1
    assert summary.losing_windows == 1
    assert summary.zero_trade_windows == 0
    assert summary.statistically_sufficient is True
    assert summary.overall_profit_factor == 2.0


def test_summary_rejects_too_few_trades():
    validator = RollingWalkForwardValidator(
        candles=make_candles(50),
        symbol="TEST",
        minimum_trades_required=30,
    )

    results = (
        make_result(10.0, 2, 100.0, float("inf")),
    )

    summary = validator.summarize(results)

    assert summary.total_trade_count == 2
    assert summary.statistically_sufficient is False


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
    ("test_requires_candles", test_requires_candles),
    ("test_requires_symbol", test_requires_symbol),
    ("test_rejects_invalid_sizes", test_rejects_invalid_sizes),
    ("test_rejects_insufficient_data", test_rejects_insufficient_data),
    ("test_window_configuration", test_window_configuration),
    ("test_parameter_space_is_preserved", test_parameter_space_is_preserved),
    ("test_selection_metadata_tracks_profile_and_raw_score_separation", test_selection_metadata_tracks_profile_and_raw_score_separation),
    ("test_summary_aggregates_results", test_summary_aggregates_results),
    ("test_summary_rejects_too_few_trades", test_summary_rejects_too_few_trades),
]


passed = sum(
    run_test(name, test)
    for name, test in tests
)

print()
print(f"{passed}/{len(tests)} Rolling Walk-Forward Tests bestanden.")
