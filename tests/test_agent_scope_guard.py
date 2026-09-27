from pathlib import Path


def test_agent_queue_uses_central_scope_guard_before_and_after_add():
    text = Path(".github/workflows/agent-request-queue.yml").read_text(encoding="utf-8")
    assert text.count('python -m automation.agent_scope_guard --contract "$RUNNER_TEMP/task_contract.json"') == 2
    assert "git add -A" in text
    assert "AGENT_SCOPE_PROTECTED_INDEX_VIOLATION" in text
    assert "staged_protected=\"$(git diff --cached --name-only -- .github/ research/evidence/ research/authorizations/ gates/)\"" in text
    assert "|| true" not in text


def test_scope_guard_collects_worktree_index_and_untracked_paths():
    text = Path("automation/agent_scope_guard.py").read_text(encoding="utf-8")
    assert '_git("diff", "--name-only")' in text
    assert '_git("diff", "--cached", "--name-only")' in text
    assert '_git("ls-files", "--others", "--exclude-standard")' in text
    assert "PROTECTED" in text
    assert "AGENT_SCOPE_VIOLATION:" in text
