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
