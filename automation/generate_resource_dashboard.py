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
    active_text = [f"{x.get('task','')} {x.get('job','')}".lower() for x in work]
    active_candidates = {
        candidate for candidate in ("Q104:I19", "Q218", "Q219", "Q220", "Q221", "Q224", "Q228", "Q231")
        if any(candidate.lower() in value for value in active_text)
    }

    overlay = os_state.get("top_candidate_capacity_overlay", {})
    a_priority = [str(x) for x in overlay.get("windows_A", {}).get("priority", [])]
    b_priority = [str(x) for x in overlay.get("windows_B", {}).get("priority", [])]
    queue = [
        {
            "plan_id": "Q104-I19-COMPILER",
            "candidate": "Q104:I19",
            "lane": "FORMAL READINESS",
            "task": "concept-specific PIT compiler after 13F acceptance-time join",
            "preferred": ["Windows self-hosted A", "GitHub-hosted Ubuntu x64"],
            "readiness": "READY_AFTER_ACCEPTANCE_JOIN",
            "basis": "frozen Q104:I19 contract + current acceptance-time join PR",
        },
        {
            "plan_id": "Q104-I19-INDEPENDENT-REPRO",
            "candidate": "Q104:I19",
            "lane": "FORMAL READINESS",
            "task": "independent reproduction of compiler/PIT result",
            "preferred": ["Windows self-hosted C", "GitHub-hosted ARM64"],
            "readiness": "BLOCKED_UNTIL_COMPILER_RECEIPT",
            "basis": "next gate explicitly requires independent reproduction",
        },
        {
            "plan_id": "Q218-PIT",
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
            "task": "historical options breadth and deterministic post-filing response PIT",
            "preferred": ["GitHub-hosted Ubuntu x64", "Windows self-hosted B"],
            "readiness": "READY_SOURCE_PIT",
            "basis": "Q129 reproduction plus Q219 breadth lead; PIT still must be proven",
        },
        {
            "plan_id": "Q220-PIT",
            "candidate": "Q220",
            "lane": "FRONTIER DISCOVERY",
            "task": "deterministic narrative/XBRL presentation mapping and PIT",
            "preferred": ["Windows self-hosted B", "GitHub-hosted ARM64"],
            "readiness": "READY_SOURCE_SCHEMA",
            "basis": "SEC FSN schema gate + XBRL concept-freeze audit",
        },
        {
            "plan_id": "Q221-PIT",
            "candidate": "Q221",
            "lane": "FRONTIER DISCOVERY",
            "task": "historical USAspending public boundary and issuer/entity mapping",
            "preferred": ["GitHub-hosted Ubuntu x64", "Windows self-hosted B"],
            "readiness": "READY_SOURCE_CLOCK",
            "basis": "USAspending public-clock contract ready; applicability/entity mapping open",
        },
        {
            "plan_id": "Q224-EDGAR-LOG",
            "candidate": "Q224",
            "lane": "FRONTIER DISCOVERY",
            "task": "modern EDGAR access-log archive census and request→filing decoding",
            "preferred": ["Windows self-hosted B", "GitHub-hosted Ubuntu x64"],
            "readiness": "READY_DISCOVERY",
            "basis": "official EDGAR log channel; archive/schema/identity gate remains",
        },
        {
            "plan_id": "Q228-CORRESPONDENCE",
            "candidate": "Q228",
            "lane": "FRONTIER DISCOVERY",
            "task": "historical SEC correspondence census, release clock and review identity",
            "preferred": ["Windows self-hosted B", "GitHub-hosted Ubuntu x64"],
            "readiness": "READY_DISCOVERY",
            "basis": "SEC correspondence source gate; selection mechanism remains a control",
        },
        {
            "plan_id": "Q231-FOIA",
            "candidate": "Q231",
            "lane": "FRONTIER DISCOVERY",
            "task": "historical SEC FOIA publication clock and requester/issuer mapping",
            "preferred": ["GitHub-hosted Ubuntu x64", "Windows self-hosted B"],
            "readiness": "READY_DISCOVERY",
            "basis": "official monthly FOIA logs; exact publication clock still open",
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
        if candidate in active_candidates or candidate in assigned_candidates:
            continue
        if item["readiness"].startswith("BLOCKED_"):
            continue
        placed = False
        for resource_name in item["preferred"]:
            if plans.get(resource_name):
                continue
            resource = next((r for r in resources if str(r["name"]) == resource_name), None)
            if resource is None:
                continue
            if resource.get("capacity_state") == "operating":
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
                "execution_status": "planned_not_started",
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
    if c_resource in plans and not plans[c_resource] and "Q104:I19" not in active_candidates:
        plans[c_resource].append({
            "plan_id": "Q104-I19-INDEPENDENT-REPRO",
            "candidate": "Q104:I19",
            "lane": "FORMAL READINESS",
            "task": "independent reproduction of compiler/PIT result",
            "readiness": "BLOCKED_UNTIL_COMPILER_RECEIPT",
            "basis": "next gate explicitly requires independent reproduction",
            "scheduled": False,
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