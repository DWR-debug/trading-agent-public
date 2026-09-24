from datetime import datetime, timezone

from automation.cs_reversal_severity_persistence_2026_09_24 import (
    CASES,
    CS_REBALANCE_SESSIONS,
    RESEARCH_COUNT,
    _run_summary,
    _state_summary,
)


def _row(index, reversal, spread, portfolio_return):
    return {
        "cs_winner_reversal": reversal,
        "cs_winner_loser_spread": spread,
        "portfolio_net_return": portfolio_return,
        "timestamp": datetime(
            2026, 1, 1 + index, tzinfo=timezone.utc
        ),
    }


def test_fixed_contract():
    assert len(CASES) == 4
    assert RESEARCH_COUNT == 2798
    assert CS_REBALANCE_SESSIONS == 21
    assert [case["artifact_id"] for case in CASES] == [
        10751817990,
        10740188093,
        10745697729,
        10753545703,
    ]


def test_state_summary_measures_fixed_severity_and_worst_day_enrichment():
    rows = [
        _row(0, True, -0.08, -0.04),
        _row(1, True, -0.04, -0.03),
        _row(2, False, 0.02, 0.01),
        _row(3, False, 0.03, 0.02),
        _row(4, False, 0.01, 0.03),
    ]
    result = _state_summary(rows)
    assert result["reversal_observations"] == 2
    assert result["mean_winner_loser_spread"] == -0.06
    assert result["mean_spread_difference_reversal_minus_non_reversal"] < 0.0
    assert result["worst_5pct_reversal_observations"] == 1
    assert result["worst_5pct_enrichment_ratio"] > 1.0


def test_run_summary_preserves_consecutive_episode_lengths():
    runs = [
        {
            "length_sessions": 2,
            "cumulative_winner_loser_spread": -0.10,
        },
        {
            "length_sessions": 1,
            "cumulative_winner_loser_spread": -0.03,
        },
        {
            "length_sessions": 2,
            "cumulative_winner_loser_spread": -0.08,
        },
    ]
    result = _run_summary(runs)
    assert result["run_count"] == 3
    assert result["mean_length_sessions"] == 5 / 3
    assert result["median_length_sessions"] == 2
    assert result["maximum_length_sessions"] == 2
    assert result["length_distribution"] == {1: 1, 2: 2}
    assert result["most_negative_cumulative_winner_loser_spread"] == -0.10
