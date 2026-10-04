import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from automation.agent_scope_guard import validate as validate_scope
from automation.agent_dispatch import (
    AgentDispatchError,
    MAX_CONCURRENT_AGENT_TASKS,
    acquire_agent_lease,
    atomic_lease_update,
    empty_lease_state,
    normalize_lease_state,
    release_agent_lease,
    renew_agent_lease,
    extract_task_metadata,
    load_event,
    main,
    validate_queued_issue,
    validate_task,
)


def valid_task() -> dict:
    return {
        "schema_version": 1,
        "task_id": "AGENT-TEST-001",
        "worker_class": "engineering",
        "custom_agent": "trading-agent-engineer",
        "base_branch": "master",
        "scope": "bounded regression test",
        "max_session_minutes": 30,
        "deterministic_compute": False,
        "holdout_selection": False,
        "parameter_selection": False,
        "asset_selection": False,
        "threshold_selection": False,
        "horizon_selection": False,
        "research_gate_changes": False,
        "promotion_decision": False,
        "live_execution": False,
        "paid_usage": False,
        "research_decision": False,
        "manual_handoff_required": False,
    }


def test_extract_task_metadata_round_trip():
    task = valid_task()
    body = "<!-- TRADING_AGENT_TASK_V1\n" + json.dumps(task) + "\n-->"
    assert extract_task_metadata(body) == task


def test_validate_task_produces_deterministic_fingerprint():
    manifest = validate_task(
        valid_task(),
        issue_number=999,
        current_master_sha="a" * 40,
        active_agent_count=0,
        labels=["agent-ready"],
    )
    assert manifest["max_concurrent_agent_tasks"] == MAX_CONCURRENT_AGENT_TASKS
    assert manifest["source_master_sha"] == "a" * 40
    assert manifest["allowed_paths"] == [
        "automation/self_hosted_research_worker.py",
        "docs/DEVELOPMENT_ORCHESTRATION.md",
        "docs/GITHUB_FREE_RESOURCE_OPERATING_MODEL.md",
        "docs/SELF_HOSTED_RESEARCH_RUNNER.md",
        "tests/test_self_hosted_research_worker.py",
    ]
    assert len(manifest["manifest_fingerprint"]) == 64

    again = validate_task(
        valid_task(),
        issue_number=999,
        current_master_sha="a" * 40,
        active_agent_count=0,
        labels=["agent-ready"],
    )
    assert manifest["manifest_fingerprint"] == again["manifest_fingerprint"]


@pytest.mark.parametrize(
    "field",
    [
        "deterministic_compute",
        "holdout_selection",
        "parameter_selection",
        "asset_selection",
        "threshold_selection",
        "horizon_selection",
        "research_gate_changes",
        "promotion_decision",
        "live_execution",
        "paid_usage",
    ],
)
def test_validate_task_rejects_unsafe_flag(field):
    task = valid_task()
    task[field] = True
    with pytest.raises(AgentDispatchError, match=field):
        validate_task(
            task,
            issue_number=999,
            current_master_sha="a" * 40,
            active_agent_count=0,
            labels=["agent-ready"],
        )


def test_validate_task_allows_two_bounded_capacity_slots():
    manifest = validate_task(
        valid_task(),
        issue_number=999,
        current_master_sha="a" * 40,
        active_agent_count=1,
        labels=["agent-ready"],
    )
    assert manifest["max_concurrent_agent_tasks"] == 2
    assert manifest["copilot_parallel_session_limit"] == 1


def test_validate_task_rejects_third_bounded_capacity_slot():
    with pytest.raises(AgentDispatchError, match="Concurrency guard"):
        validate_task(
            valid_task(), issue_number=999, current_master_sha="a" * 40,
            active_agent_count=2, labels=["agent-ready"]
        )


def test_two_slot_lease_binds_task_manifest_and_run():
    state = empty_lease_state()
    state, slot0, idempotent = acquire_agent_lease(
        state, task_id="AGENT-A", issue_number=10, manifest_fingerprint="f"*64, run_id="run-1", now=100.0
    )
    assert slot0 == 0 and idempotent is False
    state, slot1, idempotent = acquire_agent_lease(
        state, task_id="AGENT-B", issue_number=11, manifest_fingerprint="e"*64, run_id="run-2", now=100.0
    )
    assert slot1 == 1 and idempotent is False
    with pytest.raises(AgentDispatchError, match="capacity exhausted"):
        acquire_agent_lease(
            state, task_id="AGENT-C", issue_number=12, manifest_fingerprint="d"*64, run_id="run-3", now=100.0
        )


def test_lease_is_idempotent_only_for_exact_same_identity():
    state, slot, idempotent = acquire_agent_lease(
        empty_lease_state(), task_id="AGENT-A", issue_number=10, manifest_fingerprint="f"*64, run_id="run-1", now=100.0
    )
    same, same_slot, again = acquire_agent_lease(
        state, task_id="AGENT-A", issue_number=10, manifest_fingerprint="f"*64, run_id="run-1", now=101.0
    )
    assert same_slot == slot and again is True and same == state
    with pytest.raises(AgentDispatchError, match="different manifest fingerprint"):
        acquire_agent_lease(
            state, task_id="AGENT-A", issue_number=10, manifest_fingerprint="0"*64, run_id="run-1", now=101.0
        )
    with pytest.raises(AgentDispatchError, match="different run_id"):
        acquire_agent_lease(
            state, task_id="AGENT-A", issue_number=10, manifest_fingerprint="f"*64, run_id="run-2", now=101.0
        )


def test_stale_lease_is_reclaimed_and_renewal_cannot_revive_it():
    state, slot, _ = acquire_agent_lease(
        empty_lease_state(), task_id="AGENT-A", issue_number=10, manifest_fingerprint="f"*64, run_id="run-1", now=100.0, ttl_seconds=10
    )
    reclaimed = normalize_lease_state(state, now=110.0)
    assert reclaimed["slots"][slot] is None
    with pytest.raises(AgentDispatchError, match="empty or stale"):
        renew_agent_lease(
            state, slot=slot, task_id="AGENT-A", issue_number=10, manifest_fingerprint="f"*64, run_id="run-1", now=110.0
        )
    reclaimed, new_slot, _ = acquire_agent_lease(
        reclaimed, task_id="AGENT-B", issue_number=11, manifest_fingerprint="e"*64, run_id="run-2", now=110.0
    )
    assert new_slot == slot and reclaimed["slots"][slot]["task_id"] == "AGENT-B"


def test_atomic_lease_update_persists_and_recovers_stale_state(tmp_path):
    path = tmp_path / "lease.json"
    def acquire(state):
        return acquire_agent_lease(
            state, task_id="AGENT-A", issue_number=10, manifest_fingerprint="f"*64, run_id="run-1", now=100.0, ttl_seconds=10
        )
    result = atomic_lease_update(path, acquire)
    assert result[1] == 0
    loaded = normalize_lease_state(json.loads(path.read_text(encoding="utf-8")), now=100.0)
    assert loaded["slots"][0]["task_id"] == "AGENT-A"
    state = normalize_lease_state(json.loads(path.read_text(encoding="utf-8")), now=110.0)
    assert state["slots"][0] is None


def test_validate_task_rejects_two_active_tasks():
    with pytest.raises(AgentDispatchError, match="Concurrency guard"):
        validate_task(
            valid_task(),
            issue_number=999,
            current_master_sha="a" * 40,
            active_agent_count=MAX_CONCURRENT_AGENT_TASKS,
            labels=["agent-ready"],
        )


def test_validate_task_rejects_missing_label():
    with pytest.raises(AgentDispatchError, match="agent-ready"):
        validate_task(
            valid_task(),
            issue_number=999,
            current_master_sha="a" * 40,
            active_agent_count=0,
            labels=[],
        )


def test_validate_task_rejects_wrong_worker_agent_pair():
    task = valid_task()
    task["custom_agent"] = "trading-agent-research-reviewer"
    with pytest.raises(AgentDispatchError, match="custom_agent"):
        validate_task(
            task,
            issue_number=999,
            current_master_sha="a" * 40,
            active_agent_count=0,
            labels=["agent-ready"],
        )


def test_validate_task_rejects_non_master_base():
    task = valid_task()
    task["base_branch"] = "main"
    with pytest.raises(AgentDispatchError, match="master"):
        validate_task(
            task,
            issue_number=999,
            current_master_sha="a" * 40,
            active_agent_count=0,
            labels=["agent-ready"],
        )


def test_validate_task_rejects_protected_allowed_path():
    task = valid_task()
    task["allowed_paths"] = [".github/workflows/**"]
    with pytest.raises(AgentDispatchError, match="protected path"):
        validate_task(
            task,
            issue_number=999,
            current_master_sha="a" * 40,
            active_agent_count=0,
            labels=["agent-cli-ready"],
        )


def test_validate_task_accepts_copilot_cli_ready_label():
    manifest = validate_task(
        valid_task(),
        issue_number=999,
        current_master_sha="b" * 40,
        active_agent_count=0,
        labels=["agent-cli-ready"],
    )
    assert manifest["task_id"] == "AGENT-TEST-001"


@pytest.mark.parametrize(
    ("state", "labels", "is_pull_request", "message"),
    [
        ("closed", ["agent-cli-ready"], False, "no longer open"),
        ("open", [], False, "no longer labeled"),
        ("open", ["agent-cli-ready"], True, "pull request"),
    ],
)
def test_queued_issue_is_revalidated_before_dispatch(state, labels, is_pull_request, message):
    with pytest.raises(AgentDispatchError, match=message):
        validate_queued_issue(
            state,
            labels=labels,
            is_pull_request=is_pull_request,
        )


def test_queued_issue_accepts_agent_ready_label():
    validate_queued_issue(
        "open",
        labels=["agent-ready"],
        is_pull_request=False,
    )


def test_load_event_preserves_resolved_issue_state_and_pull_request_flag(tmp_path):
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps(
            {
                "issue": {
                    "number": 999,
                    "state": "closed",
                    "pull_request": None,
                    "body": "task",
                    "labels": [{"name": "agent-cli-ready"}],
                    "assignees": [],
                }
            }
        ),
        encoding="utf-8",
    )

    assert load_event(event) == (
        999,
        ["agent-cli-ready"],
        "task",
        [],
        "closed",
        False,
    )


def test_dispatch_main_rejects_stale_issue_before_parsing_task(tmp_path, monkeypatch):
    event = tmp_path / "event.json"
    output = tmp_path / "manifest.json"
    event.write_text(
        json.dumps(
            {
                "issue": {
                    "number": 999,
                    "state": "closed",
                    "body": "stale issue with no task contract",
                    "labels": [{"name": "agent-cli-ready"}],
                    "assignees": [],
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "agent_dispatch",
            "--event-json",
            str(event),
            "--master-sha",
            "a" * 40,
            "--active-agent-count",
            "0",
            "--output",
            str(output),
        ],
    )

    with pytest.raises(AgentDispatchError, match="no longer open"):
        main()
    assert not output.exists()


def _git_executable() -> str:
    candidates = [
        os.environ.get("GIT_EXECUTABLE"),
        shutil.which("git"),
    ]
    if os.name == "nt":
        for variable in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
            root = os.environ.get(variable)
            if root:
                candidates.append(str(Path(root) / "Git" / "cmd" / "git.exe"))
                candidates.append(str(Path(root) / "Git" / "bin" / "git.exe"))
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError(
        "Git executable not found; set GIT_EXECUTABLE or install Git for Windows."
    )


def _git(*args: str) -> None:
    subprocess.run([_git_executable(), *args], check=True)


def _scope_test_repo(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-q", str(repo))
    _git("-C", str(repo), "config", "user.name", "Test")
    _git("-C", str(repo), "config", "user.email", "test@example.com")
    (repo / "allowed.txt").write_text("base\n", encoding="utf-8")
    (repo / "outside.txt").write_text("outside base\n", encoding="utf-8")
    (repo / ".github").mkdir()
    (repo / ".github" / "workflow.yml").write_text("protected\n", encoding="utf-8")
    _git(
        "-C",
        str(repo),
        "add",
        "allowed.txt",
        "outside.txt",
        ".github/workflow.yml",
    )
    _git("-C", str(repo), "commit", "-qm", "base")
    monkeypatch.chdir(repo)

    contract = tmp_path / "contract.json"
    contract.write_text(
        json.dumps({"allowed_paths": ["allowed.txt", "docs/**"]}),
        encoding="utf-8",
    )
    return repo, contract


def test_scope_guard_rejects_untracked_file_outside_allowlist(tmp_path, monkeypatch):
    repo, contract = _scope_test_repo(tmp_path, monkeypatch)
    (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="AGENT_SCOPE_VIOLATION:untracked.txt"):
        validate_scope(contract)


def test_scope_guard_rejects_staged_file_outside_allowlist(tmp_path, monkeypatch):
    repo, contract = _scope_test_repo(tmp_path, monkeypatch)
    (repo / "outside.txt").write_text("staged\n", encoding="utf-8")
    _git("add", "outside.txt")

    with pytest.raises(SystemExit, match="AGENT_SCOPE_VIOLATION:outside.txt"):
        validate_scope(contract)


def test_scope_guard_rejects_unstaged_file_outside_allowlist(tmp_path, monkeypatch):
    repo, contract = _scope_test_repo(tmp_path, monkeypatch)
    (repo / "outside.txt").write_text("unstaged\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="AGENT_SCOPE_VIOLATION:outside.txt"):
        validate_scope(contract)


def test_scope_guard_rejects_rename_out_of_protected_prefix(tmp_path, monkeypatch):
    repo, contract = _scope_test_repo(tmp_path, monkeypatch)
    (repo / "docs").mkdir()
    _git("mv", ".github/workflow.yml", "docs/workflow.yml")

    with pytest.raises(SystemExit, match=r"AGENT_SCOPE_VIOLATION:.*\.github/workflow\.yml"):
        validate_scope(contract)


def test_scope_guard_does_not_extend_directory_wildcard_to_sibling_prefix(
    tmp_path, monkeypatch
):
    repo, contract = _scope_test_repo(tmp_path, monkeypatch)
    escaped = repo / "docs-escape"
    escaped.mkdir()
    (escaped / "note.md").write_text("outside\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="AGENT_SCOPE_VIOLATION:docs-escape/note.md"):
        validate_scope(contract)


def test_scope_guard_does_not_treat_backslash_filename_as_directory_path(
    tmp_path, monkeypatch
):
    repo, contract = _scope_test_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "automation.agent_scope_guard.changed_paths",
        lambda: ["docs\\escape.md"],
    )

    with pytest.raises(SystemExit, match="AGENT_SCOPE_VIOLATION:"):
        validate_scope(contract)


def test_scope_guard_accepts_allowed_staged_and_untracked_files(tmp_path, monkeypatch):
    repo, contract = _scope_test_repo(tmp_path, monkeypatch)
    (repo / "allowed.txt").write_text("staged change\n", encoding="utf-8")
    _git("add", "allowed.txt")
    (repo / "docs").mkdir()
    (repo / "docs" / "note.md").write_text("untracked\n", encoding="utf-8")

    assert validate_scope(contract) == ["allowed.txt", "docs/note.md"]


def test_autonomous_agent_request_queue_uses_two_lanes_and_is_fail_closed():
    root = Path(__file__).parents[1]
    text = (root / ".github" / "workflows" / "agent-request-queue.yml").read_text(encoding="utf-8")
    assert 'paths:' in text
    assert 'agent_requests/**' in text
    assert 'schedule:' in text
    assert 'cron: "15 */2 * * *"' in text
    assert 'workflow_dispatch:' in text
    assert 'lane: [0, 1]' in text
    assert 'trading-agent-agent-cli-queue' in text
    assert 'cancel-in-progress: false' in text
    assert 'PAPER_ONLY=True' in text
    assert 'LIVE_TRADING_ENABLED=False' in text
    assert 'orders_enabled=False' in text
    assert 'automatic_promotion=False' in text
    assert 'Automatic PR creation is unavailable' in text
    assert 'Duplicate execution is fail-closed' in text
    assert "Resolve next queued request" in text
    assert 'agent_requests/lane${{ matrix.lane }}/*.request' in text
    assert "GITHUB_EVENT_BEFORE" not in text
    assert 'cp "$RUNNER_TEMP/agent_task_manifest.json" "$RUNNER_TEMP/task_contract.json"' in text
    assert 'python -m automation.agent_dispatch' in text

def test_bounded_copilot_cli_workflow_uses_personal_repo_token_and_credit_gate():
    root = Path(__file__).parents[1]
    text = (
        root / ".github" / "workflows" / "agent-request-queue.yml"
    ).read_text(encoding="utf-8")
    assert "Check personal Copilot token" in text
    assert "PERSONAL_COPILOT_TOKEN: ${{ secrets.COPILOT_GITHUB_TOKEN }}" in text
    assert "COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_GITHUB_TOKEN }}" in text
    assert "copilot-requests: write" not in text
    assert "--max-ai-credits=30" in text
    assert "--agent=trading-agent-engineer" in text
    assert "PAPER_ONLY=True" in text
    assert "LIVE_TRADING_ENABLED=False" in text
    assert "orders_enabled=False" in text
    assert "automatic_promotion=False" in text
    assert "allowed_paths" in text
    assert "research/evidence/" in text
    assert ".github/workflows/ci.yml" not in text
    assert 'BRANCH="${BRANCH:-$(git branch --show-current)}"' in text
    assert 'test "$BRANCH" != "master"' in text
