from datetime import datetime, timedelta, timezone

from automation.cross_sectional_momentum_control import (
    ASSETS,
    REBALANCE_DAYS,
    SKIP,
    STRATEGIES,
    Bar,
    _score,
    target_weights,
)


def bars(closes):
    return tuple(
        Bar(
            timestamp=datetime(
                2020, 1, 1,
                tzinfo=timezone.utc,
            ) + timedelta(days=index),
            open=float(close),
            high=float(close) + 1.0,
            low=float(close) - 1.0,
            close=float(close),
            volume=1000.0,
        )
        for index, close in enumerate(closes)
    )


def test_asset_and_strategy_set_is_fixed():
    assert ASSETS == ("SOUN", "RKLB", "IONQ", "ASTS", "HIMS")
    assert STRATEGIES == (
        "cs_momentum_126_long_only_top2",
        "cs_momentum_252_long_only_top2",
        "cs_momentum_126_long_short_2x2",
        "cs_momentum_252_long_short_2x2",
        "equal_weight_buy_and_hold",
    )


def test_momentum_score_skips_the_recent_month():
    assets = {
        symbol: bars([100.0] * 252 + [110.0])
        for symbol in ASSETS
    }
    score = _score(assets, 252, 252)

    assert set(score) == set(ASSETS)
    assert all(value == 0.0 for value in score.values())
    assert SKIP == 21


def test_long_only_holds_exactly_top_two_winners():
    assets = {
        "SOUN": bars([100.0] * 252 + [150.0]),
        "RKLB": bars([100.0] * 252 + [140.0]),
        "IONQ": bars([100.0] * 252 + [130.0]),
        "ASTS": bars([100.0] * 252 + [120.0]),
        "HIMS": bars([100.0] * 252 + [110.0]),
    }
    weights = target_weights(
        assets,
        "cs_momentum_252_long_only_top2",
        252,
    )

    assert weights["SOUN"] == 0.5
    assert weights["RKLB"] == 0.5
    assert sum(weights.values()) == 1.0


def test_long_short_is_market_neutral_with_one_gross_unit():
    assets = {
        "SOUN": bars([100.0] * 252 + [150.0]),
        "RKLB": bars([100.0] * 252 + [140.0]),
        "IONQ": bars([100.0] * 252 + [130.0]),
        "ASTS": bars([100.0] * 252 + [120.0]),
        "HIMS": bars([100.0] * 252 + [110.0]),
    }
    weights = target_weights(
        assets,
        "cs_momentum_252_long_short_2x2",
        252,
    )

    assert abs(sum(weights.values())) < 1e-12
    assert sum(abs(value) for value in weights.values()) == 1.0
    assert weights["SOUN"] == 0.25
    assert weights["RKLB"] == 0.25
    assert weights["ASTS"] == -0.25
    assert weights["HIMS"] == -0.25


def test_rebalance_frequency_is_fixed():
    assert REBALANCE_DAYS == 21
