from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
OUT = ROOT / "docs" / "dashboard" / "dashboard_data.json"
BOOTSTRAP = ROOT / "docs" / "dashboard" / "dashboard_bootstrap.js"
REPO = os.environ.get("GITHUB_REPOSITORY", "DWR-debug/trading-agent-public")

def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

def recent_research_highlights(status_text: str) -> list[str]:
    lines = []
    for line in status_text.splitlines():
        stripped = line.strip()
        if (stripped.startswith("- **Q") or stripped.startswith("- Q")) and any(
            token in stripped for token in ("SOURCE", "PIT", "RESEARCH", "PERFORMANCE", "COMPLETED", "BLOCKED", "FALSIFIED", "FEASIBILITY")
        ):
            lines.append(stripped.lstrip("- ").strip())
    return lines[-18:]

def candidate_highlights(state: dict) -> list[dict]:
    registry = state.get("active_research_registry", [])
    if not isinstance(registry, list):
        return []
    out = []
    for item in registry[-20:]:
        if isinstance(item, dict) and item.get("code") and item.get("state"):
            out.append({
                "code": str(item["code"]),
                "state": str(item["state"]),
                "performance_authorization_allowed": bool(item.get("performance_authorization_allowed", False)),
            })
    return out



def flatten_registry(state: dict[str, Any]) -> list[dict[str, Any]]:
    registry = state.get("active_research_registry", {})
    if isinstance(registry, dict):
        registry = registry.get("active_design_families", [])
    if not isinstance(registry, list):
        return []
    return [x for x in registry if isinstance(x, dict) and x.get("code") and x.get("state")]


def research_board(state: dict[str, Any], os_state: dict[str, Any]) -> list[dict[str, Any]]:
    items = flatten_registry(state)
    priority_items = os_state.get("frontier_status_2026_10_04", {}).get("priority_order", [])
    priority_map = {
        str(item.get("candidate")): str(item.get("next_gate") or "")
        for item in priority_items
        if isinstance(item, dict) and item.get("candidate")
    }
    out = []
    for item in items:
        code = str(item["code"])
        next_gate = str(item.get("next_gate") or item.get("note") or "")
        next_gate = priority_map.get(code, next_gate)
        if code in {"104", "105", "106", "107", "108", "109", "110", "111", "112", "113", "114", "115", "116", "117", "118", "119", "120", "121", "Q121-R1", "Q121-R2"}:
            lane = "FORMAL READINESS"
        elif code in {"084", "088", "082"}:
            lane = "LEGACY / FEASIBILITY"
        else:
            lane = "FRONTIER DISCOVERY"
        out.append({
            "code": code,
            "state": str(item["state"]),
            "lane": lane,
            "issue_number": item.get("issue_number"),
            "next_gate": next_gate,
            "performance_authorization_allowed": bool(item.get("performance_authorization_allowed", False)),
        })
    return out[-40:]


def run_cmd_json(args: list[str]) -> dict[str, Any] | list[Any] | None:
    try:
        env = os.environ.copy()
        token = env.get("GITHUB_TOKEN") or env.get("GH_TOKEN") or ""
        if not token:
            return None
        env["GH_TOKEN"] = token
        raw = subprocess.check_output(
            ["gh", "api", *args],
            cwd=ROOT,
            text=True,
            env=env,
            stderr=subprocess.DEVNULL,
        )
        return json.loads(raw)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def run_duration_seconds(run: dict[str, Any]) -> int | None:
    started = parse_dt(run.get("run_started_at") or run.get("created_at"))
    finished = parse_dt(run.get("completed_at") or run.get("updated_at"))
    if not started or not finished or finished < started:
        return None
    return max(0, int((finished - started).total_seconds()))


def median(values: list[int]) -> int | None:
    if not values:
        return None
    values = sorted(values)
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return int(round((values[middle - 1] + values[middle]) / 2))


def percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    values = sorted(values)
    index = min(len(values) - 1, max(0, int(round((len(values) - 1) * fraction))))
    return values[index]


def duration_benchmarks(runs: list[dict[str, Any]], max_samples_per_workflow: int = 20) -> dict[str, dict[str, int | str]]:
    grouped: dict[str, list[int]] = {}
    counts: dict[str, int] = {}
    for run in runs:
        if not isinstance(run, dict) or run.get("status") != "completed":
            continue
        if run.get("conclusion") == "cancelled":
            continue
        name = str(run.get("name") or "")
        duration = run_duration_seconds(run)
        if not name or duration is None:
            continue
        values = grouped.setdefault(name, [])
        if len(values) < max_samples_per_workflow:
            values.append(duration)
        counts[name] = counts.get(name, 0) + 1
    out: dict[str, dict[str, int | str]] = {}
    for name, values in grouped.items():
        out[name] = {
            "p50_seconds": median(values) or 0,
            "p90_seconds": percentile(values, 0.90) or 0,
            "sample_count": len(values),
            "source": "recent completed runs; cancelled runs excluded",
        }
    return out


def job_duration_benchmarks(
    runs: list[dict[str, Any]],
    workflow_name: str = "Top-4 Candidate Research Capacity",
    recent_runs: int = 6,
) -> dict[str, dict[str, int | str]]:
    samples: dict[str, list[int]] = {}
    selected = [r for r in runs if isinstance(r, dict) and r.get("name") == workflow_name and r.get("status") == "completed"]
    for run in selected[:recent_runs]:
        for job in jobs_for_run(int(run["id"])) if run.get("id") else []:
            if job.get("status") != "completed" or job.get("conclusion") == "cancelled":
                continue
            started = parse_dt(job.get("started_at"))
            finished = parse_dt(job.get("completed_at"))
            if not started or not finished or finished < started:
                continue
            duration = max(0, int((finished - started).total_seconds()))
            job_name = str(job.get("name") or "")
            for candidate in ("Q104:I19", "Q218", "Q219", "Q220", "Q221"):
                if candidate in job_name:
                    samples.setdefault(candidate, []).append(duration)
                    break
    return {
        candidate: {
            "p50_seconds": median(values) or 0,
            "p90_seconds": percentile(values, 0.90) or 0,
            "sample_count": len(values),
            "source": "Top-4 candidate job history; cancelled jobs excluded",
        }
        for candidate, values in samples.items()
    }


def runner_snapshot() -> list[dict[str, Any]]:
    data = run_cmd_json([f"/repos/{REPO}/actions/runners?per_page=100"])
    if not isinstance(data, dict):
        return []
    return [
        {
            "id": r.get("id"),
            "name": r.get("name"),
            "status": r.get("status"),
            "busy": bool(r.get("busy", False)),
            "labels": [x.get("name") for x in r.get("labels", []) if isinstance(x, dict) and x.get("name")],
            "os": r.get("os"),
            "architecture": r.get("architecture"),
        }
        for r in data.get("runners", [])
        if isinstance(r, dict)
    ]


def jobs_for_run(run_id: int) -> list[dict[str, Any]]:
    data = run_cmd_json([f"/repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100"])
    if not isinstance(data, dict):
        return []
    return [x for x in data.get("jobs", []) if isinstance(x, dict)]


def infer_lane(workflow: str, job: str = "") -> str:
    text = f"{workflow} {job}".lower()
    if any(k in text for k in ("q104", "q121", "formal readiness", "authorization readiness")):
        return "FORMAL READINESS"
    if any(k in text for k in (
        "q119", "q120", "q126", "q127", "q128", "q129", "q130", "q131", "q132",
        "q171", "q172", "q173", "q174", "q175", "q176", "q177", "q178",
        "q179", "q180", "q181", "q182", "q183", "q184", "q185", "q186",
        "q187", "q188", "q189", "q190", "q191", "q192", "q193", "q194",
        "q195", "q196", "q197", "q198", "q199", "q201", "q202", "q203",
        "q204", "q205", "q218", "q219", "q220", "q221", "frontier"
    )):
        return "FRONTIER DISCOVERY"
    return "PLATFORM / GOVERNANCE"


def infer_resource(workflow: str, job: str, runner: str | None) -> str:
    rn = (runner or "").lower()
    wt = f"{workflow} {job}".lower()
    if rn == "lht-n133732":
        return "Windows self-hosted A"
    if rn == "lht-n133732-2":
        return "Windows self-hosted B"
    if rn == "lht-n133732-3":
        return "Windows self-hosted C"
    if "s10-termux" in rn:
        return "S10 / Android"
    if rn.startswith("samsung-phone-"):
        return "Samsung Android fleet"
    if "ubuntu-24.04-arm" in wt or "arm64" in wt:
        return "GitHub-hosted ARM64"
    if any(k in wt for k in ("free ai", "ai worker", "openrouter", "groq", "gemini", "mistral")):
        return "Free AI pool"
    if any(k in wt for k in ("resource dashboard", "github pages", "dashboard update")):
        return "Dashboard / GitHub Pages"
    if any(k in wt for k in ("ci", "full suite", "workflow lint", "t052")):
        return "GitHub-hosted CI"
    if any(k in wt for k in ("status synchronizer", "control plane", "agent request queue")):
        return "OS control plane"
    if "windows" in wt:
        return "Windows self-hosted"
    return "GitHub-hosted Ubuntu x64"


def current_work_from_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hidden_non_research = {
        "Resource Dashboard Update",
        "Current Operational Status Synchronizer",
        "Current Status Drift Guard",
        "Spine Next-Gate Autonomous Router",
        "Workflow Lint",
        "CI",
        "Full Suite Verification",
        "T052 Exact Master CI Gate",
        "Unified Research Orchestrator",
    }
    active = [
        x for x in runs
        if isinstance(x, dict)
        and x.get("status") in {"queued", "in_progress", "waiting", "pending"}
        and str(x.get("name") or "") not in hidden_non_research
    ]
    active.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    out: list[dict[str, Any]] = []
    job_budget = 60
    for run in active:
        workflow = str(run.get("name") or "")
        jobs = jobs_for_run(int(run["id"])) if job_budget and run.get("id") else []
        if jobs:
            job_budget -= 1
            jobs = [j for j in jobs if j.get("status") in {"queued", "in_progress", "waiting", "pending"}]
            for job in jobs:
                job_name = str(job.get("name") or "")
                lane = infer_lane(workflow, job_name)
                if lane == "PLATFORM / GOVERNANCE":
                    continue
                out.append({
                    "resource": infer_resource(workflow, job_name, job.get("runner_name")),
                    "lane": lane,
                    "worker": job.get("runner_name") or "pending runner assignment",
                    "job": job_name,
                    "task": workflow,
                    "status": run.get("status"),
                    "started_at": run.get("run_started_at") or run.get("created_at"),
                    "actor": (run.get("actor") or {}).get("login"),
                    "run_id": run.get("id"),
                    "run_url": run.get("html_url"),
                    "authority": "non-authorizing operational work",
                })
        else:
            lane = infer_lane(workflow)
            if lane == "PLATFORM / GOVERNANCE":
                continue
            out.append({
                "resource": infer_resource(workflow, "", None),
                "lane": lane,
                "worker": "pending runner assignment",
                "job": "",
                "task": workflow,
                "status": run.get("status"),
                "started_at": run.get("run_started_at") or run.get("created_at"),
                "actor": (run.get("actor") or {}).get("login"),
                "run_id": run.get("id"),
                "run_url": run.get("html_url"),
                "authority": "non-authorizing operational work",
            })
        if len(out) >= 36:
            break
    return out

def enrich_work_durations(
    work: list[dict[str, Any]],
    workflow_benchmarks: dict[str, dict[str, int | str]],
    job_benchmarks: dict[str, dict[str, int | str]],
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    out = []
    for item in work:
        workflow = str(item.get("task") or "")
        candidate = next((c for c in ("Q218", "Q219", "Q220", "Q221") if c in f"{workflow} {item.get('job', '')}"), None)
        benchmark = job_benchmarks.get(candidate) if workflow == "Top-4 Candidate Research Capacity" else workflow_benchmarks.get(workflow)
        entry = dict(item)
        expected = int(benchmark["p50_seconds"]) if benchmark and benchmark.get("p50_seconds") else None
        entry["expected_duration_seconds"] = expected
        entry["duration_sample_count"] = int(benchmark["sample_count"]) if benchmark else 0
        entry["duration_source"] = str(benchmark["source"]) if benchmark else "no benchmark available"
        started = parse_dt(entry.get("started_at"))
        elapsed = max(0, int((now - started).total_seconds())) if started else 0
        entry["elapsed_seconds"] = elapsed
        entry["remaining_seconds"] = max(0, expected - elapsed) if expected is not None and item.get("status") == "in_progress" else expected
        entry["expected_finish_at"] = (now + timedelta(seconds=entry["remaining_seconds"])).isoformat() if entry["remaining_seconds"] is not None else None
        out.append(entry)
    return out


def candidate_pipeline(
    top4: list[dict[str, Any]],
    work: list[dict[str, Any]],
    workflow_benchmarks: dict[str, dict[str, int | str]],
    job_benchmarks: dict[str, dict[str, int | str]],
) -> list[dict[str, Any]]:
    result = []
    active_by_candidate: dict[str, list[dict[str, Any]]] = {c: [] for c in ("Q104:I19", "Q218", "Q219", "Q220", "Q221")}
    for item in work:
        text_value = f"{item.get('task', '')} {item.get('job', '')}"
        for candidate in active_by_candidate:
            if candidate in text_value:
                active_by_candidate[candidate].append(item)
    for candidate in ("Q104:I19", "Q218", "Q219", "Q220", "Q221"):
        row = next((x for x in top4 if str(x.get("code")) == candidate), None)
        if not row:
            continue
        benchmark = job_benchmarks.get(candidate) if candidate != "Q218" else workflow_benchmarks.get("Q218 Event Pair PIT Gate")
        result.append({
            "code": candidate,
            "stage": str(row.get("state") or "not recorded"),
            "next_gate": str(row.get("next_gate") or "not recorded"),
            "issue_number": row.get("issue_number"),
            "active": bool(active_by_candidate[candidate]),
            "active_jobs": len(active_by_candidate[candidate]),
            "expected_duration_seconds": int(benchmark["p50_seconds"]) if benchmark else None,
            "duration_p90_seconds": int(benchmark["p90_seconds"]) if benchmark else None,
            "duration_sample_count": int(benchmark["sample_count"]) if benchmark else 0,
            "duration_source": str(benchmark["source"]) if benchmark else "no verified duration history",
            "performance_authorization_allowed": bool(row.get("performance_authorization_allowed", False)),
        })
    return result



def expanded_candidate_board(
    evidence: dict[str, Any],
    os_state: dict[str, Any],
    base_board: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    board = list(base_board)
    candidate_ids = []
    specs_path = ROOT / "research" / "candidates" / "orthogonal_candidate_specs_2026-10-04.json"
    try:
        specs = json.loads(specs_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        specs = {}
    for candidate in specs.get("candidates", []) if isinstance(specs, dict) else []:
        if isinstance(candidate, dict) and candidate.get("id") in {"Q202", "Q203", "Q204"}:
            candidate_ids.append(candidate["id"])

    receipt_path = ROOT / "research" / "evidence" / "q202_q204_information_timing_feasibility_latest.json"
    next_gate_path = ROOT / "research" / "evidence" / "orthogonal_next_gate_latest.json"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        receipt = {}
    try:
        next_gate = json.loads(next_gate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        next_gate = {}

    source_states = {
        str(x.get("candidate_id")): str(x.get("status"))
        for x in receipt.get("candidate_results", [])
        if isinstance(x, dict) and x.get("candidate_id")
    }
    next_gate_map = {
        str(x.get("candidate_id")): str(x.get("next_gate") or "")
        for x in next_gate.get("candidates", [])
        if isinstance(x, dict) and x.get("candidate_id")
    }

    for candidate_id in candidate_ids:
        spec = next((x for x in specs.get("candidates", []) if x.get("id") == candidate_id), {})
        board.append({
            "code": candidate_id,
            "state": source_states.get(candidate_id, "SOURCE/PIT STATUS NOT AVAILABLE"),
            "lane": "FRONTIER DISCOVERY",
            "issue_number": 1073,
            "next_gate": next_gate_map.get(candidate_id) or str((spec.get("gates") or ["historical PIT reconstruction"])[0]),
            "performance_authorization_allowed": False,
        })

    q205 = next((x for x in flatten_registry(evidence) if str(x.get("code")) == "Q205"), None)
    board = [x for x in board if x.get("code") != "Q205"]
    if q205:
        board.append({
            "code": "Q205",
            "state": str(q205.get("state")),
            "lane": "FRONTIER DISCOVERY",
            "issue_number": q205.get("issue_number"),
            "next_gate": str(q205.get("next_gate") or q205.get("note") or "historical PIT reconstruction"),
            "performance_authorization_allowed": bool(q205.get("performance_authorization_allowed", False)),
        })

    return board


def capacity_state(resource: dict[str, Any], runner: dict[str, Any] | None, assignments: list[dict[str, Any]]) -> str:
    if assignments or (runner and runner.get("busy")):
        return "operating"
    if runner and str(runner.get("status")).lower() == "online":
        return "available"
    if resource["type"] == "cloud":
        return "available"
    if resource["type"] == "service":
        return "available"
    return "unknown"


def enrich_resources(configured: list[dict[str, Any]], runners: list[dict[str, Any]], work: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    runner_by_name = {str(r.get("name")): r for r in runners}
    for resource in configured:
        assignments = [w for w in work if w.get("resource") == resource["name"]]
        runner = runner_by_name.get(resource["configured_runner"])
        state = capacity_state(resource, runner, assignments)
        if state == "operating":
            live_status = "operating"
        elif state == "available":
            live_status = "available"
        else:
            live_status = "unverified / not visible"
        out.append({
            **resource,
            "capacity_state": state,
            "live_status": live_status,
            "busy": state == "operating",
            "labels": runner.get("labels", []) if runner else [],
            "current_assignments": len(assignments),
            "research_capacity_slots": max(1, int(resource.get("research_capacity_slots", 1) or 1)),
            "research_slots_in_use": min(len(assignments), max(1, int(resource.get("research_capacity_slots", 1) or 1))),
            "research_slots_free": max(0, max(1, int(resource.get("research_capacity_slots", 1) or 1)) - len(assignments)),
            "current_tasks": [w.get("task") for w in assignments[:4]],
        })
    return out



def planned_capacity_plan(
    resources: list[dict[str, Any]],
    work: list[dict[str, Any]],
    top4: list[dict[str, Any]],
    job_benchmarks: dict[str, dict[str, int | str]],
    os_state: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compile a non-authorizing next-work plan from the real bounded backlog.

    The plan is intentionally conservative: active candidate work is excluded,
    blocked prerequisites are displayed as blocked rather than executable, and
    nothing is invented to occupy free capacity.
    """
    active_text = [f"{x.get('resource','')} {x.get('task','')} {x.get('job','')}".lower() for x in work]

    overlay = os_state.get("top_candidate_capacity_overlay", {})
    a_priority = [str(x) for x in overlay.get("windows_A", {}).get("priority", [])]
    b_priority = [str(x) for x in overlay.get("windows_B", {}).get("priority", [])]
    queue = [
        {
            "plan_id": "Q104-I19-CENSUS",
            "candidate": "Q104:I19",
            "lane": "FORMAL READINESS",
            "task": "historical SEC 13F archive/security identity census and acceptance-time closure",
            "preferred": ["Windows self-hosted A"],
            "readiness": "READY_HISTORICAL_13F_CENSUS",
            "basis": "the dedicated three-shard historical 13F census workflow is present and its next gate is receipt-defined; it internally uses Windows plus hosted x64/ARM64 shards",
            "dispatchable": True,
            "exclusive_dispatch": True,
            "execution_workflow": ".github/workflows/q104-i19-13f-historical-identity-census.yml",
        },
        {
            "plan_id": "Q104-I19-COMPILER",
            "candidate": "Q104:I19",
            "lane": "FORMAL READINESS",
            "task": "concept-specific PIT compiler after 13F acceptance-time join",
            "preferred": ["Windows self-hosted A", "GitHub-hosted Ubuntu x64"],
            "readiness": "BLOCKED_UNTIL_HISTORICAL_COMPILER_INPUTS",
            "basis": "historical 13F receipt remains the explicit compiler prerequisite",
            "dispatchable": False,
            "execution_workflow": None,
        },
        {
            "plan_id": "Q104-I19-INDEPENDENT-REPRO",
            "candidate": "Q104:I19",
            "lane": "FORMAL READINESS",
            "task": "independent reproduction of compiler/PIT result",
            "preferred": ["Windows self-hosted C", "GitHub-hosted ARM64"],
            "readiness": "BLOCKED_UNTIL_COMPILER_RECEIPT",
            "basis": "next gate explicitly requires independent reproduction",
            "dispatchable": False,
            "execution_workflow": None,
        },
        {
            "plan_id": "Q218-PIT",
"dispatchable": True,
            "execution_workflow": ".github/workflows/top4-candidate-slot-research.yml",
            "candidate": "Q218",
            "lane": "FRONTIER DISCOVERY",
            "task": "historical mandatory/voluntary 10-K → 8-K pairing and PIT lineage",
            "preferred": ["Windows self-hosted B", "GitHub-hosted Ubuntu x64"],
            "readiness": "READY_SOURCE_PIT",
            "basis": "current Q218 source/PIT workpack",
        },
        {
            "plan_id": "Q219-PIT",
            "candidate": "Q219",
            "lane": "FRONTIER DISCOVERY",
            "task": "post-filing options-response information-processing PIT join",
            "preferred": ["GitHub-hosted Ubuntu x64", "Windows self-hosted B"],
            "readiness": "READY_POST_FILING_PIT",
            "basis": "Q129 source/PIT fingerprint + fixed post-filing event-time join contract",
            "dispatchable": True,
            "execution_workflow": ".github/workflows/top4-candidate-slot-research.yml",
        },
        {
            "plan_id": "Q220-PIT",
"dispatchable": True,
            "execution_workflow": ".github/workflows/top4-candidate-slot-research.yml",
            "candidate": "Q220",
            "lane": "FRONTIER DISCOVERY",
            "task": "deterministic narrative/XBRL presentation mapping and PIT",
            "preferred": ["Windows self-hosted B", "GitHub-hosted ARM64"],
            "readiness": "READY_SOURCE_SCHEMA",
            "basis": "SEC FSN schema gate + XBRL concept-freeze audit",
        },
        {
            "plan_id": "Q221-PIT",
"dispatchable": True,
            "execution_workflow": ".github/workflows/top4-candidate-slot-research.yml",
            "candidate": "Q221",
            "lane": "FRONTIER DISCOVERY",
            "task": "historical USAspending public boundary and issuer/entity mapping",
            "preferred": ["GitHub-hosted Ubuntu x64", "Windows self-hosted B"],
            "readiness": "READY_SOURCE_CLOCK",
            "basis": "USAspending public-clock contract ready; applicability/entity mapping open",
        },
        {
            "plan_id": "Q224-EDGAR-LOG",
"dispatchable": True,
            "execution_workflow": ".github/workflows/q224-edgar-modern-source-gate.yml",
            "candidate": "Q224",
            "lane": "FRONTIER DISCOVERY",
            "task": "modern EDGAR access-log archive census and request→filing decoding",
            "preferred": ["Windows self-hosted B", "GitHub-hosted Ubuntu x64"],
            "readiness": "READY_DISCOVERY",
            "basis": "official EDGAR log channel; archive/schema/identity gate remains",
        },
        {
            "plan_id": "Q228-CORRESPONDENCE",
"dispatchable": True,
            "execution_workflow": ".github/workflows/q228-sec-correspondence-source-gate.yml",
            "candidate": "Q228",
            "lane": "FRONTIER DISCOVERY",
            "task": "historical SEC correspondence census, release clock and review identity",
            "preferred": ["Windows self-hosted B", "GitHub-hosted Ubuntu x64"],
            "readiness": "READY_DISCOVERY",
            "basis": "SEC correspondence source gate; selection mechanism remains a control",
        },
        {
            "plan_id": "Q231-FOIA",
"dispatchable": True,
            "execution_workflow": ".github/workflows/q231-sec-foia-source-gate.yml",
            "candidate": "Q231",
            "lane": "FRONTIER DISCOVERY",
            "task": "historical SEC FOIA publication clock and requester/issuer mapping",
            "preferred": ["GitHub-hosted Ubuntu x64", "Windows self-hosted B"],
            "readiness": "READY_DISCOVERY",
            "basis": "official monthly FOIA logs; exact publication clock still open",
        },
        {
            "plan_id": "Q220-ADVERSARIAL",
            "candidate": "Q220",
            "lane": "FRONTIER DISCOVERY",
            "task": "bounded adversarial contract review of Q220 source/PIT assumptions",
            "preferred": ["Free AI pool"],
            "readiness": "READY_AI_FABRIC",
            "basis": "independent adversarial review; Q218 provider attempt already failed and is not repeated merely for utilization",
            "allow_parallel_with_candidate": True,
            "dispatchable": True,
            "execution_workflow": ".github/workflows/ai-worker-fabric.yml",
            "execution_workflow_inputs": {"task_id": "AI-2026-10-06-Q220-TOP4-ADVERSARIAL", "run_secondary_provider": "false", "use_litellm_transport": "false"},
        },
        {
            "plan_id": "Q221-ADVERSARIAL",
            "candidate": "Q221",
            "lane": "FRONTIER DISCOVERY",
            "task": "bounded adversarial contract review of Q221 public-clock/entity-map assumptions",
            "preferred": ["Free AI pool"],
            "readiness": "READY_AI_FABRIC",
            "basis": "independent adversarial review; AI output is non-scientific and non-authorizing",
            "allow_parallel_with_candidate": True,
            "dispatchable": True,
            "execution_workflow": ".github/workflows/ai-worker-fabric.yml",
            "execution_workflow_inputs": {"task_id": "AI-2026-10-06-Q221-TOP4-ADVERSARIAL", "run_secondary_provider": "false", "use_litellm_transport": "false"},
        },
    ]

    def priority_bonus(item: dict[str, Any]) -> int:
        candidate = str(item.get("candidate"))
        if candidate == "Q104:I19" and any("Q104 I19" in x for x in a_priority):
            return -100
        if candidate in {x for x in b_priority}:
            return -50
        return 0

    # Each resource receives at most one next action. Existing active work blocks
    # that candidate globally to prevent dashboard planning from recommending duplicates.
    assigned_candidates: set[str] = set()
    plans: dict[str, list[dict[str, Any]]] = {str(r["name"]): [] for r in resources}

    for item in sorted(queue, key=lambda x: (priority_bonus(x), queue.index(x))):
        candidate = str(item["candidate"])
        candidate_active = any(candidate.lower() in value and "free ai" not in value for value in active_text)
        if candidate_active and not item.get("allow_parallel_with_candidate", False):
            continue
        if candidate in assigned_candidates and not item.get("allow_parallel_with_candidate", False):
            continue
        if item.get("plan_id") == "Q218-ADVERSARIAL" and any("free ai" in value and "q218" in value for value in active_text):
            continue
        if item.get("plan_id") == "Q221-ADVERSARIAL" and any("free ai" in value and "q221" in value for value in active_text):
            continue
        if item["readiness"].startswith("BLOCKED_"):
            continue
        placed = False
        for resource_name in item["preferred"]:
            resource = next((r for r in resources if str(r["name"]) == resource_name), None)
            if resource is None:
                continue
            capacity_slots = max(1, int(resource.get("research_capacity_slots", 1) or 1))
            if len(plans.get(resource_name, [])) >= capacity_slots:
                continue
            current_assignments = int(resource.get("current_assignments", 0) or 0)
            planned_for_resource = len(plans.get(resource_name, []))
            if current_assignments + planned_for_resource >= capacity_slots:
                continue
            benchmark = job_benchmarks.get(candidate)
            plans[resource_name].append({
                "plan_id": item["plan_id"],
                "candidate": candidate,
                "lane": item["lane"],
                "task": item["task"],
                "readiness": item["readiness"],
                "basis": item["basis"],
                "scheduled": True,
                "dispatchable": bool(item.get("dispatchable", False)),
                "execution_workflow": item.get("execution_workflow"),
                "execution_workflow_inputs": item.get("execution_workflow_inputs", {}),
                "execution_status": "planned_not_started",
                "dispatch_state": "READY_FOR_FAST_DISPATCH" if item.get("dispatchable", False) else "PLANNED_ADVISORY",
                "expected_duration_seconds": int(benchmark["p50_seconds"]) if benchmark else None,
                "duration_sample_count": int(benchmark["sample_count"]) if benchmark else 0,
            })
            assigned_candidates.add(candidate)
            placed = True
            break
        if placed:
            continue

    # Surface genuinely useful blocked follow-on capacity without presenting it as queued work.
    c_resource = "Windows self-hosted C"
    if c_resource in plans and not plans[c_resource] and not any("q104:i19" in value for value in active_text):
        plans[c_resource].append({
            "plan_id": "Q104-I19-INDEPENDENT-REPRO",
            "candidate": "Q104:I19",
            "lane": "FORMAL READINESS",
            "task": "independent reproduction of compiler/PIT result",
            "readiness": "BLOCKED_UNTIL_COMPILER_RECEIPT",
            "basis": "next gate explicitly requires independent reproduction",
            "scheduled": False,
            "dispatchable": False,
            "execution_workflow": None,
            "execution_workflow_inputs": {},
            "execution_status": "blocked_on_prerequisite",
            "expected_duration_seconds": None,
            "duration_sample_count": 0,
        })

    rows=[]
    for resource in resources:
        name=str(resource["name"])
        rows.append({
            "resource": name,
            "current_assignments": int(resource.get("current_assignments") or 0),
            "capacity_state": str(resource.get("capacity_state") or "unknown"),
            "planned_assignments": plans.get(name, []),
            "planned_count": sum(1 for x in plans.get(name, []) if x.get("scheduled")),
            "blocked_count": sum(1 for x in plans.get(name, []) if not x.get("scheduled")),
            "unallocated_reason": None if plans.get(name) else "no independent ready non-duplicate work assigned by bounded planner",
        })
    return rows



def android_fleet_snapshot(runners: list[dict[str, Any]], work: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        registry = json.loads(
            (ROOT / "ops" / "android_phone_resources.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        registry = {}
    runner_by_name = {str(r.get("name")): r for r in runners}
    devices = registry.get("devices", []) if isinstance(registry, dict) else []
    out = []
    for device in devices:
        if not isinstance(device, dict):
            continue
        name = str(device.get("runner_name") or "")
        assignments = [w for w in work if w.get("worker") == name]
        runner = runner_by_name.get(name)
        out.append({
            "resource_id": str(device.get("resource_id") or ""),
            "runner_name": name,
            "architecture": str(device.get("architecture") or ""),
            "runtime": str(device.get("runtime") or ""),
            "role": str(device.get("role") or "bounded utility support"),
            "enabled": bool(device.get("enabled", False)),
            "live_status": runner.get("status") if runner else ("active work assigned" if assignments else "not visible in Actions runner API"),
            "busy": bool(runner.get("busy")) if runner else bool(assignments),
            "current_assignments": len(assignments),
        })
    return out

def recent_activity() -> list[dict[str, Any]]:
    data = run_cmd_json([f"/repos/{REPO}/actions/runs?per_page=60"])
    if not isinstance(data, dict):
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    out = []
    for run in data.get("workflow_runs", []):
        if not isinstance(run, dict) or run.get("status") != "completed":
            continue
        raw = run.get("completed_at") or run.get("updated_at")
        try:
            ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts < cutoff:
            continue
        out.append({
            "task": run.get("name"),
            "status": run.get("conclusion"),
            "created_at": run.get("created_at"),
            "completed_at": raw,
            "actor": (run.get("actor") or {}).get("login"),
            "run_id": run.get("id"),
            "run_url": run.get("html_url"),
        })
        if len(out) >= 18:
            break
    return out



def _is_platform_commit_message(message: str) -> bool:
    normalized = " ".join(str(message or "").lower().split())
    excluded = (
        "refresh resource dashboard snapshot",
        "synchronize current operational status",
        "record ai worker state",
        "current operational status synchronizer",
    )
    return any(token in normalized for token in excluded)


def _is_material_milestone_commit(message: str) -> bool:
    normalized = " ".join(str(message or "").lower().split())
    if not normalized or _is_platform_commit_message(normalized):
        return False
    prefixes = ("research:", "evidence:", "science:", "governance:", "fix:", "ops:")
    return normalized.startswith(prefixes)


def _is_research_milestone_run(run: dict[str, Any]) -> bool:
    if not isinstance(run, dict) or run.get("status") != "completed" or run.get("conclusion") != "success":
        return False
    name = " ".join(str(run.get(key) or "") for key in ("name", "display_title")).lower()
    excluded = (
        "resource dashboard", "current operational status", "status synchronizer",
        "workflow lint", "full suite verification", "spine next-gate autonomous router",
        "ci", "pages",
    )
    if any(token in name for token in excluded):
        return False
    keywords = (
        "research", "candidate", "reproduction", "feasibility", "source", "pit", "census",
        "13f", "xbrl", "sec", "edgar", "foia", "correspondence", "procurement", "trace",
        "literature", "frontier",
    )
    return any(token in name for token in keywords) or bool(re.search(r"\bq\d{2,4}\b", name, re.IGNORECASE))


def milestone_history_12h() -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=12)
    since_iso = since.isoformat().replace("+00:00", "Z")
    entries: list[dict[str, Any]] = []

    commits = run_cmd_json([f"/repos/{REPO}/commits?since={since_iso}&until={now.isoformat().replace('+00:00','Z')}&per_page=100"])
    if isinstance(commits, list):
        for commit in commits:
            message = str((commit.get("commit") or {}).get("message") or "").splitlines()[0]
            if not _is_material_milestone_commit(message):
                continue
            ts = (
                (commit.get("commit") or {}).get("committer", {}).get("date")
                or (commit.get("commit") or {}).get("author", {}).get("date")
            )
            entries.append({
                "timestamp": ts, "kind": "COMMIT", "status": "recorded",
                "title": message,
                "detail": "Materialer Repository-Meilenstein im öffentlichen Verlauf.",
                "url": commit.get("html_url") or "", "source": "GitHub commit history",
            })

    runs = run_cmd_json([f"/repos/{REPO}/actions/runs?created=>={since_iso}&per_page=100"])
    if isinstance(runs, dict):
        for run in runs.get("workflow_runs", []):
            if not _is_research_milestone_run(run):
                continue
            entries.append({
                "timestamp": run.get("completed_at") or run.get("updated_at"),
                "kind": "RUN", "status": "success",
                "title": str(run.get("name") or "Research run"),
                "detail": f"Erfolgreich abgeschlossener Research-Run #{run.get('run_number')} (Run {run.get('id')}).",
                "url": run.get("html_url") or "", "source": "GitHub Actions",
            })

    entries.sort(key=lambda x: str(x.get("timestamp") or ""))
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in entries:
        key = (str(item.get("kind")), str(item.get("title")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[-24:]


def ai_provider_state() -> list[dict[str, Any]]:
    directory = ROOT / "ops" / "ai_worker_state"
    latest: dict[str, dict[str, Any]] = {}
    if directory.is_dir():
        for path in directory.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            provider = str(data.get("provider") or "unknown")
            observed = str(data.get("observed_at_utc") or "")
            if provider not in latest or observed > str(latest[provider].get("observed_at_utc") or ""):
                latest[provider] = data
    out = []
    for provider in ["openrouter_free", "groq_free", "gemini_cli", "mistral_api"]:
        data = latest.get(provider)
        if not data:
            out.append({
                "provider": provider,
                "status": "NO RECENT RECEIPT",
                "task": "",
                "observed_at_utc": "",
                "free_only": True,
                "cost": None,
                "response_model": "",
                "scientific_evidence": False,
            })
            continue
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        out.append({
            "provider": provider,
            "status": str(data.get("status") or "UNKNOWN"),
            "task": str(data.get("task_id") or ""),
            "observed_at_utc": str(data.get("observed_at_utc") or ""),
            "free_only": bool(data.get("free_only", False)),
            "cost": usage.get("cost") if usage else None,
            "response_model": str(data.get("response_model") or data.get("api_model") or ""),
            "scientific_evidence": bool(data.get("worker_output_is_scientific_evidence", False)),
        })
    return out


def main() -> None:
    status_text = (ROOT / "docs" / "CURRENT_STATUS.md").read_text(encoding="utf-8")
    evidence = json.loads((ROOT / "research" / "evidence" / "current_operational_state.json").read_text(encoding="utf-8"))
    os_state = json.loads((ROOT / "ops" / "trading_agent_os_state.json").read_text(encoding="utf-8"))
    status_line = next((line for line in status_text.splitlines() if line.startswith("**Current operational snapshot:**")), "")
    snapshot_sha = status_line.split("`")[1] if "`" in status_line else None
    latest_line = next((line for line in status_text.splitlines() if "Latest recorded formal result:" in line), "")
    latest_result = latest_line.split(":", 1)[1].strip() if ":" in latest_line else "not recorded"

    state_board = expanded_candidate_board(evidence, os_state, research_board(evidence, os_state))
    runs_payload = run_cmd_json([f"/repos/{REPO}/actions/runs?per_page=100"])
    recent_runs = runs_payload.get("workflow_runs", []) if isinstance(runs_payload, dict) else []
    workflow_benchmarks = duration_benchmarks(recent_runs)
    job_benchmarks = job_duration_benchmarks(recent_runs)
    work = enrich_work_durations(
        current_work_from_runs(recent_runs),
        workflow_benchmarks,
        job_benchmarks,
    )
    runners = runner_snapshot()
    ai = ai_provider_state()
    milestones_12h = milestone_history_12h()

    configured_resources = [
        {"name": "Windows self-hosted A", "type": "physical", "research_capacity_slots": 1, "role": "Formal readiness / local reproduction", "configured_runner": "LHT-N133732", "authority": "bounded capacity; no automatic performance authorization"},
        {"name": "Windows self-hosted B", "type": "physical", "research_capacity_slots": 1, "role": "Frontier discovery / data QA", "configured_runner": "LHT-N133732-2", "authority": "bounded capacity; no automatic performance authorization"},
        {"name": "Windows self-hosted C", "type": "physical", "research_capacity_slots": 1, "role": "Long deterministic runs / independent reproduction", "configured_runner": "LHT-N133732-3", "authority": "bounded capacity; no automatic performance authorization"},
        {"name": "GitHub-hosted Ubuntu x64", "type": "cloud", "research_capacity_slots": 2, "role": "Deterministic frontier, CI, source/PIT workflows", "configured_runner": "ubuntu-24.04", "authority": "non-authorizing operational capacity"},
        {"name": "GitHub-hosted ARM64", "type": "cloud", "research_capacity_slots": 2, "role": "Architecture-diverse CI / reproduction", "configured_runner": "ubuntu-24.04-arm", "authority": "non-authorizing operational capacity"},
        {"name": "Free AI pool", "type": "cloud", "research_capacity_slots": 1, "role": "Adversarial / design / engineering review", "configured_runner": "OpenRouter Free / Groq Free / Gemini / Mistral", "authority": "AI output never authorizes performance or promotion"},
    ]
    priority_codes = {"Q104:I19","Q218","Q219","Q220","Q221"}
    top4 = [x for x in state_board if x.get("code") in priority_codes]
    q104_parent = next((x for x in state_board if str(x.get("code")) == "104"), None)
    if q104_parent:
        nested = q104_parent.get("candidate_contracts")
        if isinstance(nested, dict):
            nested_i19 = nested.get("Q104:I19")
            if isinstance(nested_i19, dict) and not any(str(x.get("code")) == "Q104:I19" for x in top4):
                top4.insert(0, {
                    "code": "Q104:I19",
                    "state": str(q104_parent.get("state") or "not recorded"),
                    "lane": "FORMAL READINESS",
                    "issue_number": q104_parent.get("issue_number"),
                    "next_gate": str(nested_i19.get("next_gate") or "not recorded"),
                    "performance_authorization_allowed": bool(nested_i19.get("performance_authorization_allowed", False)),
                })
    planned_capacity = planned_capacity_plan(
        enrich_resources(configured_resources, runners, work),
        work,
        top4,
        job_benchmarks,
        os_state,
    )

    payload = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "master_sha": git_head(),
        "operational_snapshot_sha": snapshot_sha,
        "status_source": "docs/CURRENT_STATUS.md + research/evidence/current_operational_state.json + ops/trading_agent_os_state.json",
        "scientific_boundary": os_state.get("permanent_safety", {}),
        "dashboard_summary": {
            "active_work_items": len(work),
            "configured_resources": len(configured_resources),
            "runner_api_visible": len(runners) if runners else None,
            "busy_runners": sum(1 for r in runners if r.get("busy") is True) if runners else None,
            "runner_api_status": "available" if runners else "unavailable_or_empty",
            "runner_api_note": "Unavailable runner inventory is shown as unverified, not as zero/offline.",
            "runner_status_ui_url": f"https://github.com/{REPO}/settings/actions/runners",
            "runner_status_api_url": f"https://api.github.com/repos/{REPO}/actions/runners",
            "research_tracks": len(state_board),
            "ai_providers": len(ai),
            "active_capacity_items": sum(1 for r in enrich_resources(configured_resources, runners, work) if r.get("capacity_state") == "operating"),
            "research_capacity_slots_total": sum(int(r.get("research_capacity_slots", 1) or 1) for r in configured_resources),
            "research_capacity_slots_free": sum(int(r.get("research_slots_free", 0) or 0) for r in enrich_resources(configured_resources, runners, work)),
            "available_capacity_items": sum(1 for r in enrich_resources(configured_resources, runners, work) if r.get("capacity_state") == "available"),
            "planned_capacity_items": sum(1 for row in planned_capacity for item in row.get("planned_assignments", []) if item.get("scheduled")),
            "blocked_planned_items": sum(1 for row in planned_capacity for item in row.get("planned_assignments", []) if not item.get("scheduled")),
            "unallocated_routable_items": sum(1 for row in planned_capacity if row.get("capacity_state") == "available" and not row.get("planned_assignments")),
            "planned_capacity_note": "bounded plan; only entries marked dispatchable have an executable workflow route. This plan never creates scientific authorization.",
            "milestones_12h": len(milestones_12h),
        },
        "resources": enrich_resources(configured_resources, runners, work),
        "runner_live_snapshot": runners,
        "work_assignments": work,
        "planned_capacity": planned_capacity,
        "milestone_history_12h": milestones_12h,
        "pipeline": candidate_pipeline(top4, work, workflow_benchmarks, job_benchmarks),
        "duration_benchmarks": workflow_benchmarks,
        "job_duration_benchmarks": job_benchmarks,
        "workload_by_resource": {name: sum(1 for w in work if w.get("resource") == name) for name in sorted({w.get("resource") for w in work if w.get("resource")})},
        "workload_by_lane": {lane: sum(1 for w in work if w.get("lane") == lane) for lane in sorted({w.get("lane") for w in work if w.get("lane")})},
        "ai_fabric": ai,
        "current_research": {
            "latest_formal_result": latest_result,
            "highlights": recent_research_highlights(status_text),
            "research_board": state_board,
            "top4": top4,
            "planned_capacity_note": "bounded plan; entries with dispatchable=true have an executable workflow route; blocked/non-dispatchable entries remain advisory only.",
        },
        "lane_model": {
            "lane_a": os_state.get("two_lane_research_mode", {}).get("lane_a", {}),
            "lane_b": os_state.get("two_lane_research_mode", {}).get("lane_b", {}),
            "isolation": os_state.get("two_lane_research_mode", {}).get("isolation", {}),
        },
        "dashboard_policy": {
            "daily_update_utc": "03:35",
            "manual_update": True,
            "website_update_button": "opens authenticated GitHub Actions dispatch page; static Pages cannot safely dispatch a write-authorized workflow without a user-authenticated GitHub session or token",
            "pages_source": "/docs on master",
            "live_work_note": "Current work assignments are a timestamped GitHub Actions snapshot. They are not runner execution receipts and do not create scientific authority.",
            "fast_dispatch_rule": "When bounded research work is planned and its resource is free/routable, an executable workflow may be dispatched immediately; when zero research jobs are active, dispatch all distinct ready workflow groups up to the bounded per-event cap. Prerequisite-blocked/non-dispatchable plans never dispatch.",
        },
        "governance_notes": [
            "Operational resource availability and active jobs are separate from scientific evidence.",
            "AI worker output is never scientific evidence.",
            "Source feasibility and PIT readiness never imply performance authorization.",
            "Dashboard fields cannot authorize ranking, tuning, promotion or live execution.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    formatted = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    OUT.write_text(formatted, encoding="utf-8")
    # Embed the same snapshot in a tiny synchronous JS bootstrap so the public
    # page renders even when the first network fetch is delayed or unavailable.
    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    bootstrap_literal = json.dumps(serialized).replace("<", "\\u003c")
    BOOTSTRAP.write_text(
        "// Generated by automation/generate_resource_dashboard.py; do not edit by hand.\n"
        "window.__TRADING_AGENT_SNAPSHOT__ = JSON.parse(" + bootstrap_literal + ");\n",
        encoding="utf-8",
    )
    print(f"RESOURCE_DASHBOARD_GENERATED master={payload['master_sha']} path={OUT} bootstrap={BOOTSTRAP}")

if __name__ == "__main__":
    main()
