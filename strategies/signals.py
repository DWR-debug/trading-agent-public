"""
Trading Agent - Signal Model

Neutrales Signalmodell für alle Strategien.
Keine Orderausführung.
Keine Netzwerkverbindung.
"""

from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    HOLD = "HOLD"
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class TradingSignal:
    symbol: str
    signal: SignalType
    confidence: float
    reason: str

    def __post_init__(self):
        if not self.symbol:
            raise ValueError("Symbol darf nicht leer sein.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Confidence muss zwischen 0.0 und 1.0 liegen."
            )

        if not self.reason:
            raise ValueError("Reason darf nicht leer sein.")
