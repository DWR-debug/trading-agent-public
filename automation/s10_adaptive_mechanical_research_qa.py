"""Adaptive S10 mechanical research/governance QA.

Runs on the dedicated S10/Termux worker. The task rotates deterministically across
five bounded QA classes so the device performs changing, useful repository work
rather than repeating one fixed smoke test. It never produces scientific
evidence, selection, ranking, authorization, promotion, or live-trading actions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

CORE = (
    "docs/CURRENT_STATUS.md",
    "research/evidence/current_operational_state.json",
    "research/governance/active_research_registry.json",
    "research/governance/persistent_research_acceleration_contract.json",
    "research/governance/critical_research_quality_control.json",
    "research/governance/literature_research_policy.json",
    "research/run_requests/rolling_capacity_window_2026-10-05.json",
)
FORBIDDEN_TRUE_KEYS = {
    "performance",
    "performance_authorized",
    "performance_authorization_allowed",
    "holdout_selection",
    "holdout_selection_allowed",
    "ranking",
    "family_ranking_allowed",
    "parameter_search",
    "parameter_search_allowed",
    "asset_search",
    "asset_search_allowed",
    "threshold_search",
    "threshold_search_allowed",
    "horizon_search",
    "horizon_search_allowed",
    "variant_search_allowed",
    "promotion",
    "automatic_promotion",
    "live_execution",
    "live_trading_enabled",
    "orders_enabled",
}
MODES = (
    "PROVENANCE_STATUS",
    "FRONTIER_GOVERNANCE",
    "PIT_CLOCK_AND_LINEAGE",
    "CAPACITY_DISPATCH",
    "NEGATIVE_EVIDENCE_DEDUP",
)
SAFETY = {
    "PAPER_ONLY": True,
    "LIVE_TRADING_ENABLED": False,
    "ORDERS_ENABLED": False,
    "AUTOMATIC_PROMOTION": False,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def existing_paths_from_registry(root: Path) -> list[str]:
    registry = load_json(root / "research/governance/active_research_registry.json")
    found: set[str] = set(CORE)
    queue: list[Any] = [registry]
    while queue:
        node = queue.pop()
        if isinstance(node, dict):
            queue.extend(node.values())
        elif isinstance(node, list):
            queue.extend(node)
        elif isinstance(node, str):
            for prefix in ("docs/", "research/", "automation/", "tests/", "ops/", ".github/"):
                if node.startswith(prefix) and (root / node).is_file():
                    found.add(node)
                    break
    return sorted(found)


def inventory_objects(root: Path, paths: list[str]) -> list[tuple[str, dict[str, Any]]]:
    out: list[tuple[str, dict[str, Any]]] = []
    for rel in paths:
        if not rel.startswith("research/frontier/") or not rel.endswith(".json"):
            continue
        p = root / rel
        try:
            value = load_json(p)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            out.append((rel, value))
    return out


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.repo_root.resolve()
    run_number = int(os.environ.get("GITHUB_RUN_NUMBER", "0") or 0)
    mode = MODES[run_number % len(MODES)]
    failures: list[str] = []
    findings: list[dict[str, Any]] = []

    for rel in CORE:
        p = root / rel
        if not p.is_file():
            failures.append(f"missing:{rel}")
        else:
            findings.append({"path": rel, "sha256": digest(p), "bytes": p.stat().st_size})

    try:
        status = load_json(root / "research/evidence/current_operational_state.json")
        registry = load_json(root / "research/governance/active_research_registry.json")
        acceleration = load_json(
            root / "research/governance/persistent_research_acceleration_contract.json"
        )
        critical = load_json(
            root / "research/governance/critical_research_quality_control.json"
        )
        literature = load_json(root / "research/governance/literature_research_policy.json")
        lease = load_json(root / "research/run_requests/rolling_capacity_window_2026-10-05.json")
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        failures.append(f"core_json:{type(exc).__name__}:{exc}")
        status = registry = acceleration = critical = literature = lease = {}

    if acceleration.get("status") != "ACTIVE":
        failures.append("acceleration_contract_not_active")
    if critical.get("status") != "ACTIVE":
        failures.append("critical_quality_control_not_active")
    for key, expected in SAFETY.items():
        if critical.get("safety", {}).get(key.lower()) is not expected:
            # critical control uses lower-case safety names
            actual = critical.get("safety", {}).get(key.lower())
            if actual is not expected:
                failures.append(f"critical_safety:{key}:{actual!r}")
    for key, expected in {
        "performance": False,
        "holdout": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    }.items():
        if lease.get("safety", {}).get(key) is not expected:
            failures.append(f"lease_safety:{key}")

    source_commit = os.environ.get("GITHUB_SHA")
    status_source = status.get("source_master_sha")
    findings.append({
        "provenance": "status_vs_run_sha",
        "run_sha": source_commit,
        "status_source_sha": status_source,
        "status_sha_matches": bool(source_commit and source_commit == status_source),
        "classification": (
            "MATCH"
            if source_commit and source_commit == status_source
            else "EXPECTED_DRIFT_DURING_ACTIVE_PUSH"
        ),
    })

    paths = existing_paths_from_registry(root)
    inventories = inventory_objects(root, paths)
    findings.append({"active_registry_referenced_files": len(paths)})
    findings.append({"frontier_inventories_checked": len(inventories)})

    if mode == "PROVENANCE_STATUS":
        if status.get("repository") != "DWR-debug/trading-agent-public":
            failures.append("status_repository_mismatch")
        if status.get("safety", {}).get("status") != "SAFE":
            failures.append("status_safety_not_safe")
        handoff = root / "research/evidence/trading_agent_chat_handoff.json"
        if handoff.is_file():
            h = load_json(handoff)
            findings.append({
                "handoff_source_sha": h.get("source_master_sha"),
                "handoff_matches_run_sha": bool(source_commit and h.get("source_master_sha") == source_commit),
            })

    elif mode == "FRONTIER_GOVERNANCE":
        for rel, obj in inventories:
            for node in walk_dicts(obj):
                for key in FORBIDDEN_TRUE_KEYS:
                    if node.get(key) is True:
                        failures.append(f"forbidden_true:{rel}:{key}")
        shortlist = literature.get("shortlist_maximum")
        active = literature.get("active_frontier", [])
        if shortlist is not None and isinstance(active, list) and len(active) > int(shortlist):
            failures.append(f"literature_shortlist_exceeded:{len(active)}>{shortlist}")

    elif mode == "PIT_CLOCK_AND_LINEAGE":
        for rel, obj in inventories:
            joined = json.dumps(obj, ensure_ascii=False).lower()
            if "pit" not in joined:
                findings.append({"path": rel, "pit_marker": False})
            if "revision" not in joined and "amendment" not in joined:
                findings.append({"path": rel, "revision_lineage_marker": False})
            if "source" not in joined and "clock" not in joined:
                failures.append(f"missing_source_or_clock_marker:{rel}")

    elif mode == "CAPACITY_DISPATCH":
        phases = lease.get("phases", [])
        if not phases:
            failures.append("capacity_phases_missing")
        seen_phase: dict[str, set[str]] = {}
        for phase in phases:
            phase_id = str(phase.get("id", ""))
            names = [str(w) for w in phase.get("workflows", [])]
            phase_seen = seen_phase.setdefault(phase_id, set())
            for name in names:
                if name in phase_seen:
                    failures.append(f"duplicate_workflow_in_phase:{phase_id}:{name}")
                phase_seen.add(name)
                workflow_path = root / ".github/workflows" / name
                if not workflow_path.is_file():
                    failures.append(f"missing_capacity_workflow:{name}")
        findings.append({"capacity_phases": [p.get("id") for p in phases]})

    else:  # NEGATIVE_EVIDENCE_DEDUP
        neg = literature.get("negative_evidence", [])
        if not isinstance(neg, list) or not {"PRUNED", "UNVERIFIED", "DATA_INSUFFICIENT"}.issubset(set(neg)):
            failures.append("negative_evidence_taxonomy_incomplete")
        entries = []
        for node in walk_dicts(literature):
            for key in ("negative_findings", "negative_evidence", "retained_negative_evidence"):
                value = node.get(key)
                if isinstance(value, list):
                    entries.extend(value)
        duplicates = []
        normalized: list[str] = []
        for item in entries:
            if isinstance(item, dict):
                marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
            else:
                marker = str(item)
            normalized.append(marker)
        seen: set[str] = set()
        for marker in normalized:
            if marker in seen:
                duplicates.append(marker)
            seen.add(marker)
        if duplicates:
            failures.append(f"duplicate_negative_evidence_entries:{len(duplicates)}")
        findings.append({"negative_evidence_entries_seen": len(entries)})

    receipt = {
        "schema_version": "1.0",
        "receipt_type": "s10_adaptive_mechanical_research_qa",
        "source_commit": source_commit,
        "runner_name": os.environ.get("RUNNER_NAME"),
        "runner_arch": os.environ.get("RUNNER_ARCH"),
        "run_number": run_number,
        "mode": mode,
        "status": "S10_ADAPTIVE_QA_PASSED" if not failures else "S10_ADAPTIVE_QA_FAILED",
        "findings": findings,
        "failures": failures,
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "selection": False,
            "parameter_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": SAFETY,
    }
    receipt["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
