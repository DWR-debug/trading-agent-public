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
    AssetUniverse(
        name="validation_2026_09_23_trend",
        priority=9,
        description=(
            "Second fully disjoint ETF validation universe for the fixed trend sleeve; "
            "symbols are pre-registered before data acquisition and intentionally avoid "
            "all prior research universes."
        ),
        symbols=("VTI", "VEA", "VTV", "VUG", "XLB", "XLP", "XLU", "XLY"),
        target_count=3500,
    ),

    AssetUniverse(
        name="validation_2026_09_23_cs",
        priority=10,
        description=(
            "Second fully disjoint sector/industry ETF validation universe for the fixed "
            "cross-sectional momentum sleeve; symbols are pre-registered before data "
            "acquisition and intentionally avoid all prior research universes."
        ),
        symbols=("XBI", "KRE", "XME", "XOP", "XRT"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_23_third_trend",
        priority=11,
        description=(
            "Third fully disjoint ETF validation universe for the fixed trend sleeve; "
            "symbols are pre-registered before data acquisition and avoid all prior "
            "research universes."
        ),
        symbols=("MDY", "IJH", "EWA", "EWJ", "EWG", "BND", "SHY", "HYG"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_23_third_cs",
        priority=12,
        description=(
            "Third fully disjoint ETF validation universe for the fixed cross-sectional "
            "sleeve; symbols are pre-registered before data acquisition and avoid all "
            "prior research universes."
        ),
        symbols=("IYR", "IYT", "KIE", "IHF", "IWC"),
        target_count=3500,
    ),

    AssetUniverse(
        name="validation_2026_09_23_fourth_trend",
        priority=13,
        description=(
            "Fourth fully disjoint ETF validation universe for the fixed trend sleeve; "
            "symbols are pre-registered before data acquisition and avoid all prior "
            "research universes."
        ),
        symbols=("SCHB", "VO", "VB", "VXF", "VXUS", "VGK", "IAU", "AGG"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_23_fourth_cs",
        priority=14,
        description=(
            "Fourth fully disjoint ETF validation universe for the fixed "
            "cross-sectional sleeve; symbols are pre-registered before data acquisition "
            "and avoid all prior research universes."
        ),
        symbols=("KBE", "KCE", "IYZ", "IHI", "XHB"),
        target_count=3500,
    ),


    AssetUniverse(
        name="validation_2026_09_24_fourteenth_leverage",
        priority=18,
        description=(
            "Fourteenth fully symbol-disjoint US-listed ETF universe for "
            "pre-registered long/short and leverage research."
        ),
        symbols=("VOO", "VT", "VWO", "VEU", "IWD", "IWF", "IWN", "IWO"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_fifteenth_mean_reversion",
        priority=19,
        description=(
            "Fifteenth fully symbol-disjoint validation universe for a fixed "
            "long-only short-horizon mean-reversion control."
        ),
        symbols=("EWC", "EWH", "EWI", "EWK", "EWN", "EWP", "EWY", "EWT"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_sixteenth_cross_asset_cs",
        priority=20,
        description=(
            "Sixteenth fully symbol-disjoint validation universe spanning "
            "commodities, currencies and fixed income for 12-1 cross-sectional momentum."
        ),
        symbols=("DBA", "DBB", "FXA", "FXY", "MUB", "SHV", "EMB", "BWX"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_seventh_trend",
        priority=21,
        description=(
            "Seventh fully disjoint US-listed ETF validation universe for "
            "trend-family and multi-strategy complementarity research."
        ),
        symbols=("SLV", "RSP", "VYM", "VIG", "DVY", "EPP", "EWU", "EWZ"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_seventh_cs",
        priority=22,
        description=(
            "Seventh fully disjoint large-cap equity universe for "
            "cross-sectional momentum and multi-strategy complementarity research."
        ),
        symbols=("AAPL", "MSFT", "AMZN", "META", "GOOGL"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_portfolio_risk_parity_trend",
        priority=30,
        description=(
            "Fixed fully symbol-disjoint U.S. stock universe used by the "
            "pre-registered Trial 022 portfolio risk-parity control."
        ),
        symbols=("IBM", "GE", "CAT", "MMM", "HD", "LOW", "UNP", "NKE"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_portfolio_risk_parity_cs",
        priority=31,
        description=(
            "Fixed fully symbol-disjoint U.S. stock universe used by the "
            "pre-registered Trial 022 cross-sectional momentum sleeve control."
        ),
        symbols=("BAC", "JPM", "GS", "MS", "C"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_low_volatility_us_stocks",
        priority=33,
        description=(
            "Fixed fully symbol-disjoint U.S. stock universe used by the "
            "archived pre-registered monthly low-volatility control."
        ),
        symbols=("INTC", "QCOM", "AVGO", "HON", "LMT", "RTX", "CSX", "NSC"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_idio_volatility_us_stocks",
        priority=34,
        description=(
            "Fixed fully symbol-disjoint U.S. stock universe for the "
            "pre-registered Trial 025 market-residual-volatility control."
        ),
        symbols=("COST", "TMO", "LIN", "DE", "EMR", "SBUX", "VZ", "MA"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_common_market_momentum_gate",
        priority=35,
        description=(
            "Fully symbol-disjoint validation universe for Trial 026; thirteen traded "
            "assets plus one external ACWI common-market signal proxy."
        ),
        symbols=("VBR", "VSS", "VCIT", "BIL", "GSG", "VPL", "EWQ", "EWL", "EWW", "EZU", "ILF", "SCHD", "USMV", "ACWI"),
        target_count=3500,
    ),

    AssetUniverse(
        name="validation_2026_09_24_tsm_ensemble_candidate",
        priority=36,
        description=(
            "Fully symbol-disjoint validation universe for Trial 027; fixed long-only "
            "TSM ensemble trend-sleeve replacement."
        ),
        symbols=("IVV","ITOT","SCHX","SCHF","SPAB","IEI","MBB","VCSH","IYJ","IYC","IYM","IYK","IYW"),
        target_count=3500,
    ),


    AssetUniverse(
        name="validation_2026_09_24_per_sleeve_vol_budget",
        priority=37,
        description=(
            "Fully symbol-disjoint validation universe for Trial 028; per-sleeve "
            "volatility-budget risk reexperiment."
        ),
        symbols=("SPLV","SPHQ","SPYG","SPYV","FXI","GDX","PFF","CWB","XSD","IBB","ITA","XAR","XES"),
        target_count=3500,
    ),

    AssetUniverse(
        name="validation_2026_09_24_sleeve_volatility_parity_confirmation",
        priority=39,
        description=(
            "Fully symbol-disjoint confirmation universe for Trial 030; fixed monthly "
            "inverse-volatility parity between unchanged Trend and Cross-Sectional sleeves."
        ),
        symbols=("VV","VHT","VFH","VIS","VAW","VDE","VPU","VGT","SPDW","SPMB","SPEM","SPTL","SPIP"),
        target_count=3500,
    ),

    AssetUniverse(
        name="validation_2026_09_24_risk_adjusted_momentum_candidate",
        priority=40,
        description=(
            "Coverage-only validation universe for Trial 031; fixed cross-sectional "
            "risk-adjusted momentum candidate with formation-period volatility."
        ),
        symbols=("EIS","EPU","ECH","EWS","EWM","EZA","TUR","THD","VDC","VCR","VOX","IAT","XTN"),
        target_count=3500,
    ),

    AssetUniverse(
        name="validation_2026_09_24_relative_value_etf_pairs_v3",
        priority=47,
        description=(
            "Coverage-only validation universe for Trial 034; five fixed ex ante "
            "economic ETF relative-value pairs with long-history emerging-markets proxy."
        ),
        symbols=("VTWO","IJR","QQEW","ONEQ","EEMV","SCHE","IGIB","SPIB","SCHP","STIP"),
        target_count=3500,
    ),

    AssetUniverse(
        name="validation_2026_09_24_trend_family_wfo_candidate",
        priority=50,
        description=(
            "Coverage-only validation universe for Trial 035; ten fully symbol-disjoint "
            "multi-asset instruments for family-level walk-forward selection."
        ),
        symbols=("SPTM","IWR","RWR","SCHZ","VGSH","VGLT","DJP","MOO","GCC","REM"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_network_momentum_t039",
        priority=51,
        description=(
            "Pre-registered fully symbol-disjoint validation universe for Trial 039; "
            "fixed cross-asset network-momentum challenger with COMT replaced by FTGC."
        ),
        symbols=(
            "EIRL", "ENZL", "NORW", "EDEN", "FXF", "FXC",
            "CEW", "EIDO", "SCHO", "MINT", "FTGC", "RWX",
        ),
        target_count=3520,
    ),

    AssetUniverse(
        name="validation_2026_09_24_network_momentum_t040",
        priority=52,
        description=(
            "Repair successor for Trial 039 with one fixed coverage replacement "
            "FTGC -> BIV; all other symbols and the Network Momentum mechanism remain unchanged."
        ),
        symbols=(
            "EIRL", "ENZL", "NORW", "EDEN", "FXF", "FXC",
            "CEW", "EIDO", "SCHO", "MINT", "BIV", "RWX",
        ),
        target_count=3520,
    ),

    AssetUniverse(
        name="validation_2026_09_24_portfolio_risk_control_trend",
        priority=53,
        description=(
            "Fresh fully symbol-disjoint ETF universe for Trial 041; fixed trend "
            "sleeve input for correlation-aware minimum-variance allocation."
        ),
        symbols=("VONE", "VONG", "VONV", "VOE", "VOT", "IWB", "IUSG", "IUSV"),
        target_count=3500,
    ),
    AssetUniverse(
        name="validation_2026_09_24_portfolio_risk_control_cs",
        priority=54,
        description=(
            "Fresh fully symbol-disjoint ETF universe for Trial 041; fixed "
            "cross-sectional momentum sleeve input for correlation-aware allocation."
        ),
        symbols=("IWS", "IWP", "IJS", "IJJ", "IJK"),
        target_count=3500,
    ),

    AssetUniverse(
        name="validation_2026_09_24_volatility_managed_tsm",
        priority=55,
        description=(
            "Fresh fully symbol-disjoint ETF universe for Trial 042; fixed "
            "long/short 252-day time-series momentum with de-risk-only inverse-variance scaling."
        ),
        symbols=("DLS", "DEM", "EES", "EWX", "HDV", "SPHD", "VOOG", "VOOV", "OEF", "IWV"),
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
