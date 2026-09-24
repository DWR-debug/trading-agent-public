import pytest
from research.strategy_lifecycle import LifecycleError, StrategyRecord, StrategyRegistry

def test_lifecycle_is_fail_closed_and_rejected_records_remain():
    registry = StrategyRegistry((StrategyRecord("s1", "trend"),))
    for status in ("RESEARCH", "WALK_FORWARD", "HOLDOUT", "REJECTED"):
        registry.transition("s1", status)
    assert registry.get("s1").status == "REJECTED"
    assert registry.graveyard()[0].strategy_id == "s1"

def test_invalid_promotion_is_rejected():
    registry = StrategyRegistry((StrategyRecord("s1", "trend"),))
    with pytest.raises(LifecycleError):
        registry.transition("s1", "PROMOTED")

def test_blocked_can_return_to_research():
    registry = StrategyRegistry((StrategyRecord("s1", "trend", status="RESEARCH"),))
    registry.transition("s1", "BLOCKED")
    registry.transition("s1", "RESEARCH")
    assert registry.get("s1").status == "RESEARCH"
