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

def test_current_status_reports_completed_q218_replication_and_open_primary_revalidation() -> None:
    from automation.sync_current_operational_status import generate

    payload, doc = generate(
        source_master_sha="abc123",
        workflow_run_id=None,
        github_state_path=None,
    )
    focus = payload["chat_handoff"]["next_research_focus"]
    assert "Q218 primary one-shot and pre-registered fresh-symbol replication both completed" in focus
    assert "8 event pairs across GOOGL/META/ORCL/PFE" in focus
    assert "primary trial current-context revalidation remains a separate open gate" in focus
    assert "bfed980b13d9640aece19d4ebb24ccf05b5ea4589772f64001eff29728f58bb7" in focus
    assert "no holdout selection, tuning, ranking, promotion or live execution is inferred" in focus
    assert "canonical current operational status" in doc

    assert "Active execution focus is locked to exactly three candidates: Q104:I19, Q220, and Q218." in focus
    assert "Q219 and Q221 remain reserve design/source tracks and are outside active automatic dispatch" in focus
    assert "Do not launch a duplicate full census while a useful run remains active." in focus
    assert "do not repeat the consumed primary one-shot" in focus
    assert focus.count("Q218 primary one-shot and pre-registered fresh-symbol replication both completed in PAPER_ONLY") == 1
    assert "Q220 previous population receipt is STALE" in focus
    assert "before starting the historical prefix/acceptance-time PIT compiler" in focus
    assert "transport-success/content-unusable" in focus
    assert "not a methods review or scientific evidence" in focus

def test_q220_population_focus_sentence_requires_a_positive_fingerprinted_receipt():
    import hashlib
    from pathlib import Path
    from automation.sync_current_operational_status import q220_population_focus_sentence

    root = Path(__file__).parents[1]

    positive = {
        "candidate_id": "Q220",
        "mode": "population",
        "status": "Q220_AS_FILED_XBRL_POPULATION_COMPLETED",
        "row_count": 55,
        "record_count": 55,
        "failure_count": 0,
        "receipt_fingerprint": "a" * 64,
        "gate_code_sha256": hashlib.sha256((root / "automation/q220_as_filed_xbrl_population_gate.py").read_bytes()).hexdigest(),
        "contract_sha256": hashlib.sha256((root / "research/preregistrations/q220_as_filed_xbrl_population_contract_2026_10_06.json").read_bytes()).hexdigest(),
    }
    rendered = q220_population_focus_sentence(positive)
    assert "population gate is positive" in rendered
    assert "55 filing records" in rendered
    assert "historical prefix/acceptance-time PIT representation-state compiler" in rendered
    assert "a" * 64 in rendered

    negative = dict(positive, status="Q220_AS_FILED_XBRL_POPULATION_BLOCKED")
    assert "Complete and reconcile the bounded fixed-population gate" in q220_population_focus_sentence(negative)
    negative = dict(positive, failure_count=1)
    assert "Complete and reconcile the bounded fixed-population gate" in q220_population_focus_sentence(negative)





def test_q220_hashless_legacy_population_receipt_is_not_a_positive_gate():
    from automation.sync_current_operational_status import q220_population_focus_sentence

    legacy = {
        "candidate_id": "Q220",
        "mode": "population",
        "status": "Q220_AS_FILED_XBRL_POPULATION_COMPLETED",
        "row_count": 55,
        "record_count": 55,
        "failure_count": 0,
        "receipt_fingerprint": "a" * 64,
    }
    rendered = q220_population_focus_sentence(legacy)
    assert "STALE" in rendered
    assert "fresh post-fix population receipt" in rendered
