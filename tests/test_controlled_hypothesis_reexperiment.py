from automation.controlled_hypothesis_reexperiment import (
    FIXED,
    SAFETY,
    WINDOW_10_SIGNATURE,
    candidate_from_dict,
    counterfactual,
    parameter_diff,
    validate_source,
)


def candidate(window=10):
    return {
        "risk_per_trade": 0.0025,
        "leverage": 1.0,
        "strategy": {
            "momentum": {"lookback": 3},
            "mean_reversion": {"window": window, "threshold": 0.01},
        },
    }


def test_counterfactual_changes_only_window():
    base = candidate(10)
    changed = counterfactual(base)
    assert parameter_diff(base, changed) == ["mean_reversion.window"]
    assert changed["strategy"]["mean_reversion"]["window"] == 5
    assert changed["strategy"]["momentum"]["lookback"] == 3
    assert changed["strategy"]["mean_reversion"]["threshold"] == 0.01
    assert changed["risk_per_trade"] == 0.0025
    assert changed["leverage"] == 1.0


def test_counterfactual_is_bidirectional():
    changed = counterfactual(candidate(5))
    assert parameter_diff(candidate(5), changed) == ["mean_reversion.window"]
    assert changed["strategy"]["mean_reversion"]["window"] == 10


def test_candidate_fixture_matches_predeclared_signature_contract():
    assert candidate_from_dict(candidate())["risk_per_trade"] == FIXED["risk_per_trade"]


def test_source_validation_is_fail_closed():
    rolling = {
        "diagnostic_type": "rolling_geometry_time_phase_control",
        "universe": "benchmark",
        "target_count": 5000,
        "research_candle_count": 4500,
        "safety": SAFETY,
    }
    manifest = {
        "universe": "benchmark",
        "target_count": 5000,
        "safety": SAFETY,
        "datasets": [
            {"symbol": "IWM", "fingerprint": "bad"},
        ],
    }
    try:
        validate_source(rolling, manifest)
    except ValueError as exc:
        assert "fingerprints" in str(exc)
    else:
        raise AssertionError("source validation must reject mismatched data")


def test_expected_window_signature_is_pinned():
    assert len(WINDOW_10_SIGNATURE) == 64
