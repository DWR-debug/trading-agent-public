"""Deterministic S10 research-operations QA.

This is mechanical QA only. It does not invoke the local language model and
cannot authorize performance, ranking, selection, promotion, or live trading.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

TARGETS = (
    "docs/CURRENT_STATUS.md",
    "research/frontier/q185_q186_candidate_wave_2026_10_04.json",
    "research/frontier/q187_q192_candidate_wave_2026_10_04.json",
    "research/frontier/q193_q196_candidate_wave_2026_10_04.json",
    "research/governance/persistent_research_acceleration_contract.json",
    "research/governance/critical_research_quality_control.json",
    "automation/q185_q186_source_feasibility.py",
    "automation/q187_q192_source_feasibility.py",
    "automation/q193_q196_source_feasibility.py",
)

OPTIONAL_TARGETS = {
    "research/frontier/q193_q196_candidate_wave_2026_10_04.json",
    "automation/q193_q196_source_feasibility.py",
}

SAFETY = {
    "PAPER_ONLY": True,
    "LIVE_TRADING_ENABLED": False,
    "ORDERS_ENABLED": False,
    "AUTOMATIC_PROMOTION": False,
}

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.repo_root.resolve()
    findings = []
    failures = []

    for rel in TARGETS:
        path = root / rel
        if not path.is_file():
            if rel not in OPTIONAL_TARGETS:
                failures.append(f"missing:{rel}")
            continue
        findings.append({"path": rel, "sha256": digest(path), "bytes": path.stat().st_size})

    for rel in (
        "research/frontier/q185_q186_candidate_wave_2026_10_04.json",
        "research/frontier/q187_q192_candidate_wave_2026_10_04.json",
        "research/frontier/q193_q196_candidate_wave_2026_10_04.json",
    ):
        path = root / rel
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"json:{rel}:{exc}")
            continue
        if payload.get("status") != "DESIGN_INVENTORY_ONLY":
            failures.append(f"inventory_status:{rel}")
        policy = payload.get("policy", {})
        for key in ("performance_authorized", "holdout_selection_allowed", "parameter_search_allowed",
                    "asset_search_allowed", "threshold_search_allowed", "horizon_search_allowed",
                    "variant_search_allowed", "family_ranking_allowed", "automatic_promotion"):
            if policy.get(key) is not False:
                failures.append(f"governance:{rel}:{key}")

    contract = root / "research/governance/persistent_research_acceleration_contract.json"
    if contract.is_file():
        try:
            payload = json.loads(contract.read_text(encoding="utf-8"))
            if payload.get("status") != "ACTIVE":
                failures.append("acceleration_contract_not_active")
            safety = payload.get("non_negotiable_safety", {})
            if any(safety.get(k) != v for k, v in SAFETY.items()) or safety.get("paid_resources_allowed") is not False:
                failures.append("acceleration_contract_safety")
        except json.JSONDecodeError as exc:
            failures.append(f"acceleration_contract_json:{exc}")

    critical = root / "research/governance/critical_research_quality_control.json"
    if critical.is_file():
        try:
            payload = json.loads(critical.read_text(encoding="utf-8"))
            if payload.get("status") != "ACTIVE":
                failures.append("critical_quality_control_not_active")
            gate = payload.get("candidate_robustness_gate", {})
            if gate.get("required_before_any_formal_phase") is not True:
                failures.append("candidate_robustness_gate_not_required")
            if payload.get("immediate_replication", {}).get("required_for_any_future_full_formal_pass") is not True:
                failures.append("immediate_replication_not_required")
        except json.JSONDecodeError as exc:
            failures.append(f"critical_quality_control_json:{exc}")

    current = root / "docs/CURRENT_STATUS.md"
    if current.is_file():
        text = current.read_text(encoding="utf-8")
        required_markers = (
            "Permanent two-lane research mode: ACTIVE",
            "Universal pre-formal candidate robustness gate: **ACTIVE**",
            "No current candidate is authorized for promotion or live execution.",
        )
        for marker in required_markers:
            if marker not in text:
                failures.append(f"status_marker:{marker}")

    receipt = {
        "schema_version": "1.0",
        "receipt_type": "s10_mechanical_research_qa",
        "source_commit": os.environ.get("GITHUB_SHA"),
        "runner_name": os.environ.get("RUNNER_NAME"),
        "runner_arch": os.environ.get("RUNNER_ARCH"),
        "status": "S10_MECHANICAL_QA_PASSED" if not failures else "S10_MECHANICAL_QA_FAILED",
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
