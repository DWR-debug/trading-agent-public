"""Research asset universes and priority tiers.

The priority order is a research hypothesis about where higher volatility may
create more strategy opportunity. It is not a forecast of future returns.

Stock universes are deliberately separated from crypto and from each other so
that survivorship/liquidity/data-quality effects remain visible in reports.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetUniverse:
    name: str
    priority: int
    description: str
    symbols: tuple[str, ...]
    interval: str = "1d"
    target_count: int = 2500
    source: str = "yahoo_chart"


UNIVERSES: tuple[AssetUniverse, ...] = (
    AssetUniverse(
        name="small_cap_high_volatility",
        priority=1,
        description="Exploratory listed small/high-volatility growth names.",
        symbols=("SOUN", "RKLB", "IONQ", "ASTS", "HIMS"),
    ),
    AssetUniverse(
        name="liquid_high_volatility",
        priority=2,
        description="Liquid US equities with substantial historical movement.",
        symbols=("NVDA", "AMD", "TSLA", "COIN", "PLTR"),
    ),
    AssetUniverse(
        name="penny_stock",
        priority=3,
        description="Low-priced listed equities; price/liquidity filters remain mandatory.",
        symbols=("SNDL", "BNGO", "TLRY"),
    ),
    AssetUniverse(
        name="european_volatile",
        priority=4,
        description="European listed equities for cross-market robustness checks.",
        symbols=("RHM.DE", "TUI1.DE", "NEL.OL", "VOW3.DE"),
    ),
    AssetUniverse(
        name="benchmark",
        priority=5,
        description="Liquid benchmarks used as robustness/control datasets.",
        symbols=("SPY", "QQQ", "IWM"),
    ),
    AssetUniverse(
        name="cross_asset_trend",
        priority=6,
        description=(
            "Independent liquid ETF universe spanning equities, fixed income, "
            "commodities and currency exposure for trend-following replication."
        ),
        symbols=("SPY", "EFA", "TLT", "GLD", "DBC", "UUP", "QQQ", "IWM"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_trend",
        priority=7,
        description=(
            "Pre-registered independent ETF validation universe for the fixed trend sleeve; "
            "no symbol overlap with prior mechanism-replication universes."
        ),
        symbols=("DIA", "EEM", "LQD", "IEF", "VNQ", "USO", "FXE", "TIP"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_cs",
        priority=8,
        description=(
            "Pre-registered independent sector-ETF validation universe for the fixed "
            "cross-sectional momentum sleeve; no symbol overlap with prior universes."
        ),
        symbols=("XLK", "XLF", "XLE", "XLV", "XLI"),
        target_count=3500,
    ),
)


def get_universe(name: str) -> AssetUniverse:
    for universe in UNIVERSES:
        if universe.name == name:
            return universe
    available = ", ".join(item.name for item in UNIVERSES)
    raise ValueError(f"Unbekanntes Aktienuniversum: {name}. Verfügbar: {available}")


def list_universes() -> tuple[AssetUniverse, ...]:
    return UNIVERSES


def datasets_for(name: str) -> tuple[tuple[str, str, int], ...]:
    universe = get_universe(name)
    return tuple(
        (symbol, universe.interval, universe.target_count)
        for symbol in universe.symbols
    )
