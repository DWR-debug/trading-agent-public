"""
Öffentlicher Binance-Loader für historische OHLCV-Daten.

Verwendet den offiziellen Binance-Market-Data-Endpunkt.
429/418 und temporäre 5xx-Antworten werden mit Backoff behandelt.
Nur Marktdaten. Keine API-Schlüssel. Keine Orderausführung.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from backtesting.models import Candle
from data.quality import validate_candles
from data.time_utils import interval_delta, is_candle_closed


# Separater Market-Data-Endpunkt; kein Account/API-Key erforderlich.
BASE_URL = "https://data-api.binance.vision/api/v3/klines"

ALLOWED_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m", "1h",
    "2h", "4h", "6h", "8h", "12h", "1d",
}

RETRYABLE_STATUS_CODES = {418, 429, 500, 502, 503, 504}
MAX_REQUEST_ATTEMPTS = 4
DEFAULT_BACKOFF_SECONDS = 1.0


def _retry_after_seconds(error: urllib.error.HTTPError) -> float:
    value = error.headers.get("Retry-After")
    if value is None:
        return DEFAULT_BACKOFF_SECONDS
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return DEFAULT_BACKOFF_SECONDS


def _fetch_json(url: str) -> object:
    for attempt in range(1, MAX_REQUEST_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                return json.loads(
                    response.read().decode("utf-8")
                )
        except urllib.error.HTTPError as exc:
            if (
                exc.code not in RETRYABLE_STATUS_CODES
                or attempt == MAX_REQUEST_ATTEMPTS
            ):
                raise

            delay = (
                _retry_after_seconds(exc)
                if exc.code in {418, 429}
                else DEFAULT_BACKOFF_SECONDS * (2 ** (attempt - 1))
            )
            time.sleep(delay)
        except (
            urllib.error.URLError,
            TimeoutError,
        ):
            if attempt == MAX_REQUEST_ATTEMPTS:
                raise
            time.sleep(
                DEFAULT_BACKOFF_SECONDS * (2 ** (attempt - 1))
            )

    raise RuntimeError("Unerwarteter Request-Fehler.")


def _parse_candles(data: object) -> list[Candle]:
    if not isinstance(data, list):
        raise ValueError("Binance lieferte keine Kline-Liste.")

    candles = []

    for row_number, row in enumerate(data, start=1):
        if not isinstance(row, list) or len(row) < 6:
            raise ValueError(
                f"Ungültige Binance-Kline in Zeile {row_number}."
            )

        try:
            timestamp = datetime.fromtimestamp(
                int(row[0]) / 1000.0,
                tz=timezone.utc,
            )
            candles.append(
                Candle(
                    timestamp=timestamp,
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                )
            )
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError(
                f"Ungültige Binance-Kline in Zeile "
                f"{row_number}: {exc}"
            ) from exc

    if not candles:
        raise ValueError("Binance lieferte keine Candles.")

    validate_candles(candles)
    return candles


def _build_url(
    symbol: str,
    interval: str,
    limit: int,
    *,
    end_time: int | None = None,
) -> str:
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit,
    }
    if end_time is not None:
        params["endTime"] = end_time

    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


def load_binance_candles(
    symbol: str,
    interval: str,
    limit: int = 500,
) -> list[Candle]:
    if not symbol:
        raise ValueError("Symbol darf nicht leer sein.")
    if interval not in ALLOWED_INTERVALS:
        raise ValueError(
            f"Nicht unterstütztes Intervall: {interval}"
        )
    if not 1 <= limit <= 1000:
        raise ValueError(
            "Limit muss zwischen 1 und 1000 liegen."
        )

    try:
        data = _fetch_json(
            _build_url(symbol, interval, limit)
        )
    except Exception as exc:
        raise ValueError(
            f"Binance-Daten konnten nicht geladen werden: {exc}"
        ) from exc

    return _parse_candles(data)


def load_binance_history(
    symbol: str,
    interval: str,
    total: int,
) -> list[Candle]:
    if not symbol:
        raise ValueError("Symbol darf nicht leer sein.")
    if interval not in ALLOWED_INTERVALS:
        raise ValueError(
            f"Nicht unterstütztes Intervall: {interval}"
        )
    if total < 1:
        raise ValueError("Total muss größer als 0 sein.")

    candles = []
    end_time = None
    validation_now = datetime.now(timezone.utc)

    while len(candles) < total:
        batch_limit = min(
            1000,
            total - len(candles) + 1,
        )
        try:
            data = _fetch_json(
                _build_url(
                    symbol,
                    interval,
                    batch_limit,
                    end_time=end_time,
                )
            )
        except Exception as exc:
            raise ValueError(
                f"Binance-Daten konnten nicht geladen werden: {exc}"
            ) from exc

        batch = _parse_candles(data)
        candles.extend(
            candle
            for candle in batch
            if is_candle_closed(
                candle.timestamp,
                interval,
                now=validation_now,
            )
        )

        oldest_timestamp_ms = int(data[0][0])
        if oldest_timestamp_ms <= 0:
            break

        end_time = oldest_timestamp_ms - 1

        if len(batch) < batch_limit:
            break

    if not candles:
        raise ValueError("Binance lieferte keine Candles.")

    candles.sort(key=lambda candle: candle.timestamp)
    candles = candles[-total:]
    validate_candles(candles)

    if len(candles) != total:
        raise ValueError(
            f"Binance lieferte nur {len(candles)} "
            f"von {total} angeforderten Candles."
        )

    return candles
