from automation.research_policy import writeback_allowed


def test_blocked_result_cannot_write_back():
    assert not writeback_allowed(
        "BLOCKED",
        "research/autonomous-results",
    )


def test_passed_result_cannot_write_to_wrong_branch():
    assert not writeback_allowed(
        "PASSED",
        "master",
    )


def test_passed_result_can_write_to_dedicated_branch():
    assert writeback_allowed(
        "PASSED",
        "research/autonomous-results",
    )


def test_blocked_result_cannot_write_to_wrong_branch():
    assert not writeback_allowed(
        "BLOCKED",
        "master",
    )


def test_alternate_target_branch_cannot_bypass_policy():
    assert not writeback_allowed(
        "PASSED",
        "research/autonomous-results",
        target_branch="master",
    )
