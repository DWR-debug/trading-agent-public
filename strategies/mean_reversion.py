from strategies.signals import SignalType, TradingSignal


class MeanReversionStrategy:
    def __init__(
        self,
        window: int = 5,
        threshold: float = 0.02,
    ):
        if window < 2:
            raise ValueError("Window muss mindestens 2 sein.")

        if threshold <= 0:
            raise ValueError("Threshold muss größer als 0 sein.")

        self.window = window
        self.threshold = threshold

    def _generate_signal(
        self,
        symbol: str,
        prices: list[float],
        validate_all: bool,
    ) -> TradingSignal:
        if not symbol:
            raise ValueError("Symbol darf nicht leer sein.")

        if len(prices) < self.window:
            raise ValueError(
                "Nicht genügend Preise für Mean-Reversion."
            )

        recent_prices = prices[-self.window:]

        if validate_all:
            if any(price <= 0 for price in prices):
                raise ValueError("Preise müssen größer als 0 sein.")
        else:
            if any(price <= 0 for price in recent_prices):
                raise ValueError("Preise müssen größer als 0 sein.")

        mean_price = (
            sum(recent_prices)
            / len(recent_prices)
        )

        current_price = prices[-1]

        deviation = (
            (current_price - mean_price)
            / mean_price
        )

        if deviation <= -self.threshold:
            return TradingSignal(
                symbol=symbol,
                signal=SignalType.BUY,
                confidence=min(
                    abs(deviation) / self.threshold,
                    1.0,
                ),
                reason="Preis unter Mittelwert",
            )

        if deviation >= self.threshold:
            return TradingSignal(
                symbol=symbol,
                signal=SignalType.SELL,
                confidence=min(
                    abs(deviation) / self.threshold,
                    1.0,
                ),
                reason="Preis über Mittelwert",
            )

        return TradingSignal(
            symbol=symbol,
            signal=SignalType.HOLD,
            confidence=0.0,
            reason="Preis nahe Mittelwert",
        )

    def generate_signal(
        self,
        symbol: str,
        prices: list[float],
    ) -> TradingSignal:
        return self._generate_signal(
            symbol,
            prices,
            validate_all=True,
        )

    def generate_signal_validated(
        self,
        symbol: str,
        prices: list[float],
    ) -> TradingSignal:
        """
        Interner schneller Pfad für bereits validierte Backtestdaten.
        """
        return self._generate_signal(
            symbol,
            prices,
            validate_all=False,
        )
