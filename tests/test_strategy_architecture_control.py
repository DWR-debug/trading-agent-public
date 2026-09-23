from datetime import datetime, timedelta, timezone

from config.parameter_space import ParameterSpace
from config.parameters import StrategyParameters
from automation.strategy_architecture_control import (
    ASSETS,
    FIXED_LEVERAGE,
    FIXED_RISK_PER_TRADE,
    MODES,
    _aggregate_pf,
    _build_mode_signals,
    _candidate_pool,
)


def _candles(count=40):
    from backtesting.models import Candle

    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return [
        Candle(
            timestamp=start + timedelta(days=index),
            open=100.0 + index,
            high=101.0 + index,
            low=99.0 + index,
            close=100.5 + index,
            volume=1000.0,
        )
        for index in range(count)
    ]


def test_candidate_pool_is_fixed_to_one_risk_and_leverage():
    candidates = _candidate_pool()

    assert len(candidates) == 80
    assert {
        candidate.risk_per_trade for candidate in candidates
    } == {FIXED_RISK_PER_TRADE}
    assert {
        candidate.leverage for candidate in candidates
    } == {FIXED_LEVERAGE}


def test_candidate_pool_matches_strategy_only_parameter_grid():
    space = ParameterSpace(
        risk_per_trade_values=[FIXED_RISK_PER_TRADE],
        leverage_values=[FIXED_LEVERAGE],
    )

    assert len(tuple(space.candidates())) == len(_candidate_pool())


def test_all_ablation_modes_emit_one_signal_per_candle():
    candles = _candles()
    parameters = StrategyParameters()

    from config.parameter_space import ParameterCandidate

    candidate = ParameterCandidate(
        strategy=parameters,
        risk_per_trade=FIXED_RISK_PER_TRADE,
        leverage=FIXED_LEVERAGE,
    )

    for mode in MODES:
        signals = _build_mode_signals(
            candles,
            "TEST",
            candidate,
            mode,
        )
        assert len(signals) == len(candles)
        non_warmup = [signal for signal in signals if signal is not None]
        assert non_warmup
        assert all(signal.symbol == "TEST" for signal in non_warmup)


def test_aggregate_pf_handles_profit_and_loss():
    rows = [
        {"total_net_profit_eur": 10.0},
        {"total_net_profit_eur": -5.0},
        {"total_net_profit_eur": 15.0},
    ]

    assert _aggregate_pf(rows) == 5.0


def test_ablation_surface_has_three_assets():
    assert ASSETS == ("SPY", "QQQ", "IWM")
