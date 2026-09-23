"""
Automatischer Marktdaten-Updater.

Lädt historische Binance-Candles und aktualisiert
den lokalen MarketDataStore.

Nur Marktdaten.
Keine API-Schlüssel.
Keine Orderausführung.
Kein Echtgeldhandel.
"""

from collections.abc import Callable
from dataclasses import dataclass

from backtesting.models import Candle
from data.binance_loader import load_binance_history
from data.market_store import MarketDataStore


CandleLoader = Callable[[str, str, int], list[Candle]]


@dataclass(frozen=True)
class UpdateResult:
    symbol: str
    interval: str
    previous_count: int
    fetched_count: int
    final_count: int
    path: str


def update_dataset(
    symbol: str,
    interval: str,
    target_count: int,
    *,
    store: MarketDataStore | None = None,
    loader: CandleLoader = load_binance_history,
    refresh_count: int = 1000,
) -> UpdateResult:
    if not symbol:
        raise ValueError("Symbol darf nicht leer sein.")

    if not interval:
        raise ValueError("Intervall darf nicht leer sein.")

    if target_count < 1:
        raise ValueError(
            "target_count muss mindestens 1 sein."
        )

    if refresh_count < 1:
        raise ValueError(
            "refresh_count muss mindestens 1 sein."
        )

    store = store or MarketDataStore()

    existing = store.load(symbol, interval)
    previous_count = len(existing)

    # Initialer Import: vollständige Zielmenge laden.
    # Bestehender Datensatz: nur den aktuellen Bereich auffrischen.
    fetch_count = (
        target_count
        if not existing
        else min(target_count, refresh_count)
    )

    fetched = loader(
        symbol,
        interval,
        fetch_count,
    )

    merged = store.merge(
        symbol,
        interval,
        fetched,
        target_count=target_count,
    )

    path = store.save(
        symbol,
        interval,
        merged,
    )

    return UpdateResult(
        symbol=symbol.upper(),
        interval=interval,
        previous_count=previous_count,
        fetched_count=len(fetched),
        final_count=len(merged),
        path=str(path),
    )


def update_all(
    datasets: list[tuple[str, str, int]],
    *,
    store: MarketDataStore | None = None,
    loader: CandleLoader = load_binance_history,
    refresh_count: int = 1000,
) -> list[UpdateResult]:
    if not datasets:
        raise ValueError(
            "Mindestens ein Datensatz muss angegeben werden."
        )

    store = store or MarketDataStore()

    results = []

    for symbol, interval, target_count in datasets:
        results.append(
            update_dataset(
                symbol,
                interval,
                target_count,
                store=store,
                loader=loader,
                refresh_count=refresh_count,
            )
        )

    return results


if __name__ == "__main__":
    datasets = [
        ("BTCUSDT", "1h", 10000),
        ("BTCUSDT", "15m", 10000),
        ("ETHUSDT", "1h", 10000),
        ("ETHUSDT", "15m", 10000),
    ]

    results = update_all(datasets)

    for result in results:
        print(
            f"{result.symbol} {result.interval}: "
            f"{result.previous_count} -> "
            f"{result.final_count} Candles | "
            f"geladen: {result.fetched_count} | "
            f"{result.path}"
        )
