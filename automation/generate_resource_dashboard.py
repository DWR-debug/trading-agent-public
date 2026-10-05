from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
OUT = ROOT / "docs" / "dashboard" / "dashboard_data.json"
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
        env.setdefault("GH_TOKEN", env.get("GITHUB_TOKEN", ""))
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
        "q204", "q205", "frontier"
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


def current_work() -> list[dict[str, Any]]:
    data = run_cmd_json([f"/repos/{REPO}/actions/runs?per_page=100"])
    if not isinstance(data, dict):
        return []
    active = [
        x for x in data.get("workflow_runs", [])
        if isinstance(x, dict) and x.get("status") in {"queued", "in_progress", "waiting", "pending"}
    ]
    active.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    out = []
    job_budget = 18
    for run in active:
        workflow = str(run.get("name") or "")
        jobs = jobs_for_run(int(run["id"])) if job_budget and run.get("id") else []
        if jobs:
            job_budget -= 1
            jobs = [j for j in jobs if j.get("status") in {"queued", "in_progress", "waiting"}] or jobs[:1]
            for job in jobs:
                out.append({
                    "resource": infer_resource(workflow, str(job.get("name") or ""), job.get("runner_name")),
                    "lane": infer_lane(workflow, str(job.get("name") or "")),
                    "worker": job.get("runner_name") or "pending runner assignment",
                    "job": str(job.get("name") or ""),
                    "task": workflow,
                    "status": run.get("status"),
                    "started_at": run.get("run_started_at") or run.get("created_at"),
                    "actor": (run.get("actor") or {}).get("login"),
                    "run_id": run.get("id"),
                    "run_url": run.get("html_url"),
                    "authority": "non-authorizing operational work",
                })
        else:
            out.append({
                "resource": infer_resource(workflow, "", None),
                "lane": infer_lane(workflow),
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


def enrich_resources(configured: list[dict[str, Any]], runners: list[dict[str, Any]], work: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    runner_by_name = {str(r.get("name")): r for r in runners}
    for resource in configured:
        assignments = [w for w in work if w.get("resource") == resource["name"]]
        runner = runner_by_name.get(resource["configured_runner"])
        if runner:
            live_status = "online / busy" if runner.get("busy") else str(runner.get("status") or "unknown")
        elif assignments:
            live_status = f"active work assigned ({len(assignments)})"
        elif resource["type"] in {"cloud", "service"}:
            live_status = "not assigned in snapshot"
        else:
            live_status = "configured / live runner state unavailable"
        out.append({
            **resource,
            "live_status": live_status,
            "busy": bool(runner.get("busy")) if runner else bool(assignments),
            "labels": runner.get("labels", []) if runner else [],
            "current_assignments": len(assignments),
            "current_tasks": [w.get("task") for w in assignments[:4]],
        })
    return out



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
    work = current_work()
    runners = runner_snapshot()
    ai = ai_provider_state()

    payload = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "master_sha": git_head(),
        "operational_snapshot_sha": snapshot_sha,
        "status_source": "docs/CURRENT_STATUS.md + research/evidence/current_operational_state.json + ops/trading_agent_os_state.json",
        "scientific_boundary": os_state.get("permanent_safety", {}),
        "dashboard_summary": {
            "active_work_items": len(work),
            "configured_resources": 12,
            "runner_api_visible": len(runners),
            "busy_runners": sum(1 for r in runners if r.get("busy") is True) if runners else None,
            "runner_api_status": "available" if runners else "unavailable_or_empty",
            "research_tracks": len(state_board),
            "ai_providers": len(ai),
        },
        "resources": enrich_resources(
            [
                {"name": "Windows self-hosted A", "type": "physical", "role": "Formal readiness / local reproduction", "configured_runner": "LHT-N133732", "authority": "bounded capacity; no automatic performance authorization"},
                {"name": "Windows self-hosted B", "type": "physical", "role": "Frontier discovery / data QA", "configured_runner": "LHT-N133732-2", "authority": "bounded capacity; no automatic performance authorization"},
                {"name": "Windows self-hosted C", "type": "physical", "role": "Long deterministic runs / independent reproduction", "configured_runner": "LHT-N133732-3", "authority": "bounded capacity; no automatic performance authorization"},
                {"name": "GitHub-hosted Ubuntu x64", "type": "cloud", "role": "Deterministic frontier, CI, source/PIT workflows", "configured_runner": "ubuntu-24.04", "authority": "non-authorizing unless an exact formal gate says otherwise"},
                {"name": "GitHub-hosted ARM64", "type": "cloud", "role": "Architecture-diverse CI / reproduction", "configured_runner": "ubuntu-24.04-arm", "authority": "non-authorizing unless an exact formal gate says otherwise"},
                {"name": "S10 / Android", "type": "physical", "role": "Deterministic mechanical QA", "configured_runner": "S10-TERMUX", "authority": "non-scientific support only"},
                {"name": "Samsung Android fleet", "type": "physical", "role": "Prepared bounded utility capacity; five labelled slots", "configured_runner": "SAMSUNG-PHONE-01..05", "authority": "bounded support only; activation is online/acceptance gated"},
                {"name": "Free AI pool", "type": "cloud", "role": "Adversarial / design / engineering review", "configured_runner": "OpenRouter Free / Groq Free / Gemini / Mistral", "authority": "AI output never authorizes performance or promotion"},
                {"name": "Bounded Agent Queue", "type": "cloud", "role": "Bounded engineering / review requests", "configured_runner": "agent-request-queue", "authority": "no paid fallback; no scientific authority"},
                {"name": "Codespaces fallback", "type": "cloud", "role": "Interactive debugging / data QA", "configured_runner": "manual", "authority": "fallback only; unattended default disabled"},
                {"name": "Paper Forward / Shadow", "type": "simulation", "role": "Paper-only monitoring and MTM ledger", "configured_runner": "scheduled workflows", "authority": "simulation only; no live orders"},
                {"name": "Dashboard / GitHub Pages", "type": "service", "role": "Operational visibility and status publication", "configured_runner": "GitHub Pages", "authority": "read-only operational snapshot"},
            ],
            runners,
            work,
        ),
        "runner_live_snapshot": runners,
        "work_assignments": work,
        "workload_by_resource": {name: sum(1 for w in work if w.get("resource") == name) for name in sorted({w.get("resource") for w in work if w.get("resource")})},
        "workload_by_lane": {lane: sum(1 for w in work if w.get("lane") == lane) for lane in sorted({w.get("lane") for w in work if w.get("lane")})},
        "recent_activity_24h": recent_activity(),
        "ai_fabric": ai,
        "android_fleet": android_fleet_snapshot(runners, work),
        "current_research": {
            "latest_formal_result": latest_result,
            "highlights": recent_research_highlights(status_text),
            "research_board": state_board,
        },
        "lane_model": {
            "lane_a": os_state.get("two_lane_research_mode", {}).get("lane_a", {}),
            "lane_b": os_state.get("two_lane_research_mode", {}).get("lane_b", {}),
            "isolation": os_state.get("two_lane_research_mode", {}).get("isolation", {}),
        },
        "dashboard_policy": {
            "daily_update_utc": "03:35",
            "manual_update": True,
            "website_update_button": "opens GitHub Actions workflow dispatch page",
            "pages_source": "/docs on master",
            "live_work_note": "Current work assignments are a timestamped GitHub Actions snapshot. They are not runner execution receipts and do not create scientific authority.",
        },
        "governance_notes": [
            "Operational resource availability and active jobs are separate from scientific evidence.",
            "AI worker output is never scientific evidence.",
            "Source feasibility and PIT readiness never imply performance authorization.",
            "Dashboard fields cannot authorize ranking, tuning, promotion or live execution.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESOURCE_DASHBOARD_GENERATED master={payload['master_sha']} path={OUT}")

if __name__ == "__main__":
    main()
