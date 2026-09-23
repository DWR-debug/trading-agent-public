from strategies.signals import SignalType, TradingSignal


class MomentumStrategy:
    def __init__(self, lookback: int = 5):
        if lookback < 1:
            raise ValueError("Lookback muss mindestens 1 sein.")

        self.lookback = lookback

    def _generate_signal(
        self,
        symbol: str,
        prices: list[float],
        validate_all: bool,
    ) -> TradingSignal:
        if not symbol:
            raise ValueError("Symbol darf nicht leer sein.")

        if len(prices) < self.lookback + 1:
            raise ValueError("Nicht genügend Preise für Momentum.")

        if validate_all:
            if any(price <= 0 for price in prices):
                raise ValueError("Preise müssen größer als 0 sein.")
        else:
            previous_price = prices[-self.lookback - 1]
            current_price = prices[-1]

            if previous_price <= 0 or current_price <= 0:
                raise ValueError("Preise müssen größer als 0 sein.")

        previous_price = prices[-self.lookback - 1]
        current_price = prices[-1]

        momentum = (
            (current_price - previous_price)
            / previous_price
        )

        if momentum > 0:
            return TradingSignal(
                symbol=symbol,
                signal=SignalType.BUY,
                confidence=min(abs(momentum) * 10.0, 1.0),
                reason="Positives Momentum",
            )

        if momentum < 0:
            return TradingSignal(
                symbol=symbol,
                signal=SignalType.SELL,
                confidence=min(abs(momentum) * 10.0, 1.0),
                reason="Negatives Momentum",
            )

        return TradingSignal(
            symbol=symbol,
            signal=SignalType.HOLD,
            confidence=0.0,
            reason="Kein Momentum",
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

        Es wird nur geprüft, dass die für das Momentum tatsächlich
        benötigten Preise gültig sind.
        """
        return self._generate_signal(
            symbol,
            prices,
            validate_all=False,
        )
