"""Fast-path dispatch for executable dashboard capacity plans.

This is orchestration only: it dispatches already-defined workflows from the
current bounded dashboard plan, never creates new research hypotheses and never
authorizes performance, ranking, tuning, promotion or live execution.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
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

FOCUS_CANDIDATES = {"Q104:I19", "Q218"}
TOP4_CANDIDATES = {"Q218", "Q219", "Q220", "Q221"}
TOP4_PRIORITY = ("Q218", "Q219", "Q220", "Q221")
SLOT_SCOPED_WORKFLOW = ".github/workflows/top4-candidate-slot-research.yml"


Q218_INDEPENDENT_WORKFLOW = ".github/workflows/q218-independent-architecture-pit-reproduction.yml"
Q218_GATE_NAMES = {"source", "event_pair"}


def gate_files_unchanged_since_run(run: dict[str, Any], gate: str) -> bool:
    """Fail closed unless the relevant Q218 gate implementation is unchanged."""
    head_sha = str(run.get("head_sha") or "")
    if not head_sha:
        return False
    if gate == "source":
        paths = ["automation/q218_sec_multichannel_source_gate.py"]
    elif gate == "event_pair":
        paths = ["automation/q218_sec_event_pair_lineage_gate.py"]
    else:
        return False
    try:
        proc = subprocess.run(
            ["git", "diff", "--quiet", head_sha, "HEAD", "--", *paths],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return proc.returncode == 0


def completed_q218_gates_for_current_context(runs: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for run in runs:
        if not isinstance(run, dict) or run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        title = " ".join(str(run.get(key) or "") for key in ("name", "display_title", "run_name"))
        if "Top-4 Slot " not in title or "Q218" not in title:
            continue
        parts = title.split("Top-4 Slot ", 1)[1].strip().split()
        if len(parts) < 3 or parts[2] not in Q218_GATE_NAMES:
            continue
        if gate_files_unchanged_since_run(run, parts[2]):
            out.add(parts[2])
    return out


def q218_independent_reproduction_current(runs: list[dict[str, Any]]) -> bool:
    for run in runs:
        if not isinstance(run, dict) or run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        title = " ".join(str(run.get(key) or "") for key in ("name", "display_title", "run_name"))
        if "Q218 Independent Architecture PIT Reproduction" not in title:
            continue
        head_sha = str(run.get("head_sha") or "")
        if not head_sha:
            continue
        try:
            proc = subprocess.run(
                [
                    "git", "diff", "--quiet", head_sha, "HEAD", "--",
                    "automation/q218_independent_architecture_pit_reproduction.py",
                    Q218_INDEPENDENT_WORKFLOW,
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError:
            continue
        if proc.returncode == 0:
            return True
    return False


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


def _candidate_key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def candidate_is_active(candidate: str, work: list[dict[str, Any]], *, exclude_resources: set[str] | None = None) -> bool:
    c = _candidate_key(candidate)
    excluded = exclude_resources or set()
    return any(
        x.get("resource") not in excluded
        and c in _candidate_key(f"{x.get('task', '')} {x.get('job', '')}")
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


TECHNICAL_FAILURE_CONCLUSIONS = {"failure", "startup_failure", "timed_out"}


def slot_failure_counts(runs: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for run in runs:
        if not isinstance(run, dict) or run.get("status") != "completed" or run.get("conclusion") not in TECHNICAL_FAILURE_CONCLUSIONS:
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


def workflow_failure_streaks(runs: list[dict[str, Any]]) -> dict[str, int]:
    """Count consecutive technical failures per workflow, resetting after a success."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        if not isinstance(run, dict) or run.get("status") != "completed":
            continue
        path = str(run.get("path") or run.get("workflow_path") or "")
        if not path:
            continue
        grouped.setdefault(path, []).append(run)

    streaks: dict[str, int] = {}
    for path, items in grouped.items():
        items.sort(key=lambda x: str(x.get("created_at") or x.get("updated_at") or ""))
        streak = 0
        for run in reversed(items):
            conclusion = str(run.get("conclusion") or "")
            if conclusion == "success":
                break
            if conclusion in TECHNICAL_FAILURE_CONCLUSIONS:
                streak += 1
                continue
            break
        streaks[path] = streak
        streaks[path.rsplit("/", 1)[-1]] = streak
    return streaks


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


def normalize_runs_payload(run_payload: Any) -> list[dict[str, Any]]:
    """Normalize the dispatcher snapshot payload into a run-record list."""
    if isinstance(run_payload, list):
        return [x for x in run_payload if isinstance(x, dict)]
    if isinstance(run_payload, dict):
        runs = run_payload.get("workflow_runs", [])
        return [x for x in runs if isinstance(x, dict)] if isinstance(runs, list) else []
    return []


def ai_task_completed_with_current_context(task_id: str, *, root: Path = Path(".")) -> bool:
    """Return True only when an AI task succeeded under the current task context."""
    if not task_id:
        return False
    task_path = root / "ai_requests" / f"{task_id}.json"
    state_path = root / "ops" / "ai_worker_state" / f"{task_id}__openrouter_free.json"
    if not task_path.is_file() or not state_path.is_file():
        return False
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if state.get("status") != "SUCCESS":
        return False
    previous = str(state.get("context_fingerprint") or "")
    if not previous:
        return False
    try:
        current = subprocess.check_output(
            [
                sys.executable,
                "-m",
                "automation.ai_worker_fabric",
                "--context-fingerprint",
                "--task",
                str(task_path),
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        return False
    return bool(current) and current == previous


def dispatch_candidates(snapshot: dict[str, Any], runs: list[dict[str, Any]], max_dispatches: int = 4) -> dict[str, Any]:
    planned = []
    for row in snapshot.get("planned_capacity", []):
        resource = str(row.get("resource") or "")
        current = int(row.get("current_assignments") or 0)
        slots = max(1, int(row.get("research_capacity_slots") or 1))
        reported_free = row.get("research_slots_free")
        resource_free = int(reported_free) > 0 if reported_free is not None else current < slots
        for item in row.get("planned_assignments", []):
            if not isinstance(item, dict) or not item.get("scheduled"):
                continue
            if not item.get("dispatchable"):
                continue
            candidate = str(item.get("candidate") or "")
            focus_candidates = set(str(x) for x in snapshot.get("focus_candidates", []) if x)
            if focus_candidates and candidate not in focus_candidates:
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
    rank = {"Q104:I19": -100, "Q218": 0}
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
    workflow_failure_streak = workflow_failure_streaks(runs)
    zero_active = len(work) == 0
    decisions = []
    dispatches = []
    seen_dispatch_keys: set[tuple[str, str, str, str]] = set()
    chosen_slot_scopes: set[tuple[str, str]] = set()
    active_slot_scopes: set[tuple[str, str, str]] = set()
    for run in runs:
        if not isinstance(run, dict) or run.get("status") == "completed":
            continue
        title = " ".join(str(run.get(key) or "") for key in ("name", "display_title", "run_name"))
        marker = "Top-4 Slot "
        if marker not in title:
            continue
        scope_parts = title.split(marker, 1)[1].strip().split()
        if len(scope_parts) >= 2 and scope_parts[0] in {"windows", "ubuntu_x64", "ubuntu_arm64"}:
            gate = scope_parts[2] if len(scope_parts) >= 3 else "all"
            active_slot_scopes.add((scope_parts[0], scope_parts[1], gate))
    leased_resources: set[str] = set()
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

        if candidate == "Q218" and str(item.get("plan_id") or "") == "Q218-INDEPENDENT-ARCH":
            q218_completed_gates = completed_q218_gates_for_current_context(runs)
            if not Q218_GATE_NAMES.issubset(q218_completed_gates):
                decisions.append({
                    "plan_id": item.get("plan_id"),
                    "decision": "SKIP_Q218_INDEPENDENT_PREREQUISITES_INCOMPLETE",
                    "completed_gates": sorted(q218_completed_gates),
                })
                continue
            if q218_independent_reproduction_current(runs):
                decisions.append({
                    "plan_id": item.get("plan_id"),
                    "decision": "SKIP_Q218_INDEPENDENT_ALREADY_COMPLETED_CURRENT_CONTEXT",
                })
                continue

        # Automatic candidate execution is hard-locked to the focused pair.
        focus_candidates = set(str(x) for x in snapshot.get("focus_candidates", []) if x)
        if focus_candidates and candidate not in focus_candidates:
            decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_FOCUS_LOCK"})
            continue

        if (
            not focus_candidates
            and workflow.endswith("top4-candidate-research-capacity.yml")
            and top4_candidate_active
        ):
            decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_TOP4_ACTIVE_OR_DUPLICATE"})
            continue

        if workflow == SLOT_SCOPED_WORKFLOW:
            resource_input = {
                "Windows self-hosted A": "windows",
                "Windows self-hosted B": "windows",
                "Windows self-hosted C": "windows",
                "GitHub-hosted Ubuntu x64": "ubuntu_x64",
                "GitHub-hosted ARM64": "ubuntu_arm64",
            }.get(resource)
            slot_inputs = dict(item.get("execution_workflow_inputs") or {})
            focus_wave = bool(slot_inputs.get("focus_wave"))
            gate = str(slot_inputs.get("gate") or "all")
            scope = (resource_input, candidate) if resource_input else None
            focused_active_scope = (resource_input, candidate, gate) if resource_input else None
            if focused_active_scope and focused_active_scope in active_slot_scopes:
                decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_FOCUSED_GATE_ACTIVE_OR_DUPLICATE"})
                continue
            if resource_input and (resource_input, candidate, "all") in active_slot_scopes and gate == "all":
                decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_SLOT_ACTIVE_OR_DUPLICATE"})
                continue

        if not item.get("allow_parallel_with_candidate", False) and candidate_is_active(candidate, work, exclude_resources={"Free AI pool"}):
            decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_CANDIDATE_ACTIVE"})
            continue

        resource = str(item.get("resource") or "")
        if resource in leased_resources:
            decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_RESOURCE_RESERVED_BY_MULTI_RESOURCE_RUN"})
            continue
        dispatch_gate = str((item.get("execution_workflow_inputs") or {}).get("gate") or "all")
        dispatch_key = (workflow, candidate, resource, dispatch_gate) if workflow == SLOT_SCOPED_WORKFLOW else (workflow, "", "", "")
        if workflow != SLOT_SCOPED_WORKFLOW:
            failures = workflow_failure_streak.get(workflow, workflow_failure_streak.get(workflow.rsplit("/", 1)[-1], 0))
            if failures >= 2:
                decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_WORKFLOW_TECHNICAL_RETRY_EXHAUSTED"})
                continue
            if failures == 1:
                decisions.append({"plan_id": item.get("plan_id"), "decision": "WORKFLOW_TECHNICAL_RETRY_PERMITTED"})
        if workflow == SLOT_SCOPED_WORKFLOW:
            resource_input = {"Windows self-hosted A":"windows","Windows self-hosted B":"windows","Windows self-hosted C":"windows","GitHub-hosted Ubuntu x64":"ubuntu_x64","GitHub-hosted ARM64":"ubuntu_arm64"}.get(resource)
            scope = (resource_input, candidate) if resource_input else None
            focus_wave = bool((item.get("execution_workflow_inputs") or {}).get("focus_wave"))
            q218_completed_gates = completed_q218_gates_for_current_context(runs) if candidate == "Q218" and focus_wave else set()
            if candidate == "Q218" and focus_wave and gate in q218_completed_gates:
                decisions.append({
                    "plan_id": item.get("plan_id"),
                    "decision": "SKIP_FOCUSED_GATE_ALREADY_COMPLETED_CURRENT_CONTEXT",
                    "gate": gate,
                })
                continue
            if scope and scope in completed_slots and not focus_wave:
                decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_SLOT_ALREADY_COMPLETED"})
                fallback = top4_slot_fallback(
                    resource,
                    candidate,
                    work,
                    runs,
                    completed_slots,
                    failure_counts,
                    chosen_slot_scopes,
                )
                if fallback and len(dispatches) < max_dispatches:
                    fallback_scope = (resource_input, fallback)
                    dispatch_key = (workflow, fallback, resource, str((item.get("execution_workflow_inputs") or {}).get("gate") or "all"))
                    if dispatch_key not in seen_dispatch_keys and fallback_scope not in completed_slots and failure_counts.get(fallback_scope, 0) < 2:
                        inputs = dict(item.get("execution_workflow_inputs") or {})
                        inputs.update({"candidate": fallback, "resource": resource_input})
                        dispatches.append({
                            "plan_id": f"{item.get('plan_id')}-BACKFILL-{fallback}",
                            "candidate": fallback,
                            "resource": resource,
                            "workflow": workflow,
                            "inputs": inputs,
                            "exclusive_dispatch": bool(item.get("exclusive_dispatch", False)),
                        })
                        seen_dispatch_keys.add(dispatch_key)
                        chosen_slot_scopes.add(fallback_scope)
                        decisions.append({
                            "plan_id": item.get("plan_id"),
                            "decision": "DISPATCH_SLOT_BACKFILL",
                            "fallback_candidate": fallback,
                            "mode": "FILL_FREE_READY_CAPACITY",
                        })
                continue
            failures = (failure_counts.get(scope, 0) if scope else 0) if not focus_wave else 0
            if failures >= 2:
                decisions.append({"plan_id": item.get("plan_id"), "decision": "SKIP_SLOT_RETRY_EXHAUSTED"})
                fallback = top4_slot_fallback(
                    resource,
                    candidate,
                    work,
                    runs,
                    completed_slots,
                    failure_counts,
                    chosen_slot_scopes,
                )
                if fallback and len(dispatches) < max_dispatches and scope:
                    fallback_scope = (resource_input, fallback)
                    dispatch_key = (workflow, fallback, resource, str((item.get("execution_workflow_inputs") or {}).get("gate") or "all"))
                    if (
                        dispatch_key not in seen_dispatch_keys
                        and fallback_scope not in completed_slots
                        and failure_counts.get(fallback_scope, 0) < 2
                    ):
                        inputs = dict(item.get("execution_workflow_inputs") or {})
                        inputs.update({"candidate": fallback, "resource": resource_input})
                        dispatches.append({
                            "plan_id": f"{item.get('plan_id')}-BACKFILL-{fallback}",
                            "candidate": fallback,
                            "resource": resource,
                            "workflow": workflow,
                            "inputs": inputs,
                            "exclusive_dispatch": bool(item.get("exclusive_dispatch", False)),
                        })
                        seen_dispatch_keys.add(dispatch_key)
                        chosen_slot_scopes.add(fallback_scope)
                        decisions.append({
                            "plan_id": item.get("plan_id"),
                            "decision": "DISPATCH_SLOT_BACKFILL",
                            "fallback_candidate": fallback,
                            "mode": "TECHNICAL_RETRY_EXHAUSTION_BACKFILL",
                        })
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
        if workflow.endswith("ai-worker-fabric.yml"):
            task_id = str(inputs.get("task_id") or "")
            if task_id and ai_task_completed_with_current_context(task_id):
                decisions.append({
                    "plan_id": item.get("plan_id"),
                    "decision": "SKIP_AI_TASK_ALREADY_COMPLETED_CURRENT_CONTEXT",
                })
                continue
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
        if workflow == SLOT_SCOPED_WORKFLOW:
            resource_input = {"Windows self-hosted A":"windows","Windows self-hosted B":"windows","Windows self-hosted C":"windows","GitHub-hosted Ubuntu x64":"ubuntu_x64","GitHub-hosted ARM64":"ubuntu_arm64"}.get(resource)
            if resource_input:
                chosen_slot_scopes.add((resource_input, candidate))
        for leased in (item.get("resource_leases") or []):
            leased_resources.add(str(leased))
        decisions.append({
            "plan_id": item.get("plan_id"),
            "decision": "DISPATCH",
            "mode": "ZERO_ACTIVE_FAST_PATH" if zero_active else "FILL_FREE_READY_CAPACITY",
        })
        # Multi-resource exclusivity is enforced by explicit resource leases above,
        # not by stopping the entire dispatch pulse. Other free resources may fill now.

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


def top4_slot_fallback(
    resource: str,
    skipped_candidate: str,
    work: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    completed_slots: set[tuple[str, str]],
    failure_counts: dict[tuple[str, str], int],
    chosen_scopes: set[tuple[str, str]],
) -> str | None:
    """Choose the next uncompleted Top-4 candidate for a now-free slot."""
    resource_input = {
        "Windows self-hosted A": "windows",
        "Windows self-hosted B": "windows",
        "Windows self-hosted C": "windows",
        "GitHub-hosted Ubuntu x64": "ubuntu_x64",
        "GitHub-hosted ARM64": "ubuntu_arm64",
    }.get(resource)
    if not resource_input or skipped_candidate not in TOP4_CANDIDATES:
        return None
    start = TOP4_PRIORITY.index(skipped_candidate) + 1 if skipped_candidate in TOP4_PRIORITY else 0
    for candidate in TOP4_PRIORITY[start:]:
        scope = (resource_input, candidate)
        if scope in completed_slots or scope in chosen_scopes:
            continue
        if failure_counts.get(scope, 0) >= 2:
            continue
        if candidate_is_active(candidate, work, exclude_resources={"Free AI pool"}):
            continue
        return candidate
    return None


def run_dispatches(plan: dict[str, Any], repo: str) -> dict[str, Any]:
    results = []
    for item in plan.get("dispatches", []):
        workflow = str(item["workflow"])
        cmd = ["gh", "workflow", "run", workflow, "--repo", repo, "--ref", "master"]
        for key, value in (item.get("inputs") or {}).items():
            serialized = str(value).lower() if isinstance(value, bool) else str(value)
            cmd.extend(["-f", f"{key}={serialized}"])
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
    ap.add_argument("--max-dispatches", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    run_payload = json.loads(args.runs.read_text(encoding="utf-8"))
    runs = normalize_runs_payload(run_payload)
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
