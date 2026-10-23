"""Build the fast-dispatch plan from canonical state and live Actions jobs, not the dashboard artifact.

The dashboard remains a display. This controller reuses the canonical candidate/gate planner
but obtains current occupancy directly from in-progress Actions job records.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation import generate_resource_dashboard as dashboard

ROOT = Path(__file__).resolve().parents[1]
WINDOWS_RUNNERS = {
    "lht-n133732": "Windows self-hosted A",
    "lht-n133732-2": "Windows self-hosted B",
    "lht-n133732-3": "Windows self-hosted C",
}
WINDOWS_LABELS = {"trading-agent-research", "trading-agent-long"}
MAX_ACTIVE_RUNS_TO_INSPECT = 100
GH_API_ATTEMPTS = 3


def normalize_runs(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("workflow_runs", [])
    else:
        rows = []
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def fetch_one_run_jobs(repo: str, run: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch the job-level state for one actually in-progress workflow run."""
    run_id = run.get("id")
    if run_id is None:
        raise ValueError("ACTIVE_RUN_ID_MISSING")
    endpoint = f"/repos/{repo}/actions/runs/{int(run_id)}/jobs?per_page=100"
    last_error = "unknown"
    for attempt in range(1, GH_API_ATTEMPTS + 1):
        proc = subprocess.run(
            ["gh", "api", endpoint],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if proc.returncode == 0:
            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                last_error = f"INVALID_JSON:{type(exc).__name__}"
            else:
                if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
                    last_error = "JOBS_LIST_MISSING"
                elif int(payload.get("total_count") or 0) > len(payload["jobs"]):
                    last_error = "ACTIVE_JOB_PAGE_INCOMPLETE"
                else:
                    out: list[dict[str, Any]] = []
                    workflow_name = str(run.get("name") or run.get("display_title") or "")
                    workflow_path = str(run.get("path") or run.get("workflow_path") or "")
                    for job in payload["jobs"]:
                        if not isinstance(job, dict) or str(job.get("status") or "").lower() != "in_progress":
                            continue
                        runner_name = str(job.get("runner_name") or "").strip()
                        labels = {
                            str(label).strip().lower()
                            for label in job.get("labels", [])
                            if str(label).strip()
                        }
                        self_hosted_windows = (
                            bool(labels.intersection(WINDOWS_LABELS))
                            or ("self-hosted" in labels and "windows" in labels)
                        )
                        if self_hosted_windows and runner_name.lower() not in WINDOWS_RUNNERS:
                            raise RuntimeError(
                                "ACTIVE_WINDOWS_JOB_RUNNER_IDENTITY_UNRESOLVED:"
                                f"run={run_id}:job={job.get('id')}:runner={runner_name or 'missing'}"
                            )
                        out.append({
                            **job,
                            "run_id": int(run_id),
                            "run_url": run.get("html_url"),
                            "workflow_name": workflow_name,
                            "workflow_path": workflow_path,
                            "event": run.get("event"),
                            "actor": (run.get("actor") or {}).get("login") if isinstance(run.get("actor"), dict) else None,
                        })
                    return out
        else:
            last_error = f"GH_API_EXIT_{proc.returncode}:{(proc.stderr or '').strip()[:250]}"
        if attempt < GH_API_ATTEMPTS:
            time.sleep(attempt)
    raise RuntimeError(f"ACTIVE_RUN_JOBS_UNVERIFIED:{run_id}:{last_error}")


def fetch_active_jobs(repo: str, runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only an in-progress job assigned to a runner counts as slot occupancy."""
    active_runs = [
        run for run in runs
        if str(run.get("status") or "").lower() == "in_progress" and run.get("id") is not None
    ]
    active_runs = list({int(run["id"]): run for run in active_runs}.values())
    if len(active_runs) > MAX_ACTIVE_RUNS_TO_INSPECT:
        raise RuntimeError(f"ACTIVE_RUN_COUNT_EXCEEDS_BOUND:{len(active_runs)}")
    if not active_runs:
        return []

    all_jobs: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(8, len(active_runs))) as pool:
        futures = {pool.submit(fetch_one_run_jobs, repo, run): run for run in active_runs}
        for future in as_completed(futures):
            run = futures[future]
            try:
                all_jobs.extend(future.result())
            except Exception as exc:
                raise RuntimeError(f"ACTIVE_JOB_SNAPSHOT_INCOMPLETE:{run.get('id')}:{exc}") from exc
    return sorted(all_jobs, key=lambda job: (int(job.get("run_id") or 0), int(job.get("id") or 0)))


def work_from_active_jobs(runs: list[dict[str, Any]], active_jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create occupancy assignments exclusively from job records with status=in_progress."""
    run_by_id = {
        int(run["id"]): run
        for run in runs
        if isinstance(run, dict) and run.get("id") is not None
    }
    work: list[dict[str, Any]] = []
    for job in active_jobs:
        if not isinstance(job, dict) or str(job.get("status") or "").lower() != "in_progress":
            continue
        run = run_by_id.get(int(job.get("run_id") or 0), {})
        workflow = str(job.get("workflow_name") or run.get("name") or run.get("display_title") or "")
        job_name = str(job.get("name") or "")
        runner_name = str(job.get("runner_name") or "").strip()
        resource = dashboard.infer_resource(workflow, job_name, runner_name or None)
        lane = dashboard.infer_lane(workflow, job_name, run.get("event"))
        work.append({
            "resource": resource,
            "lane": lane,
            "worker": runner_name or "runner identity not published",
            "runner_name": runner_name or None,
            "job": job_name,
            "task": workflow,
            "status": "in_progress",
            "job_status": "in_progress",
            "run_status": "in_progress",
            "run_started_at": run.get("run_started_at"),
            "started_at": job.get("started_at") or run.get("run_started_at"),
            "actor": job.get("actor") or run.get("actor"),
            "run_id": job.get("run_id"),
            "job_id": job.get("id"),
            "run_url": job.get("run_url") or run.get("html_url"),
            "authority": "non-authorizing observed active job",
        })
    return work


def configured_resources(os_state: dict[str, Any]) -> list[dict[str, Any]]:
    policy = dashboard.configured_windows_availability_policy(os_state)
    return [
        {"name": "Windows self-hosted A", "type": "physical", "availability_policy": policy, "research_capacity_slots": 1, "role": "Formal readiness / local reproduction", "configured_runner": "LHT-N133732", "authority": "bounded capacity; no automatic performance authorization"},
        {"name": "Windows self-hosted B", "type": "physical", "availability_policy": policy, "research_capacity_slots": 1, "role": "Frontier discovery / data QA", "configured_runner": "LHT-N133732-2", "authority": "bounded capacity; no automatic performance authorization"},
        {"name": "Windows self-hosted C", "type": "physical", "availability_policy": policy, "research_capacity_slots": 1, "role": "Long deterministic runs / independent reproduction", "configured_runner": "LHT-N133732-3", "authority": "bounded capacity; no automatic performance authorization"},
        {"name": "GitHub-hosted Ubuntu x64", "type": "cloud", "research_capacity_slots": 2, "role": "Deterministic frontier, CI, source/PIT workflows", "configured_runner": "ubuntu-24.04", "authority": "non-authorizing operational capacity"},
        {"name": "GitHub-hosted ARM64", "type": "cloud", "research_capacity_slots": 2, "role": "Architecture-diverse CI / reproduction", "configured_runner": "ubuntu-24.04-arm", "authority": "non-authorizing operational capacity"},
        {"name": "Free AI pool", "type": "cloud", "research_capacity_slots": 1, "role": "Adversarial / design / engineering review", "configured_runner": "OpenRouter Free / Groq Free / Gemini / Mistral", "authority": "AI output never authorizes performance or promotion"},
    ]


def compile_direct_snapshot(
    runs: list[dict[str, Any]],
    active_jobs: list[dict[str, Any]],
    *,
    evidence: dict[str, Any] | None = None,
    os_state: dict[str, Any] | None = None,
    master_sha: str | None = None,
) -> dict[str, Any]:
    """Compile the same receipt-gated plan without generating or reading dashboard_data.json."""
    if evidence is None:
        evidence = json.loads((ROOT / "research/evidence/current_operational_state.json").read_text(encoding="utf-8"))
    if os_state is None:
        os_state = json.loads((ROOT / "ops/trading_agent_os_state.json").read_text(encoding="utf-8"))
    safety = os_state.get("permanent_safety", {})
    if not (
        safety.get("PAPER_ONLY") is True
        and safety.get("LIVE_TRADING_ENABLED") is False
        and safety.get("ORDERS_ENABLED") is False
        and safety.get("AUTOMATIC_PROMOTION") is False
    ):
        raise RuntimeError("PERMANENT_SAFETY_BOUNDARY_MISSING_OR_CHANGED")

    state_board = dashboard.expanded_candidate_board(
        evidence, os_state, dashboard.research_board(evidence, os_state)
    )
    top4_codes = set(dashboard.FOCUS_CANDIDATES) | set(dashboard.TOP4_CANDIDATES)
    top4 = [candidate for candidate in state_board if str(candidate.get("code")) in top4_codes]
    q104_parent = next((row for row in state_board if str(row.get("code")) == "104"), None)
    if q104_parent:
        nested = q104_parent.get("candidate_contracts")
        if isinstance(nested, dict):
            nested_i19 = nested.get("Q104:I19")
            if isinstance(nested_i19, dict) and not any(str(row.get("code")) == "Q104:I19" for row in top4):
                top4.insert(0, {
                    "code": "Q104:I19",
                    "state": str(q104_parent.get("state") or "not recorded"),
                    "lane": "FORMAL READINESS",
                    "issue_number": q104_parent.get("issue_number"),
                    "next_gate": str(nested_i19.get("next_gate") or "not recorded"),
                    "performance_authorization_allowed": bool(nested_i19.get("performance_authorization_allowed", False)),
                })

    work = work_from_active_jobs(runs, active_jobs)
    resources = dashboard.enrich_resources(configured_resources(os_state), [], work)
    plan = dashboard.planned_capacity_plan(
        resources,
        work,
        top4,
        {},
        os_state,
        recent_runs=runs,
    )
    running_by_runner = {
        str(job.get("runner_name") or "").lower(): {
            "job_id": job.get("id"),
            "run_id": job.get("run_id"),
            "workflow": job.get("workflow_name"),
            "job": job.get("name"),
            "run_url": job.get("run_url"),
        }
        for job in active_jobs
        if str(job.get("status") or "").lower() == "in_progress"
        and str(job.get("runner_name") or "").lower() in WINDOWS_RUNNERS
    }
    slots = {}
    for runner_key, resource_name in WINDOWS_RUNNERS.items():
        occupied = runner_key in running_by_runner
        slots[resource_name] = {
            "runner_name": runner_key,
            "status": "OCCUPIED_BY_RUNNING_JOB" if occupied else "ROUTABLE_NO_RUNNING_JOB_OBSERVED",
            "occupied": occupied,
            "active_job": running_by_runner.get(runner_key),
        }

    return {
        "schema_version": 1,
        "record_type": "direct_research_dispatch_snapshot",
        "status": "DIRECT_SNAPSHOT_READY",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "master_sha": master_sha or dashboard.git_head(),
        "decision_source": "canonical operational evidence + ops policy + fresh GitHub Actions run/job records",
        "dashboard_is_display_only": True,
        "dashboard_artifact_used_as_input": False,
        "runs_observed": len(runs),
        "in_progress_runs_inspected": len({int(run["id"]) for run in runs if run.get("id") is not None and str(run.get("status") or "").lower() == "in_progress"}),
        "active_jobs_observed": len(active_jobs),
        "windows_slot_occupancy": slots,
        "resources": resources,
        "work_assignments": work,
        "planned_capacity": plan,
        "planner_suppression_reasons": (
            list(plan[0].get("planner_suppression_reasons") or [])
            if plan and isinstance(plan[0], dict) else []
        ),
        "focus_candidates": list(dashboard.FOCUS_CANDIDATES),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repo != "DWR-debug/trading-agent-public":
        raise RuntimeError("UNEXPECTED_REPOSITORY")
    run_payload = json.loads(args.runs.read_text(encoding="utf-8"))
    runs = normalize_runs(run_payload)
    if not runs:
        raise RuntimeError("WORKFLOW_RUN_SNAPSHOT_EMPTY")
    current_run_id = os.environ.get("GITHUB_RUN_ID")
    if current_run_id and not any(
        str(run.get("id")) == current_run_id
        and str(run.get("status") or "").lower() == "in_progress"
        for run in runs
    ):
        raise RuntimeError("CURRENT_DISPATCH_RUN_NOT_PRESENT_IN_RUN_SNAPSHOT")
    active_jobs = fetch_active_jobs(args.repo, runs)
    snapshot = compile_direct_snapshot(runs, active_jobs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": snapshot["status"],
        "master_sha": snapshot["master_sha"],
        "windows_slot_occupancy": snapshot["windows_slot_occupancy"],
        "active_jobs_observed": snapshot["active_jobs_observed"],
        "planned_capacity_count": len(snapshot["planned_capacity"]),
        "dashboard_artifact_used_as_input": snapshot["dashboard_artifact_used_as_input"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
