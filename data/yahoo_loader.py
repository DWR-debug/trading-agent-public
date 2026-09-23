"""Yahoo Finance historical OHLCV loader.

Uses the public chart endpoint for historical market data.
No account credentials and no order functionality are involved.

The loader is intentionally limited to daily bars for the first stock
research expansion. Corporate-action events are requested for provenance,
while the executable OHLC prices remain split-adjusted market prices; dividend
cash flows are not modeled by the current Candle/BacktestTrade model.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from backtesting.models import Candle
from data.quality import validate_candles
from data.time_utils import is_candle_closed


BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
ALLOWED_INTERVALS = {"1d"}
MAX_REQUEST_ATTEMPTS = 4
DEFAULT_BACKOFF_SECONDS = 1.0
USER_AGENT = "trading-agent-research/1.0"


def _fetch_json(url: str) -> object:
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(1, MAX_REQUEST_ATTEMPTS + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if attempt == MAX_REQUEST_ATTEMPTS or exc.code not in {429, 500, 502, 503, 504}:
                raise
            time.sleep(DEFAULT_BACKOFF_SECONDS * (2 ** (attempt - 1)))
        except (urllib.error.URLError, TimeoutError):
            if attempt == MAX_REQUEST_ATTEMPTS:
                raise
            time.sleep(DEFAULT_BACKOFF_SECONDS * (2 ** (attempt - 1)))
    raise RuntimeError("Unerwarteter Yahoo-Request-Fehler.")


def _build_url(symbol: str, period1: int, period2: int, interval: str) -> str:
    params = {
        "period1": period1,
        "period2": period2,
        "interval": interval,
        "events": "div,splits",
        "includePrePost": "false",
    }
    encoded = urllib.parse.urlencode(params)
    return f"{BASE_URL}/{urllib.parse.quote(symbol, safe='')}?{encoded}"


def load_yahoo_history(
    symbol: str,
    interval: str = "1d",
    total: int = 2500,
    *,
    allow_partial: bool = False,
    skip_invalid_ohlc: bool = False,
    quality_report: dict[str, int] | None = None,
) -> list[Candle]:
    if not symbol:
        raise ValueError("Symbol darf nicht leer sein.")
    if interval not in ALLOWED_INTERVALS:
        raise ValueError(f"Nicht unterstütztes Yahoo-Intervall: {interval}")
    if total < 1:
        raise ValueError("total muss größer als 0 sein.")

    now = datetime.now(timezone.utc)
    period2 = int((now + timedelta(days=1)).timestamp())
    # Trading days are sparse relative to calendar days. Four calendar days
    # per requested bar gives sufficient history for the initial stock phase.
    period1 = int((now - timedelta(days=total * 4)).timestamp())

    try:
        payload = _fetch_json(_build_url(symbol, period1, period2, interval))
    except Exception as exc:
        raise ValueError(
            f"Yahoo-Daten konnten nicht geladen werden für {symbol}: {exc}"
        ) from exc

    try:
        result = payload["chart"]["result"][0]
        timestamps = result["timestamp"]
        quote = result["indicators"]["quote"][0]
        opens = quote["open"]
        highs = quote["high"]
        lows = quote["low"]
        closes = quote["close"]
        volumes = quote["volume"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Ungültige Yahoo-Antwort für {symbol}.") from exc

    if quality_report is not None:
        quality_report.setdefault("rows_seen", 0)
        quality_report.setdefault("rows_skipped_none", 0)
        quality_report.setdefault("rows_skipped_unclosed", 0)
        quality_report.setdefault("rows_skipped_invalid_ohlc", 0)

    candles = []
    for index, timestamp in enumerate(timestamps):
        if quality_report is not None:
            quality_report["rows_seen"] += 1
        values = (
            opens[index],
            highs[index],
            lows[index],
            closes[index],
            volumes[index],
        )
        if any(value is None for value in values):
            if quality_report is not None:
                quality_report["rows_skipped_none"] += 1
            continue

        candle_timestamp = datetime.fromtimestamp(
            int(timestamp), tz=timezone.utc
        )
        # Yahoo can include today's still-open daily bar. Exclude it before
        # constructing Candle so incomplete vendor data cannot trigger OHLC
        # validation errors before the completed-session filter runs.
        if not is_candle_closed(candle_timestamp, interval, now=now):
            if quality_report is not None:
                quality_report["rows_skipped_unclosed"] += 1
            continue

        open_price, high_price, low_price, close_price, volume = (
            float(values[0]),
            float(values[1]),
            float(values[2]),
            float(values[3]),
            float(values[4]),
        )
        valid_ohlc = (
            open_price > 0
            and high_price > 0
            and low_price > 0
            and close_price > 0
            and volume >= 0
            and high_price >= max(open_price, close_price)
            and low_price <= min(open_price, close_price)
            and low_price <= high_price
        )
        if not valid_ohlc and skip_invalid_ohlc:
            if quality_report is not None:
                quality_report["rows_skipped_invalid_ohlc"] += 1
            continue

        candles.append(
            Candle(
                timestamp=candle_timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )
        )

    candles.sort(key=lambda candle: candle.timestamp)
    candles = candles[-total:]

    if not candles:
        raise ValueError(f"Yahoo lieferte keine abgeschlossenen Candles für {symbol}.")
    if len(candles) != total and not allow_partial:
        raise ValueError(
            f"Yahoo lieferte nur {len(candles)} von {total} "
            f"angeforderten Candles für {symbol}."
        )

    validate_candles(candles)
    if quality_report is not None:
        quality_report["rows_returned"] = len(candles)
    return candles
