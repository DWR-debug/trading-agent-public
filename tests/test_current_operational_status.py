import json

from automation.sync_current_operational_status import generate


def test_current_status_separates_operations_from_science(tmp_path, monkeypatch):
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
    monkeypatch.setattr(
        "automation.sync_current_operational_status._recent_commits",
        lambda limit=8: [{"sha": "abc123", "timestamp": "2026-09-28T00:00:00+00:00", "message": "test"}],
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
    assert payload["q067_execution_pipeline"]["family"] == "Q067"
    assert payload["q068_execution_pipeline"]["family"] == "Q068"
    assert payload["q070_execution_pipeline"]["family"] == "Q070"
    assert payload["q068_execution_pipeline"]["state"] == "RETIRED"
    assert "obsolete execution path retired; historical evidence preserved" in payload["q068_execution_pipeline"]["blocking_reasons"]
    assert "### Q068 execution pipeline" in doc
    assert "### Q070 execution pipeline" in doc
    assert "canonical current operational status" in doc
    assert payload["safety"]["status"] == "SAFE"


def test_current_status_detects_safety_violation(monkeypatch, tmp_path):
    state = tmp_path / "github_state.json"
    state.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("config.settings.PAPER_ONLY", False)
    monkeypatch.setattr(
        "automation.sync_current_operational_status._recent_commits",
        lambda limit=8: [],
    )
    payload, _ = generate(
        source_master_sha="abc123",
        workflow_run_id=None,
        github_state_path=state,
    )
    assert payload["safety"]["status"] == "VIOLATION"


def test_current_status_generator_advances_q081r4_focus_to_q100() -> None:
    source = __import__("pathlib").Path(
        "automation/sync_current_operational_status.py"
    ).read_text(encoding="utf-8")
    assert "Q100 frontier feasibility synthesis" in source
    assert "No performance authorization is " in source
    assert "created by these feasibility steps." in source


def test_current_status_renders_q197_q201_frontier() -> None:
    payload, doc = __import__("automation.sync_current_operational_status", fromlist=["generate"]).generate(
        source_master_sha="abc123",
        workflow_run_id=None,
        github_state_path=None,
    )
    assert "### Q197–Q201 Orthogonal Information Frontier" in doc
    assert "Q198" in doc
    assert "Q197" in doc
    assert "Q199" in doc
    assert "Q201" in doc
    frontier = payload["scientific_state_recorded"]["frontier_q197_q201"]
    assert frontier["Q201"]["stage"] == "SOURCE_COMPONENT_READY"
    assert frontier["Q198"]["stage"] == "SOURCE_COMPONENT_READY"
    assert frontier["performance_authorized"] is False


def test_current_status_renders_q202_q204_frontier() -> None:
    payload, doc = __import__("automation.sync_current_operational_status", fromlist=["generate"]).generate(
        source_master_sha="abc123",
        workflow_run_id=None,
        github_state_path=None,
    )
    assert "### Q202–Q204 Information-Timing Frontier" in doc
    assert "Q202" in doc
    assert "Q203" in doc
    assert "Q204" in doc
    frontier = payload["scientific_state_recorded"]["frontier_q202_q204"]
    assert frontier["Q202"]["stage"] == "SOURCE_COMPONENT_READY"
    assert frontier["Q203"]["stage"] == "SOURCE_COMPONENT_READY"
    assert frontier["Q204"]["stage"] == "SOURCE_COMPONENT_READY"
    assert frontier["performance_authorized"] is False
    assert frontier["pit_validated"] is False
