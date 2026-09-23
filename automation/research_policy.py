"""Policy for research-result writeback.

Writeback is permitted only for a completed research result that passed all
research gates and only to the dedicated autonomous-results branch.

No live trading.
"""


AUTONOMOUS_RESULTS_BRANCH = "research/autonomous-results"


def writeback_allowed(
    research_status: str,
    current_branch: str,
    *,
    target_branch: str = AUTONOMOUS_RESULTS_BRANCH,
) -> bool:
    """Return True only for a PASSED result on the dedicated target branch."""

    return (
        research_status == "PASSED"
        and current_branch == target_branch
        and target_branch == AUTONOMOUS_RESULTS_BRANCH
    )
