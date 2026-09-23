from automation import candidate_validation_50_50_vol_budget as base
from automation.risk_layer_window_31_vs_63_2026_09_23 import (
    CASES,
    RESEARCH_COUNT,
    WINDOW_A,
    WINDOW_B,
    _consensus,
    _simulate_with_window,
)


def test_fixed_hypothesis_contract():
    assert WINDOW_A == 31
    assert WINDOW_B == 63
    assert RESEARCH_COUNT == 2798
    assert [case["artifact_id"] for case in CASES] == [
        10751817990,
        10740188093,
        10745697729,
        10753545703,
    ]


def test_63_session_simulation_is_row_for_row_parity_with_existing_control():
    rows = tuple(
        {
            "timestamp": index,
            "gross_open": ((index % 7) - 3) / 1000,
            "gross_close": ((index % 5) - 2) / 1000,
            "gross_adjusted_close": ((index % 5) - 2) / 1000,
            "turnover": 0.01 + (index % 3) / 100,
        }
        for index in range(90)
    )
    reference = base._simulate(rows, 1.0, True, False)
    replica = _simulate_with_window(rows, 63)
    assert [
        (x["timestamp"], x["scale"], x["net_return"], x["realized_vol_estimate"])
        for x in reference
    ] == [
        (x["timestamp"], x["scale"], x["net_return"], x["realized_vol_estimate"])
        for x in replica
    ]


def test_consensus_requires_both_timing_and_non_deterioration_for_support():
    def case(timing_delay, timing_onset, dd_ok, pf_ok):
        return {
            "comparison": {
                "rapid_delayed_rate_improved": timing_delay,
                "rapid_onset_active_rate_improved": timing_onset,
                "research_drawdown_non_deteriorated": dd_ok,
                "rolling_pf_non_deteriorated": pf_ok,
            }
        }

    good = {
        f"validation_{i}": case(True, True, True, True)
        for i in range(1, 5)
    }
    result = _consensus(good)
    assert result["decision_rule"].startswith("supports_31_session_risk_window_for_fifth_validation:")

    tradeoff = {
        "validation_1": case(True, True, False, False),
        "validation_2": case(True, True, False, False),
        "validation_3": case(True, True, True, True),
        "validation_4": case(False, False, True, True),
    }
    result = _consensus(tradeoff)
    assert result["decision_rule"].startswith("timing_improvement_with_research_tradeoff:")
