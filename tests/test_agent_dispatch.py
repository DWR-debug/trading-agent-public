import json
from pathlib import Path

import pytest

from automation.agent_dispatch import (
    AgentDispatchError,
    MAX_CONCURRENT_AGENT_TASKS,
    extract_task_metadata,
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


def test_validate_task_accepts_copilot_cli_ready_label():
    manifest = validate_task(
        valid_task(),
        issue_number=999,
        current_master_sha="b" * 40,
        active_agent_count=0,
        labels=["agent-cli-ready"],
    )
    assert manifest["task_id"] == "AGENT-TEST-001"


def test_autonomous_agent_request_queue_uses_two_lanes_and_is_fail_closed():
    root = Path(__file__).parents[1]
    text = (root / ".github" / "workflows" / "agent-request-queue.yml").read_text(encoding="utf-8")
    assert 'paths:' in text
    assert 'agent_requests/**' in text
    assert 'schedule:' in text
    assert 'cron: "*/10 * * * *"' in text
    assert 'workflow_dispatch:' in text
    assert 'lane: [0, 1]' in text
    assert 'trading-agent-agent-cli-queue-lane-${{ matrix.lane }}' in text
    assert 'PAPER_ONLY=True' in text
    assert 'LIVE_TRADING_ENABLED=False' in text
    assert 'orders_enabled=False' in text
    assert 'automatic_promotion=False' in text
    assert 'Automatic PR creation is unavailable' in text
    assert 'Duplicate execution is fail-closed' in text
    assert 'before="${{ github.event.before }}"' in text
    assert 'cp "$RUNNER_TEMP/agent_task_manifest.json" "$RUNNER_TEMP/task_contract.json"' in text
    assert 'python -m automation.agent_dispatch' in text

def test_bounded_copilot_cli_workflow_uses_builtin_token_and_credit_gate():
    root = Path(__file__).parents[1]
    text = (
        root / ".github" / "workflows" / "copilot-cli-engineering-task.yml"
    ).read_text(encoding="utf-8")
    assert "copilot-requests: write" in text
    assert "GITHUB_TOKEN: ${{ github.token }}" in text
    assert "COPILOT_GITHUB_TOKEN" not in text
    assert "--max-ai-credits=45" in text
    assert "--agent=trading-agent-engineer" in text
    assert "github.event.issue.user.login == github.repository_owner" in text
    assert "PAPER_ONLY=True" in text
    assert "LIVE_TRADING_ENABLED=False" in text
    assert "orders_enabled=False" in text
    assert "automatic_promotion=False" in text
    assert "Enforce task-scoped file scope" in text
    assert "Copilot CLI changed file outside task-scoped engineering scope" in text
    assert "allowed_paths" in text
    assert "research/evidence/" in text
    assert ".github/workflows/ci.yml" not in text
    assert ".github/workflows/research-orchestrator.yml" not in text
