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


def test_literature_policy_covers_free_public_source_classes_without_claiming_exhaustiveness():
    p = json.loads(Path("research/governance/literature_research_policy.json").read_text(encoding="utf-8"))
    scope = p["source_scope"]
    assert scope["free_access_only"] is True
    for required in (
        "open_access_peer_reviewed_literature",
        "public_blogs_essays_and_research_notes",
        "public_github_repositories_readmes_issues_and_pull_requests",
        "other_legally_accessible_public_web_sources",
    ):
        assert required in scope["include_classes"]
    assert scope["paywalled_only_sources_excluded"] is True
    assert "not a claim of exhaustive coverage" in scope["exhaustiveness"]
