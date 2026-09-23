"""
CSV-Loader für historische OHLCV-Daten.

Nur Datenimport und Validierung.
Keine Netzwerkverbindung.
Keine Orderausführung.
Kein Echtgeldhandel.
"""

import csv
from pathlib import Path

from backtesting.models import Candle
from data.quality import validate_candles
from data.time_utils import parse_timestamp


REQUIRED_COLUMNS = {
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
}


def load_candles(path: str) -> list[Candle]:
    """
    Lädt historische OHLCV-Candles aus einer CSV-Datei.

    Erwartete Spalten:
    timestamp, open, high, low, close, volume

    Die Candles werden chronologisch sortiert
    und anschließend validiert.
    """

    file_path = Path(path)

    if not file_path.is_file():
        raise ValueError(f"CSV-Datei nicht gefunden: {path}")

    candles: list[Candle] = []

    with file_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("CSV enthält keinen Header.")

        columns = set(reader.fieldnames)

        if not REQUIRED_COLUMNS.issubset(columns):
            missing = REQUIRED_COLUMNS - columns
            raise ValueError(
                f"Fehlende CSV-Spalten: {sorted(missing)}"
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            try:
                timestamp = parse_timestamp(
                    row["timestamp"].strip()
                )

                candle = Candle(
                    timestamp=timestamp,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )

            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(
                    f"Ungültige Candle in Zeile "
                    f"{row_number}: {exc}"
                ) from exc

            candles.append(candle)

    if not candles:
        raise ValueError(
            "CSV enthält keine Candles."
        )

    candles.sort(
        key=lambda candle: candle.timestamp
    )

    validate_candles(candles)

    return candles
