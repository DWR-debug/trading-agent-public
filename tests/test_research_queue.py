import pytest

from research.research_queue import ResearchQueueError, default_research_queue


def test_queue_is_deterministic_and_tracks_current_priority():
    queue = default_research_queue()
    first = queue.next_task()
    assert first is not None
    assert first.task_id == "Q-009-T045-POSITION-LIFECYCLE-EXIT-CONTROL"
    task_by_id = {task.task_id: task for task in queue.all()}
    assert task_by_id["Q-007-T043-TSM-SIGNAL-CONSISTENCY"].status == "BLOCKED"
    assert task_by_id["Q-008-T044-TSM-SIGNAL-CONSISTENCY-REPAIR"].status == "PENDING"


def test_queue_rejects_invalid_transition():
    queue = default_research_queue()
    blocked = queue.all()[0]
    assert blocked.status == "BLOCKED"
    with pytest.raises(ResearchQueueError):
        queue.set_status(blocked.task_id, "COMPLETED")


def test_default_queue_has_unique_ids():
    queue = default_research_queue()
    ids = [item.task_id for item in queue.all()]
    assert len(ids) == len(set(ids))
