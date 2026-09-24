from automation.risk_layer_forward_horizon_profile_2026_09_24 import (
    CASES,
    HORIZONS,
    RESEARCH_COUNT,
    _aggregate_horizon_consensus,
    _state_horizon_stats,
)


def test_fixed_horizon_contract():
    assert RESEARCH_COUNT == 2798
    assert HORIZONS == (1, 5, 20, 60)
    assert len(CASES) == 4
    assert [case["artifact_id"] for case in CASES] == [
        10751817990,
        10740188093,
        10745697729,
        10753545703,
    ]


def test_horizon_stats_never_cross_research_boundary():
    rows = tuple(
        {
            "timestamp": i,
            "gross_open": 0.01,
            "gross_close": 0.0,
            "gross_adjusted_close": 0.0,
            "turnover": 0.0,
        }
        for i in range(12)
    )
    simulated = [
        {
            "scale": 0.5 if i % 2 == 0 else 1.0,
            "net_return": 0.0,
            "gross_return": 0.0,
        }
        for i in range(12)
    ]

    import automation.risk_layer_forward_horizon_profile_2026_09_24 as mod

    old_count = mod.RESEARCH_COUNT
    try:
        mod.RESEARCH_COUNT = 10
        result = _state_horizon_stats(rows, simulated, 5)
        assert result["eligible_state_observations"] == 5
        assert result["de_risk_observations"] + result["full_risk_observations"] == 5
    finally:
        mod.RESEARCH_COUNT = old_count


def test_horizon_consensus_counts_are_fixed_per_horizon():
    case_template = {
        "horizons": {
            "1": {"combined_relationship": "adverse"},
            "5": {"combined_relationship": "favorable"},
            "20": {"combined_relationship": "mixed_or_inconclusive"},
            "60": {"combined_relationship": "adverse"},
        }
    }
    cases = {f"validation_{i}": case_template for i in range(4)}
    result = _aggregate_horizon_consensus(cases)

    assert result["by_horizon"]["1"] == {
        "favorable": 0,
        "adverse": 4,
        "mixed_or_inconclusive": 0,
    }
    assert result["by_horizon"]["5"] == {
        "favorable": 4,
        "adverse": 0,
        "mixed_or_inconclusive": 0,
    }
    assert result["by_horizon"]["20"] == {
        "favorable": 0,
        "adverse": 0,
        "mixed_or_inconclusive": 4,
    }
    assert result["by_horizon"]["60"] == {
        "favorable": 0,
        "adverse": 4,
        "mixed_or_inconclusive": 0,
    }
