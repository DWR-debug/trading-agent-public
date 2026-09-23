"""
Trading Agent - Strategy Engine

Kombiniert mehrere unabhängige Strategien.

Die Strategieparameter werden von außen injiziert,
damit Backtesting und spätere Optimierung möglich sind.

Keine Orderausführung.
Keine Netzwerkverbindung.
"""

from config.parameters import StrategyParameters
from strategies.signals import SignalType, TradingSignal
from strategies.momentum import MomentumStrategy
from strategies.mean_reversion import MeanReversionStrategy


class StrategyEngine:
    COMBINATION_THRESHOLD = 0.25

    def __init__(
        self,
        parameters: StrategyParameters | None = None,
        momentum: MomentumStrategy | None = None,
        mean_reversion: MeanReversionStrategy | None = None,
    ):
        self.parameters = parameters or StrategyParameters()

        self.momentum = momentum or MomentumStrategy(
            lookback=self.parameters.momentum.lookback
        )

        self.mean_reversion = mean_reversion or MeanReversionStrategy(
            window=self.parameters.mean_reversion.window,
            threshold=self.parameters.mean_reversion.threshold,
        )

    def _combine_signals(
        self,
        momentum_signal: TradingSignal,
        mean_reversion_signal: TradingSignal,
    ) -> TradingSignal:
        threshold = self.COMBINATION_THRESHOLD

        def signed_confidence(signal: TradingSignal) -> float:
            if signal.signal == SignalType.BUY:
                return signal.confidence

            if signal.signal == SignalType.SELL:
                return -signal.confidence

            return 0.0

        momentum_score = signed_confidence(momentum_signal)
        mean_reversion_score = signed_confidence(mean_reversion_signal)

        combined_score = (
            momentum_score + mean_reversion_score
        ) / 2.0

        if combined_score >= threshold:
            return TradingSignal(
                symbol=momentum_signal.symbol,
                signal=SignalType.BUY,
                confidence=round(min(abs(combined_score), 1.0), 10),
                reason="Signal Combiner: gewichtetes BUY-Signal.",
            )

        if combined_score <= -threshold:
            return TradingSignal(
                symbol=momentum_signal.symbol,
                signal=SignalType.SELL,
                confidence=round(min(abs(combined_score), 1.0), 10),
                reason="Signal Combiner: gewichtetes SELL-Signal.",
            )

        return TradingSignal(
            symbol=momentum_signal.symbol,
            signal=SignalType.HOLD,
            confidence=0.0,
            reason=(
                "Signal Combiner: Score unterhalb der "
                "Entscheidungsschwelle."
            ),
        )

    def generate_signal(
        self,
        symbol: str,
        prices: list[float],
    ) -> TradingSignal:
        momentum_signal = self.momentum.generate_signal(
            symbol,
            prices,
        )

        mean_reversion_signal = self.mean_reversion.generate_signal(
            symbol,
            prices,
        )

        return self._combine_signals(
            momentum_signal,
            mean_reversion_signal,
        )

    def generate_signal_validated(
        self,
        symbol: str,
        prices: list[float],
    ) -> TradingSignal:
        """
        Schneller interner Pfad für bereits validierte Backtestdaten.

        Die öffentliche generate_signal()-Methode behält weiterhin
        ihre vollständige Eingabevalidierung.
        """
        momentum_signal = self.momentum.generate_signal_validated(
            symbol,
            prices,
        )

        mean_reversion_signal = (
            self.mean_reversion.generate_signal_validated(
                symbol,
                prices,
            )
        )

        return self._combine_signals(
            momentum_signal,
            mean_reversion_signal,
        )
