import math

from automation.risk_layer_ewma_094_2026_09_24 import (
    CASES,
    EWMA_LAMBDA,
    RESEARCH_COUNT,
    TARGET_VOL,
    WARMUP_WINDOW,
    _consensus,
    _simulate_ewma,
)


def test_fixed_hypothesis_contract():
    assert EWMA_LAMBDA == 0.94
    assert WARMUP_WINDOW == 63
    assert TARGET_VOL == 0.10
    assert RESEARCH_COUNT == 2798
    assert len(CASES) == 4
    assert [case["artifact_id"] for case in CASES] == [
        10751817990,
        10740188093,
        10745697729,
        10753545703,
    ]


def test_ewma_warmup_and_recurrence_contract():
    rows = tuple(
        {
            "timestamp": i,
            "gross_open": 0.01 if i == 2 else 0.0,
            "gross_close": 0.0,
            "gross_adjusted_close": 0.0,
            "turnover": 0.0,
        }
        for i in range(70)
    )
    result = _simulate_ewma(rows)
    assert all(row["ewma_realized_vol_estimate"] is None for row in result[:63])
    assert result[63]["ewma_realized_vol_estimate"] is not None

    expected_variance = 0.0
    for i in range(63):
        observed = 0.01 if i == 2 else 0.0
        if i == 0:
            expected_variance = observed * observed
        else:
            expected_variance = (
                EWMA_LAMBDA * expected_variance
                + (1.0 - EWMA_LAMBDA) * observed * observed
            )
    expected_vol = math.sqrt(expected_variance) * math.sqrt(252.0)
    assert math.isclose(
        result[63]["ewma_realized_vol_estimate"],
        expected_vol,
        rel_tol=0,
        abs_tol=1e-15,
    )


def test_consensus_requires_both_timing_and_research_non_deterioration():
    def case(delay, onset, dd_ok, pf_ok):
        return {
            "comparison": {
                "rapid_delayed_rate_improved": delay,
                "rapid_onset_active_rate_improved": onset,
                "research_drawdown_non_deteriorated": dd_ok,
                "rolling_pf_non_deteriorated": pf_ok,
            }
        }

    supported = {f"validation_{i}": case(True, True, True, True) for i in range(1, 5)}
    assert _consensus(supported)["decision_rule"].startswith(
        "supports_ewma_094_for_fifth_validation:"
    )

    tradeoff = {
        "validation_1": case(True, True, False, False),
        "validation_2": case(True, True, False, False),
        "validation_3": case(True, True, True, True),
        "validation_4": case(False, False, True, True),
    }
    assert _consensus(tradeoff)["decision_rule"].startswith(
        "ewma_094_timing_improvement_with_research_tradeoff:"
    )


def test_consensus_can_reject_without_timing_replication():
    case = {
        "comparison": {
            "rapid_delayed_rate_improved": False,
            "rapid_onset_active_rate_improved": False,
            "research_drawdown_non_deteriorated": True,
            "rolling_pf_non_deteriorated": True,
        }
    }
    assert _consensus({f"validation_{i}": case for i in range(1, 5)})[
        "decision_rule"
    ].startswith("ewma_094_not_supported:")
