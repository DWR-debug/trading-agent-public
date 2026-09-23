from automation.portfolio_regime_interaction_diagnosis_2026_09_23 import (
    EXPECTED_SHARED_FAILURES,
    _fingerprint,
)


def test_shared_failure_signature_is_fixed():
    assert EXPECTED_SHARED_FAILURES == {
        "research_drawdown",
        "rolling_profit_factor",
        "rolling_average_drawdown",
        "holdout_drawdown",
    }


def test_fingerprint_is_deterministic():
    payload = {"b": 2, "a": 1}
    assert _fingerprint(payload) == _fingerprint({"a": 1, "b": 2})
