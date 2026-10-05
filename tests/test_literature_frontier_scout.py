import json
from pathlib import Path


def test_literature_policy_is_active_and_bounded():
    p = json.loads(Path("research/governance/literature_research_policy.json").read_text(encoding="utf-8"))
    assert p["status"] == "ACTIVE"
    assert p["selection_rule"]["shortlist_maximum"] <= 4
    boundary = p["discovery_boundary"]
    assert boundary["performance_authorized"] is False
    assert boundary["holdout_selection_allowed"] is False
    assert boundary["ranking_allowed"] is False
    assert boundary["parameter_search_allowed"] is False
    assert boundary["promotion_allowed"] is False
    assert boundary["live_execution_allowed"] is False


def test_literature_search_axes_are_distinct():
    axes = json.loads(Path("research/governance/literature_research_policy.json").read_text(encoding="utf-8"))["search_axes"]
    assert len(axes) == len(set(axes))
    assert len(axes) >= 8
