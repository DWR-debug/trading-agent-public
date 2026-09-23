"""
Trading Agent - Walk-Forward Validation

Optimiert auf einem Trainingsfenster und validiert den
ausgewählten Kandidaten anschließend auf einem getrennten
Out-of-Sample-Testfenster.

Nur Offline-Backtesting.
Keine Orderausführung.
Keine Netzwerkverbindung.
"""

from dataclasses import dataclass

from backtesting.engine import BacktestEngine
from backtesting.models import Candle
from config import settings
from config.parameter_space import ParameterCandidate
from config.parameters import StrategyParameters
from optimization.optimizer import Optimizer


@dataclass(frozen=True)
class WalkForwardResult:
    train_candles: int
    test_candles: int
    selected_candidate: ParameterCandidate
    test_net_profit_eur: float
    test_return_percent: float
    test_win_rate_percent: float
    test_profit_factor: float
    test_max_drawdown_percent: float
    test_sharpe_ratio: float
    test_trade_count: int
    test_average_trade_eur: float


class WalkForwardValidator:
    def __init__(
        self,
        candles: tuple[Candle, ...],
        symbol: str,
        parameter_space=None,
        train_ratio: float = 0.7,
        selection_profile: str | None = None,
    ):
        if not candles:
            raise ValueError("Candles dürfen nicht leer sein.")

        if not symbol or not symbol.strip():
            raise ValueError("Symbol darf nicht leer sein.")

        if not 0.5 <= train_ratio < 1.0:
            raise ValueError(
                "train_ratio muss zwischen 0.5 und kleiner 1.0 liegen."
            )

        split_index = int(len(candles) * train_ratio)

        if split_index < 2:
            raise ValueError("Zu wenige Trainings-Candles.")

        if len(candles) - split_index < 2:
            raise ValueError("Zu wenige Test-Candles.")

        self.candles = candles
        self.symbol = symbol
        self.parameter_space = parameter_space
        self.train_ratio = train_ratio
        self.selection_profile = selection_profile

        self.train_candles = candles[:split_index]
        self.test_candles = candles[split_index:]

    def validate(self) -> WalkForwardResult:
        optimizer = Optimizer(
            candles=self.train_candles,
            symbol=self.symbol,
            parameter_space=self.parameter_space,
        )

        if self.selection_profile is None:
            optimized_results = optimizer.optimize(top_n=1)
        else:
            optimized_results = optimizer.optimize(
                top_n=1,
                selection_profile=self.selection_profile,
            )

        if not optimized_results:
            raise ValueError(
                "Der Optimizer hat keinen Kandidaten geliefert."
            )

        best_result = optimized_results[0]
        candidate = best_result.candidate

        strategy_parameters = StrategyParameters(
            momentum=candidate.strategy.momentum,
            mean_reversion=candidate.strategy.mean_reversion,
        )

        backtest = BacktestEngine(
            initial_capital=settings.INITIAL_CAPITAL_EUR,
            risk_per_trade=candidate.risk_per_trade,
            leverage=candidate.leverage,
            parameters=strategy_parameters,
        )

        test_result = backtest.run(
            symbol=self.symbol,
            candles=self.test_candles,
        )

        metrics = test_result.metrics

        return WalkForwardResult(
            train_candles=len(self.train_candles),
            test_candles=len(self.test_candles),
            selected_candidate=candidate,
            test_net_profit_eur=metrics["net_profit_eur"],
            test_return_percent=metrics["return_percent"],
            test_win_rate_percent=metrics["win_rate_percent"],
            test_profit_factor=metrics["profit_factor"],
            test_max_drawdown_percent=metrics["max_drawdown_percent"],
            test_sharpe_ratio=metrics["sharpe_ratio"],
            test_trade_count=metrics["trade_count"],
            test_average_trade_eur=metrics["average_trade_eur"],
        )
