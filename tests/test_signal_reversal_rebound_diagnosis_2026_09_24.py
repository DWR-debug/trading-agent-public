from datetime import datetime, timedelta, timezone

from automation.signal_reversal_rebound_diagnosis_2026_09_24 import (
    CASES,
    PRIOR_DECLINE_SESSIONS,
    RESEARCH_COUNT,
    WORST_DAY_BUCKET_PERCENT,
    _consensus,
    _prior_close_return,
    _summary,
)


def test_fixed_diagnostic_contract():
    assert len(CASES) == 4
    assert RESEARCH_COUNT == 2798
    assert PRIOR_DECLINE_SESSIONS == 20
    assert WORST_DAY_BUCKET_PERCENT == 5
    assert [case["artifact_id"] for case in CASES] == [
        10751817990,
        10740188093,
        10745697729,
        10753545703,
    ]


def test_prior_close_return_is_equal_weighted_and_lookback_fixed():
    class Bar:
        def __init__(self, close):
            self.close = close

    assets = {
        "AAA": tuple(Bar(100 + i) for i in range(25)),
        "BBB": tuple(Bar(200 + 2 * i) for i in range(25)),
    }
    result = _prior_close_return(assets, 20, 20)
    expected = (
        ((120 / 100) - 1.0)
        + ((240 / 200) - 1.0)
    ) / 2.0
    assert abs(result - expected) < 1e-15


def test_summary_marks_worst_bucket_and_state_difference():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(20):
        value = -0.10 if i < 1 else 0.01
        rows.append(
            {
                "timestamp": start + timedelta(days=i),
                "portfolio_net_return": value,
                "state": i == 0,
            }
        )

    result = _summary(rows, "state")
    assert result["observations"] == 1
    assert result["worst_5pct_observations"] == 1
    assert result["worst_5pct_enrichment_ratio"] == 20.0
    assert result["mean_difference_state_minus_non_state"] < 0.0


def test_consensus_requires_three_of_four_for_replication():
    def case(rebound=False, reversal=False, combined=False):
        return {
            "case_flags": {
                "rebound_enriched": rebound,
                "cs_reversal_enriched": reversal,
                "combined_enriched": combined,
            }
        }

    cases = {
        "validation_1": case(rebound=True),
        "validation_2": case(rebound=True),
        "validation_3": case(rebound=True),
        "validation_4": case(),
    }
    result = _consensus(cases)
    assert result["replication_counts"]["rebound_enriched"] == 3
    assert result["interpretation"] == "rebound_state_replicated"


def test_consensus_is_inconclusive_below_replication_threshold():
    cases = {
        "validation_1": {
            "case_flags": {
                "rebound_enriched": True,
                "cs_reversal_enriched": False,
                "combined_enriched": False,
            }
        },
        "validation_2": {
            "case_flags": {
                "rebound_enriched": True,
                "cs_reversal_enriched": False,
                "combined_enriched": False,
            }
        },
        "validation_3": {
            "case_flags": {
                "rebound_enriched": False,
                "cs_reversal_enriched": False,
                "combined_enriched": False,
            }
        },
        "validation_4": {
            "case_flags": {
                "rebound_enriched": False,
                "cs_reversal_enriched": False,
                "combined_enriched": False,
            }
        },
    }
    assert _consensus(cases)["interpretation"] == (
        "no_replicated_reversal_rebound_state"
    )
