"""Fail-closed contract for bounded Copilot-agent dispatch.

The module validates an issue's explicit machine-readable task contract and
produces a deterministic manifest. It deliberately does not perform any
scientific decision, holdout selection, gate change, promotion, or live action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
MAX_CONCURRENT_AGENT_TASKS = 2
ALLOWED_WORKERS = {
    "engineering": "trading-agent-engineer",
}
DEFAULT_ALLOWED_PATHS = (
    "automation/self_hosted_research_worker.py",
    "tests/test_self_hosted_research_worker.py",
    "docs/SELF_HOSTED_RESEARCH_RUNNER.md",
    "docs/GITHUB_FREE_RESOURCE_OPERATING_MODEL.md",
    "docs/DEVELOPMENT_ORCHESTRATION.md",
)
FORBIDDEN_PATH_PREFIXES = (
    ".github/",
    "research/evidence/",
    "research/authorizations/",
    "gates/",
)
MARKER_START = "<!-- TRADING_AGENT_TASK_V1"
MARKER_END = "-->"


class AgentDispatchError(ValueError):
    """Raised when an agent-dispatch contract is invalid."""


REQUIRED_FALSE_FLAGS = (
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
)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def extract_task_metadata(issue_body: str) -> dict[str, Any]:
    """Extract the exact JSON task contract embedded in an issue body."""
    start = issue_body.find(MARKER_START)
    if start < 0:
        raise AgentDispatchError("Missing TRADING_AGENT_TASK_V1 marker.")
    start += len(MARKER_START)
    end = issue_body.find(MARKER_END, start)
    if end < 0:
        raise AgentDispatchError("Unterminated TRADING_AGENT_TASK_V1 marker.")
    raw = issue_body[start:end].strip()
    if not raw.startswith("{") or not raw.endswith("}"):
        raise AgentDispatchError("Task marker must contain one JSON object.")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AgentDispatchError(f"Invalid task JSON: {exc.msg}.") from exc
    if not isinstance(payload, dict):
        raise AgentDispatchError("Task JSON must be an object.")
    return payload


def normalize_allowed_paths(task: dict[str, Any]) -> list[str]:
    """Normalize explicit repository-relative task scope and reject protected paths."""
    raw = task.get("allowed_paths", DEFAULT_ALLOWED_PATHS)
    if not isinstance(raw, list) or not raw or any(not isinstance(item, str) or not item.strip() for item in raw):
        raise AgentDispatchError("allowed_paths must be a non-empty list of strings.")
    normalized: list[str] = []
    for item in raw:
        pattern = item.strip().replace("\\", "/")
        if pattern.startswith("/") or ".." in pattern.split("/"):
            raise AgentDispatchError("allowed_paths must be repository-relative and cannot contain ..")
        if pattern.startswith(FORBIDDEN_PATH_PREFIXES):
            raise AgentDispatchError(f"allowed_paths includes protected path: {pattern}")
        if "*" in pattern and not pattern.endswith("/**"):
            raise AgentDispatchError("allowed_paths supports only trailing /** wildcards.")
        normalized.append(pattern)
    return sorted(set(normalized))


def validate_task(
    task: dict[str, Any],
    *,
    issue_number: int,
    current_master_sha: str,
    active_agent_count: int,
    labels: list[str],
    assignees: list[str] | None = None,
) -> dict[str, Any]:
    """Validate task metadata and return a normalized dispatch manifest."""
    if task.get("schema_version") != SCHEMA_VERSION:
        raise AgentDispatchError("Unsupported task schema_version.")
    if not ({"agent", "agent-ready", "agent-cli-ready"} & set(labels)):
        raise AgentDispatchError("Task is not labeled agent or agent-ready.")
    if "copilot-swe-agent[bot]" in (assignees or []):
        raise AgentDispatchError("Task is already assigned to Copilot; duplicate dispatch is forbidden.")
    if not isinstance(issue_number, int) or issue_number <= 0:
        raise AgentDispatchError("issue_number must be a positive integer.")
    if not current_master_sha or not re.fullmatch(r"[0-9a-f]{40}", current_master_sha):
        raise AgentDispatchError("current_master_sha must be a 40-char commit SHA.")
    if not isinstance(active_agent_count, int) or active_agent_count < 0:
        raise AgentDispatchError("active_agent_count must be non-negative.")
    if active_agent_count >= MAX_CONCURRENT_AGENT_TASKS:
        raise AgentDispatchError(
            f"Concurrency guard: {active_agent_count} active agent tasks; "
            f"limit is {MAX_CONCURRENT_AGENT_TASKS}."
        )

    task_id = task.get("task_id")
    worker_class = task.get("worker_class")
    base_branch = task.get("base_branch")
    scope = task.get("scope")
    if not isinstance(task_id, str) or not task_id.strip():
        raise AgentDispatchError("task_id is required.")
    if not task_id.startswith("AGENT-"):
        raise AgentDispatchError("task_id must use the AGENT-* namespace.")
    if not isinstance(worker_class, str) or worker_class not in ALLOWED_WORKERS:
        raise AgentDispatchError("worker_class is not allowed.")
    if base_branch != "master":
        raise AgentDispatchError("Agent tasks must branch from master.")
    if not isinstance(scope, str) or not scope.strip():
        raise AgentDispatchError("scope is required.")
    allowed_paths = normalize_allowed_paths(task)

    custom_agent = task.get("custom_agent", ALLOWED_WORKERS[worker_class])
    if custom_agent != ALLOWED_WORKERS[worker_class]:
        raise AgentDispatchError("custom_agent does not match worker_class.")

    max_minutes = task.get("max_session_minutes", 45)
    if not isinstance(max_minutes, int) or not 1 <= max_minutes <= 45:
        raise AgentDispatchError("max_session_minutes must be between 1 and 45.")

    for flag in REQUIRED_FALSE_FLAGS:
        if task.get(flag) is not False:
            raise AgentDispatchError(f"{flag} must be false.")

    if task.get("research_decision", False) is not False:
        raise AgentDispatchError("research_decision must be false.")
    if task.get("manual_handoff_required", True) is not False:
        raise AgentDispatchError("manual_handoff_required must be false.")

    normalized = {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id.strip(),
        "issue_number": issue_number,
        "worker_class": worker_class,
        "custom_agent": custom_agent,
        "base_branch": base_branch,
        "source_master_sha": current_master_sha,
        "scope": scope.strip(),
        "allowed_paths": allowed_paths,
        "max_session_minutes": max_minutes,
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
        "max_concurrent_agent_tasks": MAX_CONCURRENT_AGENT_TASKS,
        "active_agent_count_before_dispatch": active_agent_count,
        "issue_body_sha256": task.get("_issue_body_sha256"),
    }
    canonical = _canonical_json(normalized)
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {**normalized, "manifest_fingerprint": fingerprint}


def load_event(event_path: Path) -> tuple[int, list[str], str, list[str]]:
    payload = json.loads(event_path.read_text(encoding="utf-8"))
    issue = payload.get("issue") or {}
    issue_number = issue.get("number")
    body = issue.get("body") or ""
    labels = [
        item.get("name")
        for item in (issue.get("labels") or [])
        if isinstance(item, dict) and item.get("name")
    ]
    assignees = [
        item.get("login")
        for item in (issue.get("assignees") or [])
        if isinstance(item, dict) and item.get("login")
    ]
    return issue_number, labels, body, assignees


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-json", type=Path, required=True)
    parser.add_argument("--master-sha", required=True)
    parser.add_argument("--active-agent-count", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    issue_number, labels, body, assignees = load_event(args.event_json)
    task = extract_task_metadata(body)
    task["_issue_body_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    manifest = validate_task(
        task,
        issue_number=issue_number,
        current_master_sha=args.master_sha,
        active_agent_count=args.active_agent_count,
        labels=labels,
        assignees=assignees,
    )
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"AGENT DISPATCH CONTRACT OK: {manifest['task_id']}")
    print(f"MANIFEST_FINGERPRINT={manifest['manifest_fingerprint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
