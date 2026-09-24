from research.research_queue import default_research_queue


def test_default_queue_tracks_current_t039_priority():
    queue = default_research_queue()
    task = queue.next_task()
    assert task is not None
    assert task.task_id == "Q-001-T039-NETWORK-MOMENTUM"
    assert task.research_family == "cross_asset_network_momentum"


def test_default_queue_has_unique_ids():
    queue = default_research_queue()
    ids = [item.task_id for item in queue.all()]
    assert len(ids) == len(set(ids))
