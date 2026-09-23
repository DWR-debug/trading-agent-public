from types import SimpleNamespace

from config.parameter_space import ParameterCandidate, ParameterSpace
from config.parameters import (
    MeanReversionParameters,
    MomentumParameters,
    StrategyParameters,
)
from optimization.optimizer import OptimizationResult, Optimizer


def _candidate(*, lookback, window, threshold, risk, leverage):
    return ParameterCandidate(
        strategy=StrategyParameters(
            momentum=MomentumParameters(lookback=lookback),
            mean_reversion=MeanReversionParameters(
                window=window,
                threshold=threshold,
            ),
        ),
        risk_per_trade=risk,
        leverage=leverage,
    )


def _result(candidate, score):
    return OptimizationResult(
        candidate=candidate,
        net_profit_eur=score,
        return_percent=score,
        win_rate_percent=50.0,
        profit_factor=1.2,
        max_drawdown_percent=5.0,
        sharpe_ratio=1.0,
        trade_count=10,
        average_trade_eur=1.0,
        score=score,
    )


def test_score_max_is_control_profile():
    space = ParameterSpace(
        momentum_lookbacks=[3, 5, 8],
        mean_reversion_windows=[5, 10, 20],
        mean_reversion_thresholds=[0.01, 0.02, 0.05],
        risk_per_trade_values=[0.0025, 0.005, 0.01],
        leverage_values=[1.0, 2.0, 3.0],
    )
    center = _candidate(
        lookback=5, window=10, threshold=0.02, risk=0.005, leverage=2.0
    )
    edge = _candidate(
        lookback=3, window=5, threshold=0.01, risk=0.0025, leverage=1.0
    )

    profile_score = SimpleNamespace(
        rank_key=lambda result, parameter_space: (result.score,),
    )
    assert profile_score.rank_key(_result(edge, 100.0), space) > (
        profile_score.rank_key(_result(center, 90.0), space)
    )


def test_optimizer_selection_profiles_can_change_selection(monkeypatch):
    space = ParameterSpace(
        momentum_lookbacks=[3, 5, 8],
        mean_reversion_windows=[5, 10, 20],
        mean_reversion_thresholds=[0.01, 0.02, 0.05],
        risk_per_trade_values=[0.0025, 0.005, 0.01],
        leverage_values=[1.0, 2.0, 3.0],
    )
    center = _candidate(
        lookback=5, window=10, threshold=0.02, risk=0.005, leverage=2.0
    )
    edge = _candidate(
        lookback=3, window=5, threshold=0.01, risk=0.01, leverage=3.0
    )

    by_key = {
        (
            center.strategy.momentum.lookback,
            center.strategy.mean_reversion.window,
            center.strategy.mean_reversion.threshold,
            center.risk_per_trade,
            center.leverage,
        ): _result(center, 90.0),
        (
            edge.strategy.momentum.lookback,
            edge.strategy.mean_reversion.window,
            edge.strategy.mean_reversion.threshold,
            edge.risk_per_trade,
            edge.leverage,
        ): _result(edge, 100.0),
    }

    optimizer = Optimizer(
        candles=(SimpleNamespace(close=100.0),),
        symbol="TEST",
        parameter_space=space,
    )

    def fake_evaluate(candidate):
        key = (
            candidate.strategy.momentum.lookback,
            candidate.strategy.mean_reversion.window,
            candidate.strategy.mean_reversion.threshold,
            candidate.risk_per_trade,
            candidate.leverage,
        )
        return by_key.get(key, _result(candidate, -1.0))

    monkeypatch.setattr(
        optimizer,
        "_evaluate_candidate_cached",
        fake_evaluate,
    )

    score_selected = optimizer.optimize(
        top_n=1,
        selection_profile="score_max",
    )[0].candidate
    boundary_selected = optimizer.optimize(
        top_n=1,
        selection_profile="boundary_averse",
    )[0].candidate

    assert score_selected == edge
    assert boundary_selected == center
