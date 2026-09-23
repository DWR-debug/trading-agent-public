"""Research-spezifische Datenqualitäts-Gates für historische OHLCV-Daten."""

from collections.abc import Sequence
from datetime import datetime, timezone
import math

from backtesting.models import Candle
from data.quality import validate_candles
from data.time_utils import interval_delta, is_candle_closed


def validate_research_dataset(
    candles: Sequence[Candle],
    interval: str,
    *,
    expected_count: int | None = None,
    now: datetime | None = None,
    max_age_intervals: int = 3,
) -> None:
    """Validate a research dataset before it enters a manifest.

    Daily exchange data is calendar-sparse: weekends and exchange holidays
    legitimately produce gaps larger than one day. For daily data, gaps up to
    seven calendar days are accepted; longer gaps remain a quality failure.
    Intraday datasets retain the exact-interval requirement.
    """

    validate_candles(candles)

    if expected_count is not None and len(candles) != expected_count:
        raise ValueError(
            f"Falsche Candle-Anzahl: {len(candles)} statt "
            f"{expected_count}."
        )

    if max_age_intervals < 1:
        raise ValueError("max_age_intervals muss mindestens 1 sein.")

    delta = interval_delta(interval)
    now = now or datetime.now(timezone.utc)

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now muss timezone-aware sein.")

    now = now.astimezone(timezone.utc)
    tolerance = (
        delta * 7 if interval == "1d" else delta * max_age_intervals
    )

    for index, candle in enumerate(candles):
        if candle.timestamp > now:
            raise ValueError(
                f"Zukünftige Candle an Position {index}: "
                f"{candle.timestamp.isoformat()}."
            )

        if candle.high < max(candle.open, candle.close):
            raise ValueError(
                f"OHLC-Fehler an Position {index}: High ist zu klein."
            )

        if candle.low > min(candle.open, candle.close):
            raise ValueError(
                f"OHLC-Fehler an Position {index}: Low ist zu groß."
            )

        if candle.high < candle.low:
            raise ValueError(
                f"OHLC-Fehler an Position {index}: High < Low."
            )

        if candle.volume < 0 or not math.isfinite(candle.volume):
            raise ValueError(
                f"Ungültiges Volumen an Position {index}."
            )

        if index > 0:
            gap = candle.timestamp - candles[index - 1].timestamp
            if interval == "1d":
                if gap > delta * 7:
                    raise ValueError(
                        f"Zeitlücke an Position {index}: {gap}, "
                        "mehr als sieben Kalendertage."
                    )
            elif gap != delta:
                raise ValueError(
                    f"Zeitlücke an Position {index}: {gap}, "
                    f"erwartet {delta}."
                )

    last_timestamp = candles[-1].timestamp
    if not is_candle_closed(last_timestamp, interval, now=now):
        raise ValueError(
            f"Letzte Candle ist noch nicht abgeschlossen: "
            f"{last_timestamp.isoformat()}."
        )

    if now - last_timestamp > tolerance:
        raise ValueError(
            f"Datensatz ist zu alt: letzter Timestamp "
            f"{last_timestamp.isoformat()}, jetzt {now.isoformat()}."
        )
