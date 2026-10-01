"""Fail-closed contract for bounded Copilot-agent dispatch.

The module validates an issue's explicit machine-readable task contract and
produces a deterministic manifest. It deliberately does not perform any
scientific decision, holdout selection, gate change, promotion, or live action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
MAX_CONCURRENT_AGENT_TASKS = 2
COPILOT_PARALLEL_SESSION_LIMIT = 1
LEASE_SCHEMA_VERSION = 1
LEASE_SLOT_COUNT = 2
DEFAULT_LEASE_TTL_SECONDS = 900
LEASE_LOCK_TIMEOUT_SECONDS = 15
LEASE_LOCK_STALE_SECONDS = 120
ALLOWED_WORKERS = {
    "engineering": "trading-agent-engineer",
}
DEFAULT_ALLOWED_PATHS = [
    "automation/self_hosted_research_worker.py",
    "tests/test_self_hosted_research_worker.py",
    "docs/SELF_HOSTED_RESEARCH_RUNNER.md",
    "docs/GITHUB_FREE_RESOURCE_OPERATING_MODEL.md",
    "docs/DEVELOPMENT_ORCHESTRATION.md",
]
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


def empty_lease_state() -> dict[str, Any]:
    """Return the canonical empty two-slot lease state."""
    return {
        "schema_version": LEASE_SCHEMA_VERSION,
        "slot_count": LEASE_SLOT_COUNT,
        "slots": [None] * LEASE_SLOT_COUNT,
    }


def _lease_now(now: float | None) -> float:
    return float(time.time() if now is None else now)


def _lease_fingerprint(*, task_id: str, issue_number: int, manifest_fingerprint: str, run_id: str) -> str:
    payload = {
        "task_id": task_id,
        "issue_number": issue_number,
        "manifest_fingerprint": manifest_fingerprint,
        "run_id": run_id,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def normalize_lease_state(state: dict[str, Any] | None, *, now: float | None = None) -> dict[str, Any]:
    """Normalize leases, remove stale entries, and reject duplicate live bindings."""
    now_value = _lease_now(now)
    if state is None:
        state = empty_lease_state()
    if not isinstance(state, dict) or state.get("schema_version") != LEASE_SCHEMA_VERSION:
        raise AgentDispatchError("Unsupported lease state schema.")
    slots = state.get("slots")
    if not isinstance(slots, list) or len(slots) != LEASE_SLOT_COUNT:
        raise AgentDispatchError("Lease state must contain exactly two slots.")
    normalized: list[dict[str, Any] | None] = []
    seen_tasks: set[str] = set()
    seen_fingerprints: set[str] = set()
    for lease in slots:
        if lease is None:
            normalized.append(None)
            continue
        if not isinstance(lease, dict):
            raise AgentDispatchError("Lease slot must be an object or null.")
        try:
            expires_at = float(lease["expires_at"])
            task_id = str(lease["task_id"])
            manifest_fingerprint = str(lease["manifest_fingerprint"])
            run_id = str(lease["run_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AgentDispatchError("Lease binding is malformed.") from exc
        if expires_at <= now_value:
            normalized.append(None)
            continue
        if not task_id or not manifest_fingerprint or not run_id:
            raise AgentDispatchError("Active lease binding is incomplete.")
        if task_id in seen_tasks:
            raise AgentDispatchError(f"Duplicate active task_id lease: {task_id}.")
        if manifest_fingerprint in seen_fingerprints:
            raise AgentDispatchError("Duplicate active manifest fingerprint lease.")
        seen_tasks.add(task_id)
        seen_fingerprints.add(manifest_fingerprint)
        normalized.append(dict(lease))
    return {"schema_version": LEASE_SCHEMA_VERSION, "slot_count": LEASE_SLOT_COUNT, "slots": normalized}


def acquire_agent_lease(
    state: dict[str, Any] | None,
    *,
    task_id: str,
    issue_number: int,
    manifest_fingerprint: str,
    run_id: str,
    now: float | None = None,
    ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
) -> tuple[dict[str, Any], int, bool]:
    """Acquire or idempotently return a slot bound to the exact dispatch identity."""
    if not task_id or not manifest_fingerprint or not run_id:
        raise AgentDispatchError("Lease requires task_id, manifest_fingerprint and run_id.")
    if not isinstance(issue_number, int) or issue_number <= 0:
        raise AgentDispatchError("Lease issue_number must be positive.")
    if not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
        raise AgentDispatchError("Lease TTL must be positive.")
    now_value = _lease_now(now)
    state = normalize_lease_state(state, now=now_value)
    binding_fp = _lease_fingerprint(
        task_id=task_id, issue_number=issue_number, manifest_fingerprint=manifest_fingerprint, run_id=run_id
    )
    for index, lease in enumerate(state["slots"]):
        if lease is None:
            continue
        if lease["task_id"] == task_id:
            if lease["manifest_fingerprint"] != manifest_fingerprint:
                raise AgentDispatchError("Task ID already has a different manifest fingerprint.")
            if lease["run_id"] != run_id:
                raise AgentDispatchError("Task ID already has a different run_id.")
            return dict(state), index, True
        if lease["binding_fingerprint"] == binding_fp:
            raise AgentDispatchError("Lease binding fingerprint is unexpectedly duplicated.")
    for index, lease in enumerate(state["slots"]):
        if lease is not None:
            continue
        state["slots"][index] = {
            "task_id": task_id,
            "issue_number": issue_number,
            "manifest_fingerprint": manifest_fingerprint,
            "run_id": run_id,
            "binding_fingerprint": binding_fp,
            "acquired_at": now_value,
            "expires_at": now_value + ttl_seconds,
            "status": "ACTIVE",
        }
        return state, index, False
    raise AgentDispatchError("Agent capacity exhausted: both lease slots are active.")


def validate_agent_lease(
    lease: dict[str, Any],
    *,
    task_id: str,
    issue_number: int,
    manifest_fingerprint: str,
    run_id: str,
    now: float | None = None,
) -> None:
    """Require an active lease to match the exact task/manifest/run identity."""
    if not isinstance(lease, dict) or lease.get("status") != "ACTIVE":
        raise AgentDispatchError("Lease is not active.")
    if float(lease.get("expires_at", 0)) <= _lease_now(now):
        raise AgentDispatchError("Lease is stale.")
    expected = _lease_fingerprint(
        task_id=task_id, issue_number=issue_number, manifest_fingerprint=manifest_fingerprint, run_id=run_id
    )
    if lease.get("binding_fingerprint") != expected:
        raise AgentDispatchError("Lease binding mismatch.")


def renew_agent_lease(
    state: dict[str, Any],
    *,
    slot: int,
    task_id: str,
    issue_number: int,
    manifest_fingerprint: str,
    run_id: str,
    now: float | None = None,
    ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
) -> dict[str, Any]:
    """Renew one exact lease; stale or mismatched bindings cannot be revived."""
    now_value = _lease_now(now)
    state = normalize_lease_state(state, now=now_value)
    if not isinstance(slot, int) or not 0 <= slot < LEASE_SLOT_COUNT:
        raise AgentDispatchError("Invalid lease slot.")
    lease = state["slots"][slot]
    if lease is None:
        raise AgentDispatchError("Lease slot is empty or stale.")
    validate_agent_lease(
        lease, task_id=task_id, issue_number=issue_number,
        manifest_fingerprint=manifest_fingerprint, run_id=run_id, now=now_value
    )
    if not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
        raise AgentDispatchError("Lease TTL must be positive.")
    lease["expires_at"] = now_value + ttl_seconds
    state["slots"][slot] = lease
    return state


def release_agent_lease(
    state: dict[str, Any],
    *,
    slot: int,
    task_id: str,
    issue_number: int,
    manifest_fingerprint: str,
    run_id: str,
    now: float | None = None,
) -> dict[str, Any]:
    """Release one exact lease. A different binding is never allowed to release it."""
    now_value = _lease_now(now)
    state = normalize_lease_state(state, now=now_value)
    if not isinstance(slot, int) or not 0 <= slot < LEASE_SLOT_COUNT:
        raise AgentDispatchError("Invalid lease slot.")
    lease = state["slots"][slot]
    if lease is None:
        raise AgentDispatchError("Lease slot is already free or stale.")
    validate_agent_lease(
        lease, task_id=task_id, issue_number=issue_number,
        manifest_fingerprint=manifest_fingerprint, run_id=run_id, now=now_value
    )
    state["slots"][slot] = None
    return state


def atomic_lease_update(path: Path, mutator, *, lock_timeout_seconds: int = LEASE_LOCK_TIMEOUT_SECONDS) -> Any:
    """Apply a lease mutation under a cross-process lock and atomically replace the state file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(str(path) + ".lock")
    deadline = time.monotonic() + lock_timeout_seconds
    fd = None
    while fd is None:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii"))
        except FileExistsError:
            try:
                if time.time() - lock_path.stat().st_mtime > LEASE_LOCK_STALE_SECONDS:
                    lock_path.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise AgentDispatchError("Lease lock acquisition timed out.")
            time.sleep(0.05)
    os.close(fd)
    try:
        if path.exists():
            try:
                state = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise AgentDispatchError("Lease state file is unreadable.") from exc
        else:
            state = empty_lease_state()
        result = mutator(state)
        new_state = result[0] if isinstance(result, tuple) and result and isinstance(result[0], dict) else result
        payload = json.dumps(new_state, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        fd_tmp, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
        try:
            with os.fdopen(fd_tmp, "w", encoding="utf-8") as fh:
                fh.write(payload)
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        return result
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass

def validate_queued_issue(
    issue_state: object,
    *,
    labels: list[str],
    is_pull_request: bool,
) -> None:
    if issue_state != "open":
        raise AgentDispatchError("Queued issue is no longer open.")
    if is_pull_request:
        raise AgentDispatchError("Queued item is a pull request, not an issue.")
    if not ({"agent", "agent-ready", "agent-cli-ready"} & set(labels)):
        raise AgentDispatchError("Queued issue is no longer labeled agent/agent-ready/agent-cli-ready.")


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


def validate_scope_paths(paths: list[str], task: dict[str, Any]) -> list[str]:
    """Validate changed repository paths against the normalized task scope."""
    allowed_paths = normalize_allowed_paths(task)
    changed_paths = sorted(set(paths))
    violations = [
        path
        for path in changed_paths
        if path.startswith(FORBIDDEN_PATH_PREFIXES)
        or not any(
            path.startswith(pattern[:-2]) if pattern.endswith("/**") else path == pattern
            for pattern in allowed_paths
        )
    ]
    if violations:
        raise AgentDispatchError(",".join(violations))
    return changed_paths


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
        "copilot_parallel_session_limit": COPILOT_PARALLEL_SESSION_LIMIT,
        "lease_schema_version": LEASE_SCHEMA_VERSION,
        "lease_slot_count": LEASE_SLOT_COUNT,
        "active_agent_count_before_dispatch": active_agent_count,
        "issue_body_sha256": task.get("_issue_body_sha256"),
    }
    canonical = _canonical_json(normalized)
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {**normalized, "manifest_fingerprint": fingerprint}


def load_event(event_path: Path) -> tuple[int, list[str], str, list[str], object, bool]:
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
    return (
        issue_number,
        labels,
        body,
        assignees,
        issue.get("state"),
        bool(issue.get("pull_request")),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-json", type=Path, required=True)
    parser.add_argument("--master-sha", required=True)
    parser.add_argument("--active-agent-count", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    issue_number, labels, body, assignees, issue_state, is_pull_request = load_event(args.event_json)
    validate_queued_issue(
        issue_state,
        labels=labels,
        is_pull_request=is_pull_request,
    )

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
