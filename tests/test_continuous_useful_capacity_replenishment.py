from pathlib import Path


def test_useful_capacity_statute_is_non_negotiable() -> None:
    import json
    root = Path(__file__).parents[1]
    payload = json.loads(
        (root / "research/governance/persistent_research_acceleration_contract.json").read_text(encoding="utf-8")
    )
    rule = payload["useful_capacity_rule"]
    assert rule["status"] == "NON_NEGOTIABLE"
    assert "keine künstliche Arbeit" in rule["statement"]
    assert "wertvolle und hilfreiche Rechenarbeit" in rule["statement"]
    assert rule["no_padding"] is True
    assert rule["no_duplicate_work"] is True
    assert "completion chaining" in rule["operational_rule"]


def test_completion_replenisher_is_event_driven_and_fail_closed() -> None:
    root = Path(__file__).parents[1]
    text = (root / ".github/workflows/continuous-useful-capacity-replenisher.yml").read_text(encoding="utf-8")
    assert "workflow_run:" in text
    assert "Permanent Windows Local Research Loop" in text
    assert "types: [completed]" in text
    assert "actions: write" in text
    assert "github.event.workflow_run.conclusion" in text
    assert "gh workflow run permanent-pc-research-loop.yml" in text
    assert "Scientific boundary unchanged" in text


def test_dashboard_never_maps_unavailable_runner_inventory_to_zero() -> None:
    root = Path(__file__).parents[1]
    text = (root / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert '"runner_api_visible": len(runners) if runners else None' in text
    html = (root / "docs/dashboard/index.html").read_text(encoding="utf-8")
    assert '["Visible runners",s.runner_api_visible??"n/a"]' in html
