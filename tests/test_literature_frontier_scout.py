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

def test_scout_workflow_installs_pytest_before_invoking_it():
    workflow = Path(".github/workflows/literature-frontier-scout.yml").read_text(encoding="utf-8")
    install = workflow.index("python -m pip install --disable-pip-version-check pytest")
    invoke = workflow.index("python -m pytest -q tests/test_literature_frontier_scout.py")
    assert install < invoke

def test_scout_runs_after_its_workflow_or_policy_changes_on_master():
    workflow = Path(".github/workflows/literature-frontier-scout.yml").read_text(encoding="utf-8")
    assert 'branches: [master]' in workflow
    assert '".github/workflows/literature-frontier-scout.yml"' in workflow
    assert '"research/governance/literature_research_policy.json"' in workflow
    assert '"tests/test_literature_frontier_scout.py"' in workflow

def test_scout_defines_run_scoped_output_path_before_use():
    workflow = Path(".github/workflows/literature-frontier-scout.yml").read_text(encoding="utf-8")
    define = workflow.index('OUT="research/runs/literature_frontier/${GITHUB_RUN_ID}"')
    use = workflow.index('mkdir -p "$OUT"')
    assert define < use
