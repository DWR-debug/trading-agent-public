"""Deterministic technical control-plane planning for bounded agent resources.

The control plane only plans queue routing and operational telemetry.
It never selects research candidates, changes evidence or gates, promotes work,
or executes live trading.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from automation.agent_dispatch import AgentDispatchError, extract_task_metadata, validate_task


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
        if issue.get("pull_request") or "agent-cli-ready" not in _labels(issue) or issue.get("assignees"):
            continue
        if _task_id(issue) is None:
            continue
        out.append(issue)
    return sorted(
        out,
        key=lambda x: (str(x.get("created_at") or ""), int(x.get("number") or 0)),
    )


def request_index(requests: list[dict]) -> dict[str, dict]:
    return {
        x["task_id"]: x
        for x in requests
        if isinstance(x.get("task_id"), str) and x["task_id"].strip()
    }


def plan(
    *,
    issues: list[dict],
    requests: list[dict],
    existing_branches: set[str],
    owner: str,
    lanes: tuple[str, ...] = ("0", "1"),
) -> dict:
    indexed = request_index(requests)
    retire = []
    active = {}

    for request in requests:
        task_id = request.get("task_id")
        lane = str(request.get("lane", ""))
        path = request.get("path")
        if not isinstance(task_id, str) or lane not in lanes:
            continue
        if not isinstance(path, str) or not path:
            continue
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

    for issue in eligible_issues(issues, owner):
        task_id = _task_id(issue)
        branch = f"agent/{task_id}-copilot-cli" if task_id else ""
        if (
            not task_id
            or task_id in indexed
            or task_id in active
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
    for assignment in assignments:
        issue = issues_by_number[assignment["issue_number"]]
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
