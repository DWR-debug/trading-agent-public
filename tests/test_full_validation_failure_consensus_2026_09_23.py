from automation.full_validation_failure_consensus_2026_09_23 import (
    EXPECTED_SHARED_FAILURES,
)


def test_expected_shared_failure_signature_is_fixed():
    assert EXPECTED_SHARED_FAILURES == {
        "research_drawdown",
        "rolling_profit_factor",
        "rolling_average_drawdown",
        "holdout_drawdown",
    }
