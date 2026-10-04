from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUT = ROOT / "docs" / "dashboard" / "dashboard_data.json"

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

def main() -> None:
    status_text = (ROOT / "docs" / "CURRENT_STATUS.md").read_text(encoding="utf-8")
    evidence = json.loads((ROOT / "research" / "evidence" / "current_operational_state.json").read_text(encoding="utf-8"))
    os_state = json.loads((ROOT / "ops" / "trading_agent_os_state.json").read_text(encoding="utf-8"))
    status_line = next((line for line in status_text.splitlines() if line.startswith("**Current operational snapshot:**")), "")
    snapshot_sha = status_line.split("`")[1] if "`" in status_line else None
    latest_line = next((line for line in status_text.splitlines() if "Latest recorded formal result:" in line), "")
    latest_result = latest_line.split(":", 1)[1].strip() if ":" in latest_line else "not recorded"

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "master_sha": git_head(),
        "operational_snapshot_sha": snapshot_sha,
        "status_source": "docs/CURRENT_STATUS.md + research/evidence/current_operational_state.json",
        "scientific_boundary": os_state.get("permanent_safety", {}),
        "resources": [
            {"name": "Windows slot A", "role": "Formal readiness / local reproduction", "cadence": "10 min + event-driven", "authority": "bounded capacity; no automatic performance authorization"},
            {"name": "Windows slot B", "role": "Frontier discovery / data QA", "cadence": "10 min + event-driven", "authority": "bounded capacity; no automatic performance authorization"},
            {"name": "GitHub-hosted Ubuntu", "role": "Deterministic frontier / CI / source-PIT", "cadence": "10 min + event-driven", "authority": "non-authorizing unless a separate formal gate says otherwise"},
            {"name": "S10 / Android", "role": "Deterministic mechanical QA", "cadence": "2 h + meaningful changes", "authority": "non-scientific support only"},
            {"name": "Free AI pool", "role": "Bounded adversarial / design / engineering review", "cadence": "event-driven", "authority": "AI outputs are never scientific evidence"}
        ],
        "resource_policy": {"windows_slots": 2, "windows_pulse_utc": "*/10 * * * *", "windows_lane_concurrency": {"local_reproduction": "trading-agent-windows-research-capacity-v1", "data_qa": "trading-agent-windows-research-data-qa-v1"}, "local_ai_workflow": ".github/workflows/windows-local-ai-worker.yml", "local_ai_trigger": "manual only", "s10_role": "deterministic mechanical research/governance QA; non-scientific", "hosted_linux_frontier": "*/10 * * * *"},
        "current_research": {"latest_formal_result": latest_result, "highlights": recent_research_highlights(status_text), "active_registry_tail": candidate_highlights(evidence)},
        "dashboard_policy": {"daily_update_utc": "03:35", "manual_update": True, "website_update_button": "opens GitHub Actions workflow dispatch page", "pages_source": "/docs on master"}
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESOURCE_DASHBOARD_GENERATED master={payload['master_sha']} path={OUT}")

if __name__ == "__main__":
    main()
