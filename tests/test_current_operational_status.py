import json

from automation.sync_current_operational_status import generate


def test_current_status_separates_operations_from_science(tmp_path):
    state = tmp_path / "github_state.json"
    state.write_text(
        json.dumps(
            {
                "open_prs": [{"number": 1, "title": "example"}],
                "agent_ready_issues": [{"number": 2, "title": "agent"}],
            }
        ),
        encoding="utf-8",
    )
    payload, doc = generate(
        source_master_sha="abc123",
        workflow_run_id="run-1",
        github_state_path=state,
    )
    assert payload["source_master_sha"] == "abc123"
    assert payload["repository_state"]["open_pull_requests"][0]["number"] == 1
    assert payload["repository_state"]["open_agent_ready_issues"][0]["number"] == 2
    assert payload["status_commit_is_documentation_only"] is True
    assert payload["scientific_state_recorded"]["latest_formal_status"]
    assert "canonical current operational status" in doc
    assert payload["safety"]["status"] == "SAFE"


def test_current_status_detects_safety_violation(monkeypatch, tmp_path):
    state = tmp_path / "github_state.json"
    state.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("config.settings.PAPER_ONLY", False)
    payload, _ = generate(
        source_master_sha="abc123",
        workflow_run_id=None,
        github_state_path=state,
    )
    assert payload["safety"]["status"] == "VIOLATION"
