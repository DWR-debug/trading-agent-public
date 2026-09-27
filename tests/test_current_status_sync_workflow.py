from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "current-status-sync.yml"


def test_current_status_sync_uses_rest_api_and_real_shell_expansion():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'gh api "/repos/${GITHUB_REPOSITORY}/pulls?state=open&per_page=100"' in text
    assert 'gh api "/repos/${GITHUB_REPOSITORY}/issues?state=open&labels=agent-cli-ready&per_page=100"' in text
    assert '--source-master-sha "${GITHUB_SHA}"' in text
    assert '--workflow-run-id "${GITHUB_RUN_ID}"' in text
    assert '--github-state "${RUNNER_TEMP}/status/github_state.json"' in text
    assert "gh pr list" not in text
    assert "gh issue list" not in text
    assert "gh api --silent" not in text
    assert "\\${GITHUB_SHA}" not in text
    assert "\\${RUNNER_TEMP}" not in text
