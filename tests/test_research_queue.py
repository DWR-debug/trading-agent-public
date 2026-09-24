import pytest

from research.research_queue import ResearchQueueError, default_research_queue


def test_queue_is_deterministic_and_fail_closed():
    queue = default_research_queue()
    first = queue.next_task()
    assert first is not None
    assert first.task_id == "Q-001-TRIAL-017"
    queue.set_status(first.task_id, "RUNNING")
    queue.set_status(first.task_id, "COMPLETED")
    assert queue.next_task().task_id == "Q-002-ADVERSARIAL"


def test_queue_rejects_invalid_transition():
    queue = default_research_queue()
    with pytest.raises(ResearchQueueError):
        queue.set_status("Q-001-TRIAL-017", "COMPLETED")
