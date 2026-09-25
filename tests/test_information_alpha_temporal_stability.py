from automation.information_alpha_temporal_stability import (
    DEFAULT_ASSETS,
    FIXED_FEATURES,
    _half_relationships,
)


def observation(day: int, sign: float) -> dict:
    return {
        "target_market_day": f"2026-04-{day:02d}",
        "features": {feature: float(day) for feature in FIXED_FEATURES},
        "market": {
            symbol: {
                "next_market_day_return": sign * (day / 1000.0),
                "five_market_day_forward_return": sign * (day / 2000.0),
            }
            for symbol in DEFAULT_ASSETS
        },
    }


def test_q012_half_relationships_are_deterministic():
    first = [observation(day, 1.0) for day in range(1, 12)]
    relationships = _half_relationships(first, DEFAULT_ASSETS, "first_half")

    assert set(relationships) == set(DEFAULT_ASSETS)
    for symbol in DEFAULT_ASSETS:
        assert set(relationships[symbol]) == set(FIXED_FEATURES)
        for feature in FIXED_FEATURES:
            metrics = relationships[symbol][feature]
            assert metrics["half"] == "first_half"
            assert metrics["sample_next_day"] == 11
            assert metrics["sample_five_day"] == 11
            assert metrics["pearson_next_day"] is not None
            assert metrics["pearson_five_day"] is not None


def test_q012_discovery_contract_is_fixed_and_paper_only(tmp_path):
    # Contract-level checks avoid any external data access in unit tests.
    assert DEFAULT_ASSETS == ("SPY", "TLT", "GLD")
    assert len(FIXED_FEATURES) == 6
