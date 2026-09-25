from datetime import date

from automation.information_alpha_temporal_stability import (
    DEFAULT_ASSETS,
    FIXED_FEATURES,
    run_stability_diagnostic,
)


def test_q012_fixed_panel_and_safety(tmp_path):
    prices = {}
    days = [date(2026, 8, day) for day in range(1, 25)]
    for symbol, base in zip(DEFAULT_ASSETS, (100.0, 200.0, 300.0)):
        prices[symbol] = {day: base + index for index, day in enumerate(days)}

    def market_loader(symbol, start, end):
        return prices[symbol]

    def event_loader(day):
        return []

    report = run_stability_diagnostic(
        date(2026, 8, 1),
        date(2026, 8, 24),
        output_dir=tmp_path / "q012",
    )

    assert report["status"] == "STABILITY_DIAGNOSTIC_ONLY"
    assert report["assets"] == list(DEFAULT_ASSETS)
    assert report["fixed_features"] == list(FIXED_FEATURES)
    assert report["selection_used"] is False
    assert report["holdout_used"] is False
    assert report["parameter_search_used"] is False
    assert report["feature_selection_used"] is False
    assert report["paper_only"] is True
    assert report["live_trading_enabled"] is False
    assert report["orders_enabled"] is False
    assert report["automatic_promotion"] is False
