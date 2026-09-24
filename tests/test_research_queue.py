import pytest

from research.research_queue import ResearchQueueError, default_research_queue


def test_queue_is_deterministic_and_tracks_current_t039_priority():
    queue = default_research_queue()
    first = queue.next_task()
    assert first is not None
    assert first.task_id == "Q-001-T039-NETWORK-MOMENTUM"
    queue.set_status(first.task_id, "RUNNING")
    queue.set_status(first.task_id, "COMPLETED")
    assert queue.next_task().task_id == "Q-002-LIVE-DISCOVERY"


def test_queue_rejects_invalid_transition():
    queue = default_research_queue()
    with pytest.raises(ResearchQueueError):
        queue.set_status("Q-001-T039-NETWORK-MOMENTUM", "COMPLETED")


def test_default_queue_has_unique_ids():
    queue = default_research_queue()
    ids = [item.task_id for item in queue.all()]
    assert len(ids) == len(set(ids))
