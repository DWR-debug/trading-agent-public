from automation.fourset_portfolio_regime_sleeve_interaction_2026_09_23 import (
    CASES,
    RESEARCH_COUNT,
    WINDOW_COUNT,
    _case_consensus,
    _window_bounds,
)


def test_fourset_contract():
    assert RESEARCH_COUNT == 2798
    assert WINDOW_COUNT == 5
    assert len(CASES) == 4
    assert [case["artifact_id"] for case in CASES] == [
        10751817990,
        10740188093,
        10745697729,
        10753545703,
    ]
    assert _window_bounds() == (
        (0, 559),
        (559, 1118),
        (1118, 1677),
        (1677, 2236),
        (2236, 2798),
    )


def test_case_consensus_counts_negative_window_classes():
    windows = [
        {
            "portfolio_negative": True,
            "both_sleeves_negative": True,
            "failure_class": "joint_sleeve_weakness",
            "de_risk_fraction": 0.5,
            "sleeve_return_corr": 0.6,
        },
        {
            "portfolio_negative": True,
            "both_sleeves_negative": False,
            "failure_class": "trend_only_weakness",
            "de_risk_fraction": 0.7,
            "sleeve_return_corr": 0.2,
        },
        {
            "portfolio_negative": True,
            "both_sleeves_negative": False,
            "failure_class": "cross_sectional_only_weakness",
            "de_risk_fraction": 0.8,
            "sleeve_return_corr": 0.3,
        },
        {
            "portfolio_negative": False,
            "both_sleeves_negative": False,
            "failure_class": "no_sleeve_negative",
            "de_risk_fraction": 0.1,
            "sleeve_return_corr": 0.1,
        },
    ]
    result = _case_consensus(windows)
    assert result["negative_portfolio_windows"] == 3
    assert result["joint_sleeve_weakness_windows"] == 1
    assert result["trend_only_weakness_windows"] == 1
    assert result["cross_sectional_only_weakness_windows"] == 1
    assert result["joint_sleeve_weakness_rate"] == 1 / 3
