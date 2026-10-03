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


def test_status_sync_has_idempotent_scheduled_heartbeat_for_automated_commits():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'cron: "7 */2 * * *"' in text
    assert "CURRENT_STATUS_ALREADY_SYNCHRONIZED" in text
    assert "recorded_status_sha" in text
