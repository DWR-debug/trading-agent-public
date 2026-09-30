from automation.q099_q081r4_failure_diagnosis import (
    EXPECTED_COMMON_FAILED_GATES,
    diagnose,
    load_result,
)
from pathlib import Path


RESULT = Path("research/evidence/q081r4_performance_result.json")


def test_q099_reproduces_common_failure_signature_without_selection() -> None:
    receipt = diagnose(load_result(RESULT))
    assert set(receipt["common_failure_signature"]["gates_failed_by_all_arms"]) == EXPECTED_COMMON_FAILED_GATES
    assert receipt["common_failure_signature"]["failed_gate_count"] == 4
    assert receipt["common_failure_signature"]["passed_gate_count"] == 9
    assert receipt["rolling_window_diagnosis"]["all_arms_share_worst_rolling_window"] is True
    assert receipt["rolling_window_diagnosis"]["shared_worst_window_index"] == 4


def test_q099_is_strictly_non_authorizing() -> None:
    receipt = diagnose(load_result(RESULT))
    governance = receipt["governance"]
    assert governance["performance_evaluation"] is False
    assert governance["holdout_evaluation"] is False
    assert governance["candidate_selection"] is False
    assert governance["candidate_ranking"] is False
    assert governance["performance_authorized"] is False
    assert governance["automatic_promotion"] is False
    assert governance["live_trading_enabled"] is False
    assert governance["orders_enabled"] is False
    assert governance["paper_only"] is True
