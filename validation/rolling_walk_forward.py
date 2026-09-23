"""
Trading Agent - Rolling Walk-Forward Validation

Wiederholte Out-of-Sample-Validierung:

Training-Fenster
    -> Optimierung
    -> unbekanntes Test-Fenster
    -> Fenster nach vorne verschieben

Nur Offline-Backtesting.
Keine Orderausführung.
Keine Netzwerkverbindung.
"""

from dataclasses import dataclass

from backtesting.engine import BacktestEngine
from backtesting.models import Candle, BacktestTrade
from config import settings
from config.parameter_space import ParameterCandidate
from config.parameters import StrategyParameters
from optimization.optimizer import Optimizer


@dataclass(frozen=True)
class RollingWalkForwardResult:
    window_index: int
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
    test_trades: tuple[BacktestTrade, ...]
    selection_rank: int | None = None
    selection_candidate_count: int | None = None
    selection_score: float | None = None
    selection_runner_up_score_gap: float | None = None
    raw_score_rank: int | None = None
    selected_vs_best_raw_score_gap: float | None = None
    training_net_profit_eur: float | None = None
    training_return_percent: float | None = None
    training_win_rate_percent: float | None = None
    training_profit_factor: float | None = None
    training_max_drawdown_percent: float | None = None
    training_sharpe_ratio: float | None = None
    training_trade_count: int | None = None
    training_average_trade_eur: float | None = None


@dataclass(frozen=True)
class RollingWalkForwardSummary:
    window_count: int
    total_test_candles: int
    total_net_profit_eur: float
    total_trade_count: int
    overall_win_rate_percent: float
    overall_profit_factor: float
    average_trade_eur: float
    average_drawdown_percent: float
    average_sharpe_ratio: float
    profitable_windows: int
    losing_windows: int
    zero_trade_windows: int
    minimum_trades_required: int
    statistically_sufficient: bool


def _selection_metadata(optimized_results: list) -> dict[str, float | int | None]:
    """Return deterministic training-selection metadata for the first result."""

    if not optimized_results:
        raise ValueError("Keine Optimierungsergebnisse für Selection-Metadaten.")

    selected = optimized_results[0]
    raw_score_rank = 1 + sum(
        result.score > selected.score
        for result in optimized_results
    )
    raw_best_score = max(result.score for result in optimized_results)

    runner_up_score_gap = None
    if len(optimized_results) >= 2:
        runner_up_score_gap = (
            selected.score - optimized_results[1].score
        )

    return {
        "selection_rank": 1,
        "selection_candidate_count": len(optimized_results),
        "selection_score": selected.score,
        "selection_runner_up_score_gap": runner_up_score_gap,
        "raw_score_rank": raw_score_rank,
        "selected_vs_best_raw_score_gap": selected.score - raw_best_score,
        "training_net_profit_eur": selected.net_profit_eur,
        "training_return_percent": selected.return_percent,
        "training_win_rate_percent": selected.win_rate_percent,
        "training_profit_factor": selected.profit_factor,
        "training_max_drawdown_percent": selected.max_drawdown_percent,
        "training_sharpe_ratio": selected.sharpe_ratio,
        "training_trade_count": selected.trade_count,
        "training_average_trade_eur": selected.average_trade_eur,
    }


class RollingWalkForwardValidator:
    def __init__(
        self,
        candles: tuple[Candle, ...],
        symbol: str,
        parameter_space=None,
        train_size: int = 30,
        test_size: int = 10,
        step_size: int = 10,
        minimum_trades_required: int = 30,
        selection_profile: str | None = None,
    ):
        if not candles:
            raise ValueError("Candles dürfen nicht leer sein.")

        if not symbol or not symbol.strip():
            raise ValueError("Symbol darf nicht leer sein.")

        if train_size < 2:
            raise ValueError("train_size muss mindestens 2 sein.")

        if test_size < 2:
            raise ValueError("test_size muss mindestens 2 sein.")

        if step_size < 1:
            raise ValueError("step_size muss mindestens 1 sein.")

        if minimum_trades_required < 1:
            raise ValueError(
                "minimum_trades_required muss mindestens 1 sein."
            )

        if len(candles) < train_size + test_size:
            raise ValueError(
                "Zu wenige Candles für Training und Test."
            )

        self.candles = candles
        self.symbol = symbol
        self.parameter_space = parameter_space
        self.train_size = train_size
        self.test_size = test_size
        self.step_size = step_size
        self.minimum_trades_required = minimum_trades_required
        self.selection_profile = selection_profile

    def validate(self) -> tuple[RollingWalkForwardResult, ...]:
        results = []

        start = 0
        window_index = 1

        while start + self.train_size + self.test_size <= len(self.candles):
            train_start = start
            train_end = start + self.train_size
            test_end = train_end + self.test_size

            train_candles = self.candles[train_start:train_end]
            test_candles = self.candles[train_end:test_end]

            optimizer = Optimizer(
                candles=train_candles,
                symbol=self.symbol,
                parameter_space=self.parameter_space,
            )

            selection_candidate_count = optimizer.parameter_space.size()
            if self.selection_profile is None:
                optimized_results = optimizer.optimize(
                    top_n=selection_candidate_count
                )
            else:
                optimized_results = optimizer.optimize(
                    top_n=selection_candidate_count,
                    selection_profile=self.selection_profile,
                )

            if not optimized_results:
                raise ValueError(
                    "Der Optimizer hat keinen Kandidaten geliefert."
                )

            selected_result = optimized_results[0]
            candidate = selected_result.candidate
            selection_metadata = _selection_metadata(optimized_results)

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
                candles=test_candles,
            )

            metrics = test_result.metrics

            results.append(
                RollingWalkForwardResult(
                    window_index=window_index,
                    train_candles=len(train_candles),
                    test_candles=len(test_candles),
                    selected_candidate=candidate,
                    test_net_profit_eur=metrics["net_profit_eur"],
                    test_return_percent=metrics["return_percent"],
                    test_win_rate_percent=metrics["win_rate_percent"],
                    test_profit_factor=metrics["profit_factor"],
                    test_max_drawdown_percent=metrics["max_drawdown_percent"],
                    test_sharpe_ratio=metrics["sharpe_ratio"],
                    test_trade_count=metrics["trade_count"],
                    test_average_trade_eur=metrics["average_trade_eur"],
                    test_trades=test_result.trades,
                    **selection_metadata,
                )
            )

            start += self.step_size
            window_index += 1

        return tuple(results)

    def summarize(
        self,
        results: tuple[RollingWalkForwardResult, ...],
    ) -> RollingWalkForwardSummary:
        if not results:
            raise ValueError(
                "Keine Rolling-Walk-Forward-Ergebnisse vorhanden."
            )

        total_net_profit = sum(
            result.test_net_profit_eur
            for result in results
        )
        total_trades = sum(
            result.test_trade_count
            for result in results
        )
        total_test_candles = sum(
            result.test_candles
            for result in results
        )

        winning_trades = sum(
            1
            for result in results
            for trade in result.test_trades
            if trade.pnl_eur > 0
        )

        if total_trades > 0:
            overall_win_rate = (
                winning_trades / total_trades
            ) * 100.0
        else:
            overall_win_rate = 0.0

        gross_profit = sum(
            max(trade.pnl_eur, 0.0)
            for result in results
            for trade in result.test_trades
        )
        gross_loss = sum(
            abs(min(trade.pnl_eur, 0.0))
            for result in results
            for trade in result.test_trades
        )

        if gross_loss > 0:
            overall_profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            overall_profit_factor = float("inf")
        else:
            overall_profit_factor = 0.0

        if total_trades > 0:
            average_trade = total_net_profit / total_trades
        else:
            average_trade = 0.0

        average_drawdown = sum(
            result.test_max_drawdown_percent
            for result in results
        ) / len(results)

        average_sharpe = sum(
            result.test_sharpe_ratio
            for result in results
        ) / len(results)

        profitable_windows = sum(
            1
            for result in results
            if result.test_net_profit_eur > 0
        )
        losing_windows = sum(
            1
            for result in results
            if result.test_net_profit_eur < 0
        )
        zero_trade_windows = sum(
            1
            for result in results
            if result.test_trade_count == 0
        )

        statistically_sufficient = (
            total_trades >= self.minimum_trades_required
        )

        return RollingWalkForwardSummary(
            window_count=len(results),
            total_test_candles=total_test_candles,
            total_net_profit_eur=total_net_profit,
            total_trade_count=total_trades,
            overall_win_rate_percent=overall_win_rate,
            overall_profit_factor=overall_profit_factor,
            average_trade_eur=average_trade,
            average_drawdown_percent=average_drawdown,
            average_sharpe_ratio=average_sharpe,
            profitable_windows=profitable_windows,
            losing_windows=losing_windows,
            zero_trade_windows=zero_trade_windows,
            minimum_trades_required=self.minimum_trades_required,
            statistically_sufficient=statistically_sufficient,
        )
