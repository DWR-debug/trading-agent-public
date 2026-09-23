"""
Lokaler Marktdaten-Store.

Verwaltet validierte Candle-Daten als CSV.
Keine Orderausführung. Kein Echtgeldhandel.
"""

import csv
from pathlib import Path

from backtesting.models import Candle
from data.quality import validate_candles
from data.time_utils import is_candle_closed, parse_timestamp


CSV_COLUMNS = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class MarketDataStore:
    def __init__(self, base_dir: str | Path = "data/market_data"):
        self.base_dir = Path(base_dir)

    def path_for(self, symbol: str, interval: str) -> Path:
        if not symbol:
            raise ValueError("Symbol darf nicht leer sein.")
        if not interval:
            raise ValueError("Intervall darf nicht leer sein.")

        return self.base_dir / symbol.upper() / f"{interval}.csv"

    def save(
        self,
        symbol: str,
        interval: str,
        candles: list[Candle] | tuple[Candle, ...],
    ) -> Path:
        if not candles:
            raise ValueError("Candles dürfen nicht leer sein.")

        validate_candles(candles)

        path = self.path_for(symbol, interval)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            writer.writeheader()

            for candle in candles:
                writer.writerow(
                    {
                        "timestamp": candle.timestamp.isoformat(),
                        "open": candle.open,
                        "high": candle.high,
                        "low": candle.low,
                        "close": candle.close,
                        "volume": candle.volume,
                    }
                )

        return path

    def load(
        self,
        symbol: str,
        interval: str,
    ) -> list[Candle]:
        path = self.path_for(symbol, interval)

        if not path.exists():
            return []

        candles: list[Candle] = []

        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)

            if tuple(reader.fieldnames or ()) != CSV_COLUMNS:
                raise ValueError(
                    "Ungültige Marktdaten-Spalten."
                )

            for row_number, row in enumerate(reader, start=2):
                try:
                    candles.append(
                        Candle(
                            timestamp=parse_timestamp(
                                row["timestamp"]
                            ),
                            open=float(row["open"]),
                            high=float(row["high"]),
                            low=float(row["low"]),
                            close=float(row["close"]),
                            volume=float(row["volume"]),
                        )
                    )
                except (ValueError, TypeError, KeyError) as exc:
                    raise ValueError(
                        f"Ungültige Marktdaten in Zeile "
                        f"{row_number}: {exc}"
                    ) from exc

        if not candles:
            raise ValueError(
                f"Marktdaten-Datei ist leer: {path}"
            )

        validate_candles(candles)
        return candles

    def merge(
        self,
        symbol: str,
        interval: str,
        candles: list[Candle] | tuple[Candle, ...],
        target_count: int | None = None,
    ) -> list[Candle]:
        if not candles:
            raise ValueError("Neue Candles dürfen nicht leer sein.")

        validate_candles(candles)

        existing = [
            candle
            for candle in self.load(symbol, interval)
            if is_candle_closed(candle.timestamp, interval)
        ]

        merged = {
            candle.timestamp: candle
            for candle in existing
        }

        for candle in candles:
            merged[candle.timestamp] = candle

        result = sorted(
            merged.values(),
            key=lambda candle: candle.timestamp,
        )

        if target_count is not None:
            if target_count < 1:
                raise ValueError(
                    "target_count muss mindestens 1 sein."
                )
            result = result[-target_count:]

        validate_candles(result)
        return result

    def merge_and_save(
        self,
        symbol: str,
        interval: str,
        candles: list[Candle] | tuple[Candle, ...],
        target_count: int | None = None,
    ) -> Path:
        merged = self.merge(
            symbol,
            interval,
            candles,
            target_count=target_count,
        )
        return self.save(symbol, interval, merged)
