from __future__ import annotations

from automation.future_performance_quality_contract_check import validate
from automation.research_os_scheduler import build_plan


def test_future_performance_contract_is_currently_clean():
    result = validate()
    assert result["status"] == "PASS"


def test_research_scheduler_selects_only_orthogonal_tracks():
    plan = build_plan(run_number=1)
    assert plan["quality_controls"]["orthogonal_only"] is True
    minimum = plan["quality_controls"]["minimum_scheduler_novelty_distance"]
    for assignment in plan["assignments"]:
        track = next(t for t in plan["tracks"] if t["id"] == assignment["track_id"])
        assert track["mechanism_novelty_distance"] >= minimum
    assert "holdout_return" in plan["forbidden_inputs"]
    assert "performance_rank" in plan["forbidden_inputs"]
    assert plan["resource_policy"]["performance_authorization"] is False
