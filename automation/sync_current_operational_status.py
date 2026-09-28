"""Generate the canonical, machine-readable current operational project status."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation.q067_pipeline_state import summarize as summarize_q067_pipeline
from automation.q068_pipeline_state import summarize as summarize_q068_pipeline

ROOT = Path(__file__).resolve().parents[1]
STATUS_DOC = ROOT / "docs" / "CURRENT_STATUS.md"
STATUS_JSON = ROOT / "research" / "evidence" / "current_operational_state.json"


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def _recent_commits(limit: int = 8) -> list[dict[str, str]]:
    last_error: subprocess.CalledProcessError | None = None
    for ref in ("master", "origin/master", "HEAD"):
        try:
            output = _git(
                "log",
                f"-{limit}",
                "--format=%H%x09%aI%x09%s",
                ref,
            )
        except subprocess.CalledProcessError as exc:
            last_error = exc
            continue
        rows = []
        for line in output.splitlines():
            sha, timestamp, message = line.split("\t", 2)
            rows.append(
                {"sha": sha, "timestamp": timestamp, "message": message}
            )
        return rows
    assert last_error is not None
    raise last_error


def _read_queue_files() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    root = ROOT / "agent_requests"
    for lane in ("lane0", "lane1"):
        lane_root = root / lane
        if not lane_root.exists():
            continue
        for path in sorted(lane_root.glob("*.request")):
            payload = _load_json(path, {})
            if isinstance(payload, dict):
                results.append(
                    {
                        "lane": lane,
                        "request_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "task_id": str(payload.get("task_id", "")),
                        "issue_number": str(payload.get("issue_number", "")),
                    }
                )
    return results


def _safety_state() -> dict[str, bool]:
    from config import settings
    return {
        "PAPER_ONLY": settings.PAPER_ONLY is True,
        "LIVE_TRADING_ENABLED": settings.LIVE_TRADING_ENABLED is True,
        "ORDERS_ENABLED": settings.ORDERS_ENABLED is True,
        "AUTOMATIC_PROMOTION": settings.AUTOMATIC_PROMOTION is True,
    }


def generate(
    *,
    source_master_sha: str,
    workflow_run_id: str | None,
    github_state_path: Path | None,
) -> tuple[dict[str, Any], str]:
    project_state = _load_json(ROOT / "research/evidence/project_state.json", {})
    checkpoint = _load_json(
        ROOT / "research/evidence/current_project_checkpoint.json", {}
    )
    decision_basis = _load_json(
        ROOT / "research/evidence/decision_basis_latest.json", {}
    )
    github_state = _load_json(github_state_path, {}) if github_state_path else {}

    safety = _safety_state()
    from config import settings
    queue = _read_queue_files()
    open_prs = github_state.get("open_prs", [])
    agent_ready_issues = github_state.get("agent_ready_issues", [])
    q067_pipeline = summarize_q067_pipeline(ROOT)
    q068_pipeline = summarize_q068_pipeline(ROOT)
    recorded_qa = project_state.get("quality_assurance", {}).get(
        "last_verified_self_hosted_qa", {}
    )

    current = {
        "schema_version": "1.0",
        "status_type": "current_operational_project_state",
        "repository": "DWR-debug/trading-agent-public",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_master_sha": source_master_sha,
        "status_commit_is_documentation_only": True,
        "canonical_sources": {
            "human_current_status": "docs/CURRENT_STATUS.md",
            "machine_current_status": "research/evidence/current_operational_state.json",
            "project_context": "docs/PROJECT_CONTEXT.md",
            "historical_status": "PROJECT_STATUS.md",
            "research_state": "research/evidence/project_state.json",
            "research_checkpoint": "research/evidence/current_project_checkpoint.json",
            "research_decision_basis": "research/evidence/decision_basis_latest.json",
            "trial_ledger": "research/evidence/trial_ledger.json",
        },
        "repository_state": {
            "default_branch": "master",
            "recent_commits": _recent_commits(),
            "open_pull_requests": open_prs,
            "open_agent_ready_issues": agent_ready_issues,
            "agent_queue_requests": queue,
        },
        "engineering_state": {
            "paper_forward": {
                "status": "MERGED",
                "merge_commit": "a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba",
                "pr": 352,
                "components": [
                    "closed-candle Binance market feed",
                    "persistent autonomous update loop",
                    "schema-v2 per-candle MTM ledger",
                    "paper-only safety guard",
                    "persistent fingerprint integrity checks",
                ],
            },
            "canonical_data_layer": {
                "status": "MERGED",
                "merge_commit": "d81c4399260145e21156064ab76fad77a9969222",
                "pr": 232,
            },
            "agent_orchestration": {
                "bounded_two_lane_queue": True,
                "control_plane": "automation/autonomous_control_plane.py",
                "copilot_cli_queue": ".github/workflows/agent-request-queue.yml",
                "current_pending_requests": queue,
            },
            "self_hosted_qa": {
                "cadence": "*/15 * * * *",
                "label": "trading-agent-research",
                "architecture": "single runner process claimed; second process prepared but not claimed online",
                "last_recorded_verified_baseline": recorded_qa,
            },
            "scientific_compute": {
                "canonical_path": "GitHub-hosted deterministic workflows",
                "self_hosted_output_formal_evidence": False,
            },
        },
        "q067_execution_pipeline": q067_pipeline,
        "q068_execution_pipeline": q068_pipeline,
        "scientific_state_recorded": {
            "latest_formal_trial": project_state.get("latest_formal_trial"),
            "latest_formal_status": project_state.get("latest_trial_status"),
            "next_research_focus_recorded": project_state.get("next_research_focus"),
            "decision_basis_stage": decision_basis.get("current_stage"),
            "q026_recorded": checkpoint.get("q026"),
            "q025_recorded": checkpoint.get("q025"),
            "q023_recorded": checkpoint.get("q023"),
            "note": "Latest recorded research state; not re-evaluated by this synchronizer.",
        },
        "resource_policy": {
            "paid_agent_budget_usd": 0,
            "paid_api_budget_usd": 0,
            "free_resources_only": True,
            "actual_capital_available": False,
            "hypothetical_reference_capital_eur": float(settings.HYPOTHETICAL_STARTING_CAPITAL_EUR),
            "legacy_operational_canary_capital_eur": 500.0,
        },
        "safety": safety,
        "workflow": {
            "name": "Current Operational Status Synchronizer",
            "run_id": workflow_run_id,
            "purpose": "Keep current operational status synchronized with master without mutating scientific evidence.",
        },
    }

    if (
        not safety["PAPER_ONLY"]
        or safety["LIVE_TRADING_ENABLED"]
        or safety["ORDERS_ENABLED"]
        or safety["AUTOMATIC_PROMOTION"]
    ):
        current["safety"]["status"] = "VIOLATION"
    else:
        current["safety"]["status"] = "SAFE"

    current_json = json.dumps(current, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    doc = f"""# Trading Agent — Current Operational Status

**Current operational snapshot:** `{source_master_sha}`

**Generated (UTC):** `{current['generated_at_utc']}`

**Repository:** `DWR-debug/trading-agent-public`

> This file is the canonical current operational status. `PROJECT_STATUS.md` is historical reconstruction and must not override it for current operational facts. Scientific evidence remains governed by the trial ledger, immutable evidence/checkpoints and workflow artifacts.

## Current state

### Engineering

- Paper/Shadow/Forward infrastructure: **MERGED** via PR #352, merge commit `a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba`.
- The Forward path contains closed-candle market-data ingestion, a persistent update loop and a schema-v2 per-candle MTM ledger.
- Canonical data-layer infrastructure is merged.
- Bounded agent routing uses two queue lanes with fail-closed task contracts.
- Self-hosted Continuous QA is scheduled every 15 minutes under label `trading-agent-research`.
- The current architecture claims one runner process; a second process is only a prepared scale path, not an online capacity claim.

### Scientific status

- Latest recorded formal result: **{project_state.get("latest_trial_status", "UNKNOWN")}** for `{project_state.get("latest_formal_trial", "UNKNOWN")}`.
- Q026 is recorded as **DATA_INVALID / NO_SCIENTIFIC_OUTCOME**; it did not produce performance evidence.
- Q023 is recorded as **COVERAGE_VALIDATED** and Q025 as **DATE_PIT_VALIDATED**; these are data-contract findings, not promotion evidence.
- No current candidate is authorized for promotion or live execution.
- Candidate discovery and PIT feasibility remain the required steps before any new formal performance evaluation.

### Q067 execution pipeline

- Operational state: **{q067_pipeline["state"]}**.
- Coverage receipt: **{q067_pipeline["coverage_receipt"]["status"] or "MISSING"}**.
- PIT receipt: **{q067_pipeline["pit_receipt"]["status"] or "MISSING"}**.
- Performance authorization: **{q067_pipeline["performance_authorization"]["authorized"]}**.
- Performance evidence: **{q067_pipeline["performance_result"]["status"] or "MISSING"}**.
- Ledger reconciled: **{q067_pipeline["ledger_reconciled"]}**.
- Blocking reasons: **{"; ".join(q067_pipeline["blocking_reasons"]) or "none"}**.

This is an operational pipeline summary only; it does not create scientific evidence or select a candidate.

### Q068 execution pipeline

- Operational state: **{q068_pipeline["state"]}**.
- Coverage receipt: **{q068_pipeline["coverage_receipt"]["status"] or "MISSING"}**.
- PIT receipt: **{q068_pipeline["pit_receipt"]["status"] or "MISSING"}**.
- Performance authorization: **{q068_pipeline["performance_authorization"]["authorized"]}**.
- Performance evidence: **{q068_pipeline["performance_result"]["status"] or "MISSING"}**.
- Ledger reconciled: **{q068_pipeline["ledger_reconciled"]}**.
- Blocking reasons: **{"; ".join(q068_pipeline["blocking_reasons"]) or "none"}**.

Q068 is a fresh symbol-disjoint validation of the unchanged Q067 E1/E2 mechanisms. This operational summary does not create scientific evidence or select an arm.

### Resource policy

- Paid agent/API budget: **0 USD**.
- Actual available capital: **0 EUR**.
- Hypothetical reference capital: **{int(settings.HYPOTHETICAL_STARTING_CAPITAL_EUR)} EUR**, simulation/planning only.
- Legacy 500-EUR operational canary remains separate.
- Deterministic research stays on reproducible runner paths.
- Agent output is never scientific evidence by itself.

## Safety

`PAPER_ONLY=True`

`LIVE_TRADING_ENABLED=False`

`ORDERS_ENABLED=False`

`AUTOMATIC_PROMOTION=False`

## Canonical source order

1. Current operational facts: `docs/CURRENT_STATUS.md` and `research/evidence/current_operational_state.json`
2. Technical truth: current `master`
3. Scientific evidence: trial ledger, immutable evidence/checkpoints and workflow artifacts
4. Project intent: `docs/PROJECT_CONTEXT.md`
5. Historical reconstruction: `PROJECT_STATUS.md`

## Continuity protocol

Every relevant `master` push triggers the status synchronizer. It records the exact source commit being synchronized and updates these two operational-status files in a documentation-only commit. Those files are excluded from the synchronizer trigger, preventing recursive commits.

A future `trading agent` chat must read this file first, then verify live GitHub state before acting.
"""
    return current, doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-master-sha", required=True)
    parser.add_argument("--workflow-run-id")
    parser.add_argument("--github-state")
    parser.add_argument("--output-doc", default=str(STATUS_DOC))
    parser.add_argument("--output-json", default=str(STATUS_JSON))
    args = parser.parse_args()

    current, doc = generate(
        source_master_sha=args.source_master_sha,
        workflow_run_id=args.workflow_run_id,
        github_state_path=Path(args.github_state) if args.github_state else None,
    )
    doc_path = Path(args.output_doc)
    json_path = Path(args.output_json)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(doc, encoding="utf-8")
    json_path.write_text(
        json.dumps(current, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if current["safety"]["status"] == "SAFE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
