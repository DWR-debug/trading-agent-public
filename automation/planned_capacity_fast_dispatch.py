"""Fast-path dispatch for executable dashboard capacity plans.

This is orchestration only: it dispatches already-defined workflows from the
current bounded dashboard plan, never creates new research hypotheses and never
authorizes performance, ranking, tuning, promotion or live execution.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

PLATFORM_NAMES = {
    "Resource Dashboard Update",
    "Current Operational Status Synchronizer",
    "Current Status Drift Guard",
    "Spine Next-Gate Autonomous Router",
    "Workflow Lint",
    "CI",
    "Full Suite Verification",
    "T052 Exact Master CI Gate",
    "Unified Research Orchestrator",
    "Planned Capacity Fast Dispatch",
}

TOP4_CANDIDATES = {"Q218", "Q219", "Q220", "Q221"}
SLOT_SCOPED_WORKFLOW = ".github/workflows/top4-candidate-slot-research.yml"


def active_research_items(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        x for x in snapshot.get("work_assignments", [])
        if isinstance(x, dict)
        and str(x.get("lane") or "") in {"FORMAL READINESS", "FRONTIER DISCOVERY"}
    ]


def active_workflow_paths(runs: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for run in runs:
        if not isinstance(run, dict) or run.get("status") == "completed":
            continue
        path = str(run.get("path") or run.get("workflow_path") or "")
        name = str(run.get("name") or run.get("workflow_name") or "")
        if name in PLATFORM_NAMES:
            continue
        if path:
            out.add(path)
    return out


def candidate_is_active(candidate: str, work: list[dict[str, Any]], *, exclude_resources: set[str] | None = None) -> bool:
    c = candidate.lower()
    excluded = exclude_resources or set()
    return any(
        x.get("resource") not in excluded
        and c in f"{x.get('task', '')} {x.get('job', '')}".lower()
        for x in work
    )


def slot_scopes(runs: list[dict[str, Any]], *, conclusion: str | None = None) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for run in runs:
        if not isinstance(run, dict) or run.get("status") != "completed":
            continue
        if conclusion is not None and run.get("conclusion") != conclusion:
            continue
        title = " ".join(str(run.get(key) or "") for key in ("name", "display_title", "run_name"))
        marker = "Top-4 Slot "
        if marker not in title:
            continue
        scope = title.split(marker, 1)[1].strip().split()
        if len(scope) >= 2 and scope[0] in {"windows", "ubuntu_x64", "ubuntu_arm64"}:
            out.add((scope[0], scope[1]))
    return out


def completed_slot_scopes(runs: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return slot_scopes(runs, conclusion="success")


def slot_failure_counts(runs: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for run in runs:
        if not isinstance(run, dict) or run.get("status") != "completed" or run.get("conclusion") != "failure":
            continue
        title = " ".join(str(run.get(key) or "") for key in ("name", "display_title", "run_name"))
        marker = "Top-4 Slot "
        if marker not in title:
            continue
        scope = title.split(marker, 1)[1].strip().split()
        if len(scope) >= 2 and scope[0] in {"windows", "ubuntu_x64", "ubuntu_arm64"}:
            key = (scope[0], scope[1])
            counts[key] = counts.get(key, 0) + 1
    return counts


def workflow_is_active(workflow: str, paths: set[str], runs: list[dict[str, Any]]) -> bool:
    if workflow == SLOT_SCOPED_WORKFLOW:
        return False
    needle = workflow.rsplit("/", 1)[-1]
    if workflow in paths or needle in paths:
        return True
    return any(
        r.get("status") != "completed"
        and (
            str(r.get("path") or "").endswith(needle)
            or str(r.get("workflow_path") or "").endswith(needle)
        )
        for r in runs
    )


def dispatch_candidates(snapshot: dict[str, Any], runs: list[dict[str, Any]], max_dispatches: int = 4) -> dict[str, Any]:
    planned = []
    for row in snapshot.get("planned_capacity", []):
        resource = str(row.get("resource") or "")
        current = int(row.get("current_assignments") or 0)
        slots = max(1, int(row.get("research_capacity_slots") or 1))
        resource_free = current < slots
        for item in row.get("planned_assignments", []):
            if not isinstance(item, dict) or not item.get("scheduled"):
                continue
            if not item.get("dispatchable"):
                continue
            workflow = item.get("execution_workflow")
            if not workflow:
                continue
            planned.append({
                "resource": resource,
                "resource_free": resource_free,
                **item,
            })

    # Prefer the canonical Top-4 cohort, then direct next-gate workflows,
    # while preserving the dashboard's deterministic order.
    rank = {"Q104:I19": -100, "Q218": 0, "Q219": 0, "Q220": 0, "Q221": 0, "Q224": 10, "Q228": 20, "Q231": 30}
    planned.sort(
        key=lambda x: (
            100 if str(x.get("execution_workflow") or "").endswith("ai-worker-fabric.yml") else 0,
            rank.get(str(x.get("candidate")), 50),
            str(x.get("plan_id") or ""),
        )
    )

    work = active_research_items(snapshot)
    active_paths = active_workflow_paths(runs)
    completed_slots = completed_slot_scopes(runs)
    failure_counts = slot_failure_counts(runs)
    zero_active = len(work) == 0
    decisions = []
    dispatches = []
    seen_dispatch_keys: set[tuple[str, str, str]] = set()
    top4_candidate_active = any(
        any(
            c.lower() in f"{item.get('task', '')} {item.get('job', '')}".lower()
            and item.get("resource") != "Free AI pool"
            for item in work
        )
        for c in TOP4_CANDIDATES
    )

    for item in planned:
        workflow = str(item["execution_workflow"])
        candidate = str(item.get("candidate") or "")
        if not item["resource_free"]:
            decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_RESOURCE_BUSY"})
            continue

        # Top-4 is one bundled workflow. Never launch the cohort while any of
        # its candidates is already running; that would create duplicate work.
        if workflow.endswith("top4-candidate-research-capacity.yml"):
            if top4_candidate_active or workflow_is_active(workflow, active_paths, runs):
                decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_TOP4_ACTIVE_OR_DUPLICATE"})
                continue

        if not item.get("allow_parallel_with_candidate", False) and candidate_is_active(candidate, work, exclude_resources={"Free AI pool"}):
            decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_CANDIDATE_ACTIVE"})
            continue

        resource = str(item.get("resource") or "")
        dispatch_key = (workflow, candidate, resource) if workflow == SLOT_SCOPED_WORKFLOW else (workflow, "", "")
        if workflow == SLOT_SCOPED_WORKFLOW:
            resource_input = {"Windows self-hosted A":"windows","Windows self-hosted B":"windows","Windows self-hosted C":"windows","GitHub-hosted Ubuntu x64":"ubuntu_x64","GitHub-hosted ARM64":"ubuntu_arm64"}.get(resource)
            scope = (resource_input, candidate) if resource_input else None
            if scope and scope in completed_slots:
                decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_SLOT_ALREADY_COMPLETED"})
                continue
            failures = failure_counts.get(scope, 0) if scope else 0
            if failures >= 2:
                decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_SLOT_RETRY_EXHAUSTED"})
                continue
            if failures == 1:
                decisions.append({"plan_id": item.get("plan_id"), "decision": "SLOT_RETRY_PERMITTED"})
        if dispatch_key in seen_dispatch_keys:
            decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_DISPATCH_SCOPE_ALREADY_SELECTED"})
            continue

        if workflow_is_active(workflow, active_paths, runs):
            decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_WORKFLOW_ACTIVE"})
            continue

        if len(dispatches) >= max_dispatches:
            decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_DISPATCH_CAP"})
            continue

        inputs = dict(item.get("execution_workflow_inputs") or {})
        if workflow == SLOT_SCOPED_WORKFLOW:
            resource_input = {"Windows self-hosted A":"windows","Windows self-hosted B":"windows","Windows self-hosted C":"windows","GitHub-hosted Ubuntu x64":"ubuntu_x64","GitHub-hosted ARM64":"ubuntu_arm64"}.get(resource)
            if resource_input:
                inputs.update({"candidate": candidate, "resource": resource_input})
        dispatches.append({
            "plan_id": item.get("plan_id"),
            "candidate": candidate,
            "resource": resource,
            "workflow": workflow,
            "inputs": inputs,
            "exclusive_dispatch": bool(item.get("exclusive_dispatch", False)),
        })
        seen_dispatch_keys.add(dispatch_key)
        decisions.append({
            "plan_id": item.get("plan_id"),
            "decision": "DISPATCH",
            "mode": "ZERO_ACTIVE_FAST_PATH" if zero_active else "FILL_FREE_READY_CAPACITY",
        })
        if item.get("exclusive_dispatch", False) or workflow in {".github/workflows/q104-i19-13f-historical-identity-census.yml"}:
            break

    return {
        "schema_version": 1,
        "record_type": "planned_capacity_fast_dispatch",
        "zero_active_research_jobs": zero_active,
        "active_research_job_count": len(work),
        "planned_executable_count": len(planned),
        "dispatches": dispatches,
        "decisions": decisions,
        "max_dispatches": max_dispatches,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "paper_only": True,
    }


def run_dispatches(plan: dict[str, Any], repo: str) -> dict[str, Any]:
    results = []
    for item in plan.get("dispatches", []):
        workflow = str(item["workflow"])
        cmd = ["gh", "workflow", "run", workflow, "--repo", repo, "--ref", "master"]
        for key, value in (item.get("inputs") or {}).items():
            cmd.extend(["-f", f"{key}={value}"])
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
        results.append({
            "plan_id": item.get("plan_id"),
            "workflow": workflow,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        })
    plan["dispatch_results"] = results
    return plan


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", type=Path, required=True)
    ap.add_argument("--runs", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--max-dispatches", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    run_payload = json.loads(args.runs.read_text(encoding="utf-8"))
    runs = run_payload.get("workflow_runs", run_payload if isinstance(run_payload, list) else [])
    plan = dispatch_candidates(snapshot, runs, max_dispatches=max(1, args.max_dispatches))
    if not args.dry_run:
        plan = run_dispatches(plan, args.repo)
        if any(int(x.get("returncode", 1)) != 0 for x in plan.get("dispatch_results", [])):
            rc = 1
        else:
            rc = 0
    else:
        rc = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
