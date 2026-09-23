from automation import candidate_validation_50_50_vol_budget as base
from automation.risk_layer_parameter_free_shock_guard_2026_09_23 import (
    CASES,
    RESEARCH_COUNT,
    TARGET_VOL,
    VOL_WINDOW,
    _consensus,
    _simulate_shock_guard,
)


def test_fixed_hypothesis_contract():
    assert VOL_WINDOW == 63
    assert TARGET_VOL == 0.10
    assert RESEARCH_COUNT == 2798
    assert len(CASES) == 4
    assert [case["artifact_id"] for case in CASES] == [
        10751817990,
        10740188093,
        10745697729,
        10753545703,
    ]


def test_shock_guard_matches_control_before_any_trailing_history_exists():
    rows = tuple(
        {
            "timestamp": i,
            "gross_open": 0.001,
            "gross_close": 0.001,
            "gross_adjusted_close": 0.001,
            "turnover": 0.01,
        }
        for i in range(10)
    )
    control = base._simulate(rows, 1.0, True, False)
    intervention = _simulate_shock_guard(rows)
    assert intervention[0]["scale"] == control[0]["scale"] == 1.0
    assert intervention[0]["one_day_shock_vol_estimate"] is None
    assert intervention[0]["effective_vol_estimate"] is None


def test_consensus_requires_timing_and_research_non_deterioration():
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
    result = _consensus(supported)
    assert result["decision_rule"].startswith(
        "supports_parameter_free_shock_guard_for_fifth_validation:"
    )

    tradeoff = {
        "validation_1": case(True, True, False, False),
        "validation_2": case(True, True, False, False),
        "validation_3": case(True, True, True, True),
        "validation_4": case(False, False, True, True),
    }
    result = _consensus(tradeoff)
    assert result["decision_rule"].startswith(
        "shock_guard_timing_improvement_with_research_tradeoff:"
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
    result = _consensus({f"validation_{i}": case for i in range(1, 5)})
    assert result["decision_rule"].startswith(
        "parameter_free_shock_guard_not_supported:"
    )
