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

    assert "Active execution focus is locked to exactly three candidates: Q104:I19, Q220 and Q221." in focus
    assert "Q218 has been removed from active focus and automatic dispatch" in focus
    assert "Q219 remains paused; its prior evidence is preserved." in focus
    assert "do not repair the receipts or restart the census" in focus
    assert "53 unique unresolved accession keys" in focus
    assert "zero new attempts and zero repairs" in focus
    assert "PR #1363 is merged" in focus
    assert "Read-only residual lineage run #38255701998 completed LINEAGE_DIAGNOSTIC_COMPLETE" in focus
    assert "4/4 frozen accessions, 12/12 SEC header probes" in focus
    assert "unresolved cross-publication source-field conflict" in focus
    assert "or restart the census" in focus
    assert "### Historical research handoff checkpoint — 2026-10-12T10:17Z" in doc
    assert "Q104:I19" in doc and "#38231636160" in doc
    assert "FORENSIC_COMPARISON_INCOMPLETE" in doc and "#38233685159" in doc
    assert "2,829,769,099 bytes downloaded" in doc
    assert "348/348" in doc and "247/247" in doc
    assert "one captured exact URL and six no-hit responses" in focus
    assert "no-hit is not proof of historical absence" in focus
    assert "do not expand the exact-page route across the 348-key sample" in focus
    assert "publicDeltaDate is documented as a filter over Last Modified Date or Reveal Date" in focus
    assert "not a dispatch-ready source contract" in focus
    assert "Q220: original SEC daily Feed forensic run #38233685159" in focus
    assert "daily .nc.tar.gz member is accession.nc" in focus
    assert "daily Feed TAR members `{accession}.nc`" in doc
    assert "both CI architectures and full-suite verification passed" in focus
    assert "Post-fix run #38254139755 is terminal FORENSIC_COMPARISON_INCOMPLETE" in focus
    assert "three preselected sample keys" in focus
    assert "2,829,769,099 bytes downloaded; receipt fingerprint 840f280cbcb1fdbe4b2fbaa88f8d7f02edf447799e13fe0171d37fcd57f3221b" in focus
    assert "each original Feed submission header lacks ACCEPTANCE-DATETIME" in focus
    assert "Do not redownload these multi-GB Feeds" in focus
    assert "header-only probes" in focus
    assert "cannot clear the 55 primary source hash failures" in focus
    assert "do not repeat an outcome-bearing run" in focus
    assert focus.count("Q218 primary one-shot and pre-registered fresh-symbol replication both completed in PAPER_ONLY") == 1
    # This status sync must fail closed when the population source code changed
    # but the old immutable receipt has not yet been regenerated. The focused
    # q220_population_focus_sentence tests cover the positive current-code case.
    q220_chain_positive = "Q220 PIT chain is positive for all 55 fixed filings" in focus
    q220_compiler_positive = "Q220 historical-prefix/representation PIT compiler is positive" in focus
    q220_population_positive = "Q220 historical as-filed population gate is positive and version-bound" in focus
    q220_stale = "Q220 population receipt is STALE:" in focus
    q220_blocked = "Q220 current-code population gate is BLOCKED:" in focus
    q220_compiler_blocked = "Q220 historical prefix/PIT compiler is BLOCKED:" in focus
    assert q220_chain_positive or q220_compiler_positive or q220_population_positive or q220_stale or q220_blocked or q220_compiler_blocked
    if q220_chain_positive:
        assert "bounded adversarial robustness review and formal trial-governance reconciliation" in focus
        assert "performance authorization remains closed" in focus
    elif q220_compiler_positive:
        assert "Next gate: independent PIT reproduction" in focus
    elif q220_population_positive:
        assert "Next gate: historical prefix/acceptance-time PIT representation-state compiler" in focus
    elif q220_compiler_blocked:
        assert "55 primary-document hash mismatches" in focus
        assert "different compiler fingerprint and is not current" in focus
        assert "repair source hash mismatches" in focus
        assert "performance authorization remains closed" in focus
    else:
        assert "historical prefix/PIT compiler" in focus

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
    assert "Q220 current-code population gate is BLOCKED" in q220_population_focus_sentence(negative)
    negative = dict(positive, failure_count=1)
    assert "no positive current-code receipt is published" in q220_population_focus_sentence(negative)





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
