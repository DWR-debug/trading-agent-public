"""
Datenqualitätsprüfung für historische OHLCV-Candles.

Keine Netzwerkverbindung.
Keine Orderausführung.
Kein Echtgeldhandel.
"""

import math
from datetime import timezone
from collections.abc import Sequence

from backtesting.models import Candle


def validate_candles(candles: Sequence[Candle]) -> None:
    """
    Prüft eine Candle-Sequenz auf grundlegende Datenqualität.

    Anforderungen:
    - nicht leer
    - ausschließlich Candle-Objekte
    - alle numerischen Werte endlich
    - chronologisch aufsteigend
    - keine doppelten Timestamps
    """

    if not candles:
        raise ValueError("Candle-Liste darf nicht leer sein.")

    previous_timestamp = None

    for index, candle in enumerate(candles):
        if not isinstance(candle, Candle):
            raise ValueError(
                f"Element {index} ist keine Candle."
            )

        values = (
            candle.open,
            candle.high,
            candle.low,
            candle.close,
            candle.volume,
        )

        if not all(math.isfinite(value) for value in values):
            raise ValueError(
                f"Element {index} enthält NaN oder Infinity."
            )

        if candle.timestamp.tzinfo is None:
            raise ValueError(
                f"Element {index} enthält keinen timezone-aware Timestamp."
            )

        if candle.timestamp.utcoffset() is None:
            raise ValueError(
                f"Element {index} enthält keinen gültigen timezone-aware Timestamp."
            )

        if candle.timestamp.utcoffset() != timezone.utc.utcoffset(candle.timestamp):
            raise ValueError(
                f"Element {index} verwendet nicht UTC."
            )

        if previous_timestamp is not None:
            if candle.timestamp < previous_timestamp:
                raise ValueError(
                    "Candles müssen chronologisch sortiert sein."
                )

            if candle.timestamp == previous_timestamp:
                raise ValueError(
                    "Doppelte Candle-Timestamps sind nicht erlaubt."
                )

        previous_timestamp = candle.timestamp
