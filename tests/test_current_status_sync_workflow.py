from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "current-status-sync.yml"


def test_current_status_sync_uses_rest_api_and_real_shell_expansion():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'gh api "/repos/${GITHUB_REPOSITORY}/pulls?state=open&per_page=100"' in text
    assert 'gh api "/repos/${GITHUB_REPOSITORY}/issues?state=open&labels=agent-cli-ready&per_page=100"' in text
    assert '--source-master-sha "${source_master_sha}"' in text
    assert '--workflow-run-id "${GITHUB_RUN_ID}"' in text
    assert '--github-state "${RUNNER_TEMP}/status/github_state.json"' in text
    assert "gh pr list" not in text
    assert "gh issue list" not in text
    assert "gh api --silent" not in text
    assert "\\${GITHUB_SHA}" not in text
    assert "\\${RUNNER_TEMP}" not in text

def test_status_sync_uses_checked_out_master_sha_not_push_event_sha():
    text = Path(".github/workflows/current-status-sync.yml").read_text(encoding="utf-8")
    assert "git rev-parse HEAD" in text
    assert 'echo "STATUS_SOURCE_SHA=${checked_out_master_sha}" >> "${GITHUB_ENV}"' in text
    assert '--source-master-sha "${source_master_sha}"' in text
    assert 'assert d["source_master_sha"] == os.environ["STATUS_SOURCE_SHA"]' in text
    assert 'if [ "$remote_master_sha" != "$STATUS_SOURCE_SHA" ]; then' in text
    assert "STATUS_SYNC_MASTER_MOVED_BEFORE_GENERATION" in text


def test_generated_status_matches_current_hosted_qa_architecture():
    generator = Path("automation/sync_current_operational_status.py").read_text(encoding="utf-8")
    assert '"continuous_qa": {' in generator
    assert '"cadence": "15 */6 * * *"' in generator
    assert '"runner": "GitHub-hosted windows-latest"' in generator
    assert '"self_hosted_slots_consumed": 0' in generator
    assert '"research_continuity": {' in generator
    assert "Continuous QA is scheduled every 6 hours on GitHub-hosted Windows" in generator


def test_status_generator_exposes_q179_q184_receipts():
    text = Path("automation/sync_current_operational_status.py").read_text(encoding="utf-8")
    assert "q179_q184_source_feasibility_latest.json" in text
    assert "q179_q184_pit_readiness_r1_latest.json" in text
    assert '"q179_q184_source_feasibility": q179_q184_source_receipt' in text
    assert '"q179_q184_pit_readiness_r1": q179_q184_pit_receipt' in text
    assert "Q179–Q184 Orthogonal Source/PIT Frontier" in text
