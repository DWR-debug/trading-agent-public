import math

from automation.risk_layer_downside_volatility_2026_09_24 import (
    CASES,
    DOWNSIDE_THRESHOLD,
    RESEARCH_COUNT,
    TARGET_VOL,
    VOL_WINDOW,
    _consensus,
    _downside_vol,
)


def test_fixed_downside_volatility_contract():
    assert DOWNSIDE_THRESHOLD == 0.0
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


def test_downside_vol_uses_negative_returns_only_and_zero_threshold():
    history = [-0.01, 0.02, -0.02, 0.0]
    result = _downside_vol(history * 16, 63)
    sample = (history * 16)[-63:]
    expected = (
        math.sqrt(sum(value * value for value in sample if value < 0.0) / 63.0)
        * math.sqrt(252.0)
    )
    assert math.isclose(result, expected, rel_tol=0, abs_tol=1e-15)


def test_downside_vol_returns_zero_when_no_negative_returns_exist():
    history = [0.01] * 63
    assert _downside_vol(history, 63) == 0.0


def test_downside_vol_requires_full_warmup_window():
    assert _downside_vol([0.01] * 62, 63) is None


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
        "supports_downside_volatility_for_fifth_validation:"
    )

    tradeoff = {
        "validation_1": case(True, True, False, False),
        "validation_2": case(True, True, False, False),
        "validation_3": case(True, True, True, True),
        "validation_4": case(False, False, True, True),
    }
    assert _consensus(tradeoff)["decision_rule"].startswith(
        "downside_volatility_timing_improvement_with_research_tradeoff:"
    )
