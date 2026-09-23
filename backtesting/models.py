"""
Trading Agent - Backtesting Datenmodelle

Neutrale Modelle für historische Marktdaten und virtuelle Trades.

Keine Orderausführung.
Keine Netzwerkverbindung.
Kein Echtgeldhandel.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Candle:
    """
    Eine historische OHLCV-Kerze.
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self):
        if not isinstance(self.timestamp, datetime):
            raise ValueError("Timestamp muss ein datetime sein.")

        if self.open <= 0:
            raise ValueError("Open muss größer als 0 sein.")

        if self.high <= 0:
            raise ValueError("High muss größer als 0 sein.")

        if self.low <= 0:
            raise ValueError("Low muss größer als 0 sein.")

        if self.close <= 0:
            raise ValueError("Close muss größer als 0 sein.")

        if self.volume < 0:
            raise ValueError("Volume darf nicht negativ sein.")

        if self.high < max(self.open, self.close):
            raise ValueError(
                "High muss mindestens Open und Close erreichen."
            )

        if self.low > min(self.open, self.close):
            raise ValueError(
                "Low muss höchstens Open und Close erreichen."
            )

        if self.low > self.high:
            raise ValueError(
                "Low darf nicht größer als High sein."
            )


@dataclass(frozen=True)
class BacktestTrade:
    """
    Ein vollständig abgeschlossener virtueller Trade.
    """

    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_timestamp: datetime
    exit_timestamp: datetime
    pnl_eur: float
    fees_eur: float

    def __post_init__(self):
        if not self.symbol:
            raise ValueError("Symbol darf nicht leer sein.")

        if self.side not in {"BUY", "SELL"}:
            raise ValueError(
                "Side muss BUY oder SELL sein."
            )

        if self.entry_price <= 0:
            raise ValueError(
                "Entry-Preis muss größer als 0 sein."
            )

        if self.exit_price <= 0:
            raise ValueError(
                "Exit-Preis muss größer als 0 sein."
            )

        if self.quantity <= 0:
            raise ValueError(
                "Quantity muss größer als 0 sein."
            )

        if self.fees_eur < 0:
            raise ValueError(
                "Gebühren dürfen nicht negativ sein."
            )

        if self.exit_timestamp < self.entry_timestamp:
            raise ValueError(
                "Exit darf nicht vor Entry liegen."
            )
