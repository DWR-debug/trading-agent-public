"""UTC- und Candle-Zeit-Helfer für Marktdaten."""

from datetime import datetime, timedelta, timezone


INTERVAL_DELTAS = {
    "1m": timedelta(minutes=1),
    "3m": timedelta(minutes=3),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "2h": timedelta(hours=2),
    "4h": timedelta(hours=4),
    "6h": timedelta(hours=6),
    "8h": timedelta(hours=8),
    "12h": timedelta(hours=12),
    "1d": timedelta(days=1),
}


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO timestamp and return a timezone-aware UTC datetime."""
    timestamp = datetime.fromisoformat(value.strip())

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return timestamp.replace(tzinfo=timezone.utc)

    return timestamp.astimezone(timezone.utc)


def interval_delta(interval: str) -> timedelta:
    """Return the expected candle duration for a supported interval."""
    try:
        return INTERVAL_DELTAS[interval]
    except KeyError as exc:
        raise ValueError(
            f"Nicht unterstütztes Intervall: {interval}"
        ) from exc


def is_candle_closed(
    timestamp: datetime,
    interval: str,
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether a candle has fully closed at the given UTC time."""
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Candle-Timestamp muss timezone-aware sein.")

    now = now or datetime.now(timezone.utc)

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now muss timezone-aware sein.")

    return (
        timestamp.astimezone(timezone.utc) + interval_delta(interval)
        <= now.astimezone(timezone.utc)
    )
