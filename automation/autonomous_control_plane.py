"""Deterministic technical control-plane planning for bounded agent resources.

The control plane only plans queue routing and operational telemetry.
It never selects research candidates, changes evidence or gates, promotes work,
or executes live trading.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from automation.agent_dispatch import (
    AgentDispatchError,
    extract_task_metadata,
    validate_queued_issue,
    validate_task,
)


def validate_request_snapshot(
    requests: list[dict],
    *,
    lanes: tuple[str, ...],
    request_root: Path = Path("agent_requests"),
) -> None:
    """Ensure the API queue inventory agrees with the checked-out repository."""
    if not isinstance(requests, list):
        raise AgentDispatchError("Queue request snapshot must be a list.")

    expected: set[tuple[str, str, str]] = set()
    for lane in lanes:
        lane_dir = request_root / f"lane{lane}"
        if not lane_dir.exists():
            continue
        if not lane_dir.is_dir():
            raise AgentDispatchError(f"Queue lane path is not a directory: {lane_dir}.")
        for path in lane_dir.glob("*.request"):
            if not path.is_file():
                raise AgentDispatchError(f"Queue request is not a file: {path}.")
            task_id = path.name.removesuffix(".request")
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise AgentDispatchError(f"Cannot read queue request: {path}.") from exc
            if not isinstance(payload, dict) or payload.get("task_id") != task_id:
                raise AgentDispatchError(f"Invalid task id in queue request: {path}.")
            relative_path = Path("agent_requests") / path.relative_to(request_root)
            expected.add((lane, task_id, relative_path.as_posix()))

    observed: set[tuple[str, str, str]] = set()
    for request in requests:
        if not isinstance(request, dict):
            raise AgentDispatchError("Queue request entries must be objects.")
        lane = request.get("lane")
        task_id = request.get("task_id")
        path = request.get("path")
        if (
            not isinstance(lane, str)
            or lane not in lanes
            or not isinstance(task_id, str)
            or not task_id.strip()
            or not isinstance(path, str)
        ):
            raise AgentDispatchError("Queue request entry has invalid lane, task_id, or path.")
        observed.add((lane, task_id, path))

    if observed != expected:
        raise AgentDispatchError(
            "Queue API snapshot does not match the checked-out request inventory."
        )


def _labels(issue: dict) -> set[str]:
    return {
        x["name"]
        for x in issue.get("labels", [])
        if isinstance(x, dict) and isinstance(x.get("name"), str)
    }


def _task_id(issue: dict) -> str | None:
    try:
        task = extract_task_metadata(issue.get("body") or "")
    except AgentDispatchError:
        return None
    value = task.get("task_id")
    return value.strip() if isinstance(value, str) and value.strip() else None


def eligible_issues(issues: list[dict], owner: str) -> list[dict]:
    out = []
    for issue in issues:
        if issue.get("state") != "open" or issue.get("user", {}).get("login") != owner:
            continue
        if issue.get("pull_request") or not ({"agent", "agent-ready", "agent-cli-ready"} & _labels(issue)) or issue.get("assignees"):
            continue
        if _task_id(issue) is None:
            continue
        out.append(issue)
    return sorted(
        out,
        key=lambda x: (str(x.get("created_at") or ""), int(x.get("number") or 0)),
    )


def request_index(
    requests: list[dict],
    lanes: tuple[str, ...] = ("0", "1"),
) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for request in requests:
        if not isinstance(request, dict):
            raise AgentDispatchError("Queue request entries must be objects.")
        task_id = request.get("task_id")
        lane = str(request.get("lane", ""))
        path = request.get("path")
        if not isinstance(task_id, str) or not task_id.strip():
            raise AgentDispatchError("Queue request task_id must be a non-empty string.")
        task_id = task_id.strip()
        if lane not in lanes or not isinstance(path, str) or not path:
            raise AgentDispatchError(f"Queue request is invalid for task {task_id}.")
        if path != f"agent_requests/lane{lane}/{task_id}.request":
            raise AgentDispatchError(f"Queue request path is invalid for task {task_id}.")
        if task_id in indexed:
            raise AgentDispatchError(f"Duplicate queued task_id: {task_id}.")
        indexed[task_id] = request
    return indexed


def plan(
    *,
    issues: list[dict],
    requests: list[dict],
    existing_branches: set[str],
    owner: str,
    lanes: tuple[str, ...] = ("0", "1"),
) -> dict:
    indexed = request_index(requests, lanes)
    retire = []
    active = {}

    for request in requests:
        task_id = request["task_id"].strip()
        lane = str(request["lane"])
        path = request["path"]
        branch = f"agent/{task_id}-copilot-cli"
        if branch in existing_branches:
            retire.append(
                {
                    "lane": lane,
                    "task_id": task_id,
                    "path": path,
                    "reason": "published agent branch exists",
                }
            )
        else:
            active[task_id] = request

    occupied = {str(x["lane"]) for x in active.values()}
    free = [lane for lane in lanes if lane not in occupied]
    assign = []
    planned_task_ids = set(indexed)

    for issue in eligible_issues(issues, owner):
        task_id = _task_id(issue)
        branch = f"agent/{task_id}-copilot-cli" if task_id else ""
        if (
            not task_id
            or task_id in planned_task_ids
            or branch in existing_branches
            or not free
        ):
            continue
        lane = free.pop(0)
        assign.append(
            {
                "lane": lane,
                "issue_number": int(issue["number"]),
                "task_id": task_id,
                "path": f"agent_requests/lane{lane}/{task_id}.request",
            }
        )
        planned_task_ids.add(task_id)

    return {
        "schema_version": 1,
        "owner": owner,
        "lanes": list(lanes),
        "retire": retire,
        "assign": assign,
    }


def validate_assignment_contracts(
    issues_by_number: dict[int, dict],
    assignments: list[dict],
    master_sha: str,
) -> None:
    _validate_master_sha(master_sha)
    for assignment in assignments:
        issue = issues_by_number[assignment["issue_number"]]
        validate_queued_issue(
            issue.get("state"),
            labels=sorted(_labels(issue)),
            is_pull_request=bool(issue.get("pull_request")),
        )
        task = extract_task_metadata(issue.get("body") or "")
        normalized = validate_task(
            task,
            issue_number=assignment["issue_number"],
            current_master_sha=master_sha,
            active_agent_count=0,
            labels=sorted(_labels(issue)),
            assignees=[],
        )
        if normalized["task_id"] != assignment["task_id"]:
            raise AgentDispatchError(
                f"Task id mismatch for issue #{assignment['issue_number']}."
            )


def _validate_master_sha(master_sha: str) -> None:
    if not isinstance(master_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", master_sha):
        raise AgentDispatchError("master_sha must be an explicitly supplied 40-char commit SHA.")


def summarize_runs(payload: object) -> dict:
    runs = payload.get("workflow_runs", []) if isinstance(payload, dict) else payload
    if not isinstance(runs, list):
        runs = []
    allowed = {
        "Autonomous Agent Request Queue",
        "Self-hosted Continuous QA",
        "Self-hosted Research Worker v4",
        "Copilot CLI CI Repair Worker",
        "Unified Research Orchestrator",
        "Wide Search Research Lane",
    }
    return {
        "recent_runs": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "status": r.get("status"),
                "conclusion": r.get("conclusion"),
                "head_sha": r.get("head_sha"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
            }
            for r in runs[:200]
            if r.get("name") in allowed
        ]
    }


def main() -> None:
    p = argparse.ArgumentParser()
    for name in ("issues", "requests", "branches", "runs"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--owner", required=True)
    p.add_argument("--master-sha", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    issues = json.loads(a.issues.read_text(encoding="utf-8"))
    requests = json.loads(a.requests.read_text(encoding="utf-8"))
    _validate_master_sha(a.master_sha)
    validate_request_snapshot(requests, lanes=("0", "1"))
    refs = json.loads(a.branches.read_text(encoding="utf-8"))
    runs = json.loads(a.runs.read_text(encoding="utf-8"))
    branches = {
        x.get("ref", "").removeprefix("refs/heads/")
        for x in refs
        if isinstance(x, dict) and x.get("ref")
    }

    decision = plan(
        issues=issues,
        requests=requests,
        existing_branches=branches,
        owner=a.owner,
    )
    by_number = {
        int(x["number"]): x
        for x in issues
        if str(x.get("number", "")).isdigit()
    }
    validate_assignment_contracts(by_number, decision["assign"], a.master_sha)
    decision.update(
        {
            "master_sha": a.master_sha,
            "telemetry": summarize_runs(runs),
            "eligible_issue_numbers": [
                int(x["number"]) for x in eligible_issues(issues, a.owner)
            ],
            "existing_agent_branches": sorted(
                x for x in branches if x.startswith("agent/")
            ),
        }
    )
    a.output.write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"CONTROL_PLANE_PLAN retire={len(decision['retire'])} "
        f"assign={len(decision['assign'])}"
    )


if __name__ == "__main__":
    main()
