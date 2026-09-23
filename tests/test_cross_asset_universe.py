def test_cross_asset_trend_universe_is_registered():
    from research.asset_universes import get_universe

    universe = get_universe("cross_asset_trend")

    assert universe.target_count == 3500
    assert universe.interval == "1d"
    assert universe.source == "yahoo_chart"
    assert universe.symbols == (
        "SPY",
        "EFA",
        "TLT",
        "GLD",
        "DBC",
        "UUP",
        "QQQ",
        "IWM",
    )
