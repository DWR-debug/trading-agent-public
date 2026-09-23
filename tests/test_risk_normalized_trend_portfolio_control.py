from automation.risk_normalized_trend_portfolio_control import (
    ASSETS,
    STRATEGIES,
    _target_weights,
    _stats,
)


def test_uses_fixed_assets_and_strategy_families():
    assert ASSETS == ("SPY", "QQQ", "IWM")
    assert STRATEGIES == (
        "buy_and_hold",
        "tsm_ensemble_risk_normalized",
        "sma_50_200_risk_normalized",
        "blend_tsm_sma_risk_normalized",
    )


def test_risk_weights_normalize_active_assets_to_one_gross():
    assets = {
        symbol: [object()]
        for symbol in ASSETS
    }
    signals = {
        "SPY": [1],
        "QQQ": [-1],
        "IWM": [0],
    }

    # Inject the ATR function through simple monkeypatch-style replacement
    import automation.risk_normalized_trend_portfolio_control as module

    original = module.atr_percent_series
    module.atr_percent_series = lambda bars: [0.02]

    try:
        weights = _target_weights(
            assets,
            signals,
            "tsm_ensemble_risk_normalized",
            0,
        )
    finally:
        module.atr_percent_series = original

    assert abs(weights["SPY"]) == 0.5
    assert abs(weights["QQQ"]) == 0.5
    assert weights["IWM"] == 0.0
    assert sum(abs(value) for value in weights.values()) == 1.0


def test_risk_weights_respect_direction():
    assets = {symbol: [object()] for symbol in ASSETS}
    signals = {symbol: [1] for symbol in ASSETS}

    import automation.risk_normalized_trend_portfolio_control as module

    original = module.atr_percent_series
    module.atr_percent_series = lambda bars: [0.01]

    try:
        weights = _target_weights(
            assets,
            signals,
            "sma_50_200_risk_normalized",
            0,
        )
    finally:
        module.atr_percent_series = original

    assert all(value > 0 for value in weights.values())
    assert sum(abs(value) for value in weights.values()) == 1.0


def test_stats_is_empty_safe():
    result = _stats([], 0, 10)
    assert result["day_count"] == 0
    assert result["period_return"] == 0.0
    assert result["profit_factor"] == 0.0
