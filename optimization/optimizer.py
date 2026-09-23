"""
Trading Agent - Parameter Optimizer

Testet erlaubte Parameterkombinationen über den Backtest.

WICHTIG:
Der Optimizer darf niemals zentrale Sicherheitslimits
aus config.settings.py überschreiben.

Optimierung:
Die Signale werden pro eindeutiger Strategie-Konfiguration
nur einmal berechnet und anschließend für unterschiedliche
Risiko-/Hebel-Kombinationen wiederverwendet.
"""

from dataclasses import dataclass

from backtesting.engine import BacktestEngine
from backtesting.models import Candle
from config import settings
from config.parameter_space import ParameterCandidate, ParameterSpace
from optimization.selection_profiles import get_selection_profile
from strategies.signals import TradingSignal
from strategies.strategy_engine import StrategyEngine


@dataclass(frozen=True)
class OptimizationResult:
    candidate: ParameterCandidate
    net_profit_eur: float
    return_percent: float
    win_rate_percent: float
    profit_factor: float
    max_drawdown_percent: float
    sharpe_ratio: float
    trade_count: int
    average_trade_eur: float
    score: float


class Optimizer:
    def __init__(
        self,
        candles: tuple[Candle, ...],
        symbol: str,
        parameter_space: ParameterSpace | None = None,
    ):
        if not candles:
            raise ValueError(
                "Für die Optimierung werden Candles benötigt."
            )

        if not symbol:
            raise ValueError(
                "Symbol darf nicht leer sein."
            )

        self.candles = candles
        self.symbol = symbol
        self.parameter_space = (
            parameter_space or ParameterSpace()
        )

        # Cache für bereits berechnete Signalfolgen.
        # Schlüssel: (Momentum-Lookback, MR-Window, MR-Threshold)
        self._signal_cache: dict[
            tuple[int, int, float],
            tuple[TradingSignal | None, ...],
        ] = {}

    @staticmethod
    def calculate_score(metrics: dict) -> float:
        """
        Ermittelt einen einfachen risikoadjustierten Score.

        Der Score belohnt:
        - positive Rendite
        - gute Sharpe Ratio
        - hohen Profit Factor

        und bestraft:
        - hohen Drawdown
        - zu wenige Trades
        """

        if metrics["trade_count"] < 2:
            return -1_000_000.0

        profit_factor = metrics["profit_factor"]

        if profit_factor == float("inf"):
            profit_factor_score = 10.0
        else:
            profit_factor_score = profit_factor

        score = (
            metrics["return_percent"]
            + metrics["sharpe_ratio"] * 10.0
            + profit_factor_score * 2.0
            - metrics["max_drawdown_percent"] * 2.0
        )

        return score

    @staticmethod
    def _strategy_key(
        candidate: ParameterCandidate,
    ) -> tuple[int, int, float]:
        """
        Liefert den Cache-Schlüssel für die Strategieparameter.

        Risiko und Hebel gehören bewusst NICHT zum Schlüssel,
        weil sie die erzeugten Signale nicht verändern.
        """

        return (
            candidate.strategy.momentum.lookback,
            candidate.strategy.mean_reversion.window,
            candidate.strategy.mean_reversion.threshold,
        )

    def _build_signals(
        self,
        candidate: ParameterCandidate,
    ) -> tuple[TradingSignal | None, ...]:
        """
        Berechnet die komplette Signalfolge für eine Strategie
        genau einmal.

        Das Verhalten entspricht der ursprünglichen Signalberechnung
        im BacktestEngine: Während der Warm-up-Phase bzw. bei einer
        ValueError wird None gespeichert.
        """

        strategy_engine = StrategyEngine(
            parameters=candidate.strategy,
        )

        prices: list[float] = []
        signals: list[TradingSignal | None] = []

        for candle in self.candles:
            prices.append(candle.close)

            try:
                signal = strategy_engine.generate_signal_validated(
                    self.symbol,
                    prices,
                )
            except ValueError:
                signal = None

            signals.append(signal)

        return tuple(signals)

    def _get_cached_signals(
        self,
        candidate: ParameterCandidate,
    ) -> tuple[TradingSignal | None, ...]:
        """Liefert Signale aus dem Cache oder berechnet sie einmal."""

        key = self._strategy_key(candidate)

        cached = self._signal_cache.get(key)

        if cached is not None:
            return cached

        signals = self._build_signals(candidate)
        self._signal_cache[key] = signals

        return signals

    @staticmethod
    def _result_from_metrics(
        candidate: ParameterCandidate,
        metrics: dict,
    ) -> OptimizationResult:
        """Erzeugt ein OptimizationResult aus Backtest-Metriken."""

        score = Optimizer.calculate_score(metrics)

        return OptimizationResult(
            candidate=candidate,
            net_profit_eur=metrics["net_profit_eur"],
            return_percent=metrics["return_percent"],
            win_rate_percent=metrics["win_rate_percent"],
            profit_factor=metrics["profit_factor"],
            max_drawdown_percent=metrics["max_drawdown_percent"],
            sharpe_ratio=metrics["sharpe_ratio"],
            trade_count=metrics["trade_count"],
            average_trade_eur=metrics["average_trade_eur"],
            score=score,
        )

    def _validate_candidate(
        self,
        candidate: ParameterCandidate,
    ) -> None:
        """Prüft die zentralen Sicherheitslimits."""

        if candidate.risk_per_trade > settings.RISK_PER_TRADE:
            raise ValueError(
                "Optimizer-Kandidat überschreitet "
                "das zentrale Risiko-Limit."
            )

        if candidate.leverage > settings.MAX_LEVERAGE:
            raise ValueError(
                "Optimizer-Kandidat überschreitet "
                "das zentrale Hebel-Limit."
            )

    def evaluate_candidate(
        self,
        candidate: ParameterCandidate,
    ) -> OptimizationResult:

        self._validate_candidate(candidate)

        engine = BacktestEngine(
            initial_capital=settings.INITIAL_CAPITAL_EUR,
            risk_per_trade=candidate.risk_per_trade,
            leverage=candidate.leverage,
            parameters=candidate.strategy,
        )

        result = engine.run(
            symbol=self.symbol,
            candles=self.candles,
        )

        return self._result_from_metrics(
            candidate,
            result.metrics,
        )

    def _evaluate_candidate_cached(
        self,
        candidate: ParameterCandidate,
    ) -> OptimizationResult:
        """
        Bewertet einen Kandidaten mit bereits berechneten Signalen.

        Dadurch entfällt die erneute Strategieausführung für jede
        Risiko-/Hebel-Kombination derselben Strategie.
        """

        self._validate_candidate(candidate)

        signals = self._get_cached_signals(candidate)

        engine = BacktestEngine(
            initial_capital=settings.INITIAL_CAPITAL_EUR,
            risk_per_trade=candidate.risk_per_trade,
            leverage=candidate.leverage,
            parameters=candidate.strategy,
        )

        result = engine.run(
            symbol=self.symbol,
            candles=self.candles,
            signals=signals,
        )

        return self._result_from_metrics(
            candidate,
            result.metrics,
        )

    def optimize(
        self,
        top_n: int = 10,
        selection_profile: str | None = None,
    ) -> list[OptimizationResult]:

        if top_n < 1:
            raise ValueError(
                "top_n muss mindestens 1 sein."
            )

        profile = get_selection_profile(selection_profile)
        results = []

        for candidate in self.parameter_space.candidates():
            result = self._evaluate_candidate_cached(candidate)
            results.append(result)

        results.sort(
            key=lambda result: profile.rank_key(
                result,
                self.parameter_space,
            ),
            reverse=True,
        )

        return results[:top_n]
