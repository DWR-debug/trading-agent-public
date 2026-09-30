"""C29 one-shot immutable reconciliation into the Trial Ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

TRIAL_ID = "T-2026-09-30-C29-PERFORMANCE-01"
PREREG_PATH = "research/preregistrations/c29_performance_2026_09_30.json"
RESULT_PATH = "research/evidence/c29_performance_result.json"
AUTH_PATH = "research/authorizations/c29_performance_2026_09_30.json"
REGISTRY_PATH = "research/governance/active_research_registry.json"
LEDGER_PATH = "research/evidence/trial_ledger.json"
RETIRED_PATH = "research/governance/retired_authorizations.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--workflow-run-id", required=True)
    args = parser.parse_args()
    root = args.repo_root

    prereg = _load(root / PREREG_PATH)
    result = _load(root / RESULT_PATH)
    auth = _load(root / AUTH_PATH)
    registry = _load(root / REGISTRY_PATH)
    ledger = _load(root / LEDGER_PATH)

    if prereg.get("trial_id") != TRIAL_ID or prereg.get("status") != "PREREGISTERED_PERFORMANCE":
        raise RuntimeError("C29 preregistration invalid at reconcile")
    if result.get("trial_id") != TRIAL_ID or result.get("status") not in {
        "PERFORMANCE_COMPLETED_ARM_PASSED_ALL_13_GATES",
        "PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES",
    }:
        raise RuntimeError("C29 performance result is not terminal")
    if result.get("selection_used") is not False or result.get("holdout_used_for_selection") is not False:
        raise RuntimeError("C29 result records selection")
    if result.get("governance", {}).get("promotion_decision") is not False:
        raise RuntimeError("C29 promotion state invalid")
    if result.get("safety") != {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }:
        raise RuntimeError("C29 result safety mismatch")

    expected_prereg_fp = _fp(prereg)
    if auth.get("trial_id") != TRIAL_ID or auth.get("authorized") is not True:
        raise RuntimeError("C29 authorization identity invalid")
    if auth.get("performance_execution_authorized") is not True or auth.get("one_shot") is not True:
        raise RuntimeError("C29 authorization flags invalid")
    if auth.get("preregistration_fingerprint") != expected_prereg_fp:
        raise RuntimeError("C29 authorization/preregistration fingerprint mismatch")
    if auth.get("input_bundle_fingerprint") != prereg["data_contract"]["input_bundle_fingerprint"]:
        raise RuntimeError("C29 authorization/input bundle fingerprint mismatch")

    entry = next((x for x in registry.get("active_trials", []) if x.get("code") == "C29P1"), None)
    if entry is None or entry.get("trial_id") != TRIAL_ID or entry.get("performance_authorization_allowed") is not True:
        raise RuntimeError("C29 registry authorization missing")

    key = "entries" if "entries" in ledger else "trials"
    entries = ledger.setdefault(key, [])
    status = (
        "performance_completed_arm_passed_all_13_gates"
        if any(arm.get("all_gates_passed") for arm in result.get("arms", {}).values())
        else "performance_completed_no_arm_passed_all_13_gates"
    )
    existing = next((x for x in entries if x.get("trial_id") == TRIAL_ID), None)
    if existing is not None:
        if existing.get("status") != status or existing.get("report_fingerprint") != result["report_fingerprint"]:
            raise RuntimeError("C29 duplicate ledger entry conflicts with immutable result")
        ledger_entry = existing
    else:
        ledger_entry = {
            "trial_id": TRIAL_ID,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "research_family": "frontier_c29_illusion_momentum_gap",
            "hypothesis": prereg["hypothesis"],
            "data_scope": {
                "research_count": result["research_periods"],
                "holdout_count": result["holdout_periods"],
                "holdout_used_for_selection": False,
                "symbols": result["symbols"],
                "target_common_candles": result["target_common_candles"],
                "lookback_sessions": result["lookback_sessions"],
            },
            "search_scope": {
                "parameter_search": False,
                "threshold_search": False,
                "asset_search": False,
                "horizon_search": False,
                "variant_search": False,
                "family_ranking": False,
            },
            "selection": {
                "selected": False,
                "selection_method": "none; two predeclared polarity arms evaluated symmetrically",
                "selection_metric": None,
                "holdout_used_for_selection": False,
            },
            "statistical_evidence": {
                "independent_trial_count": 1,
                "ready": False,
            },
            "outcome": {
                "scientific_outcome": "performance_completed",
                "performance_result_fingerprint": result["report_fingerprint"],
                "workflow_run_id": args.workflow_run_id,
                "arms": result["arms"],
            },
            "prerequisites": {
                "coverage": result["coverage_prerequisite"],
                "pit": result["pit_prerequisite"],
                "repair_discovery": result["repair_discovery_prerequisite"],
                "input_bundle": result["input_bundle_prerequisite"],
            },
            "governance": result["governance"],
            "safety": result["safety"],
        }
        entries.append(ledger_entry)

    entry["performance_authorization_allowed"] = False
    entry["state"] = status.upper()
    entry["performance_result"] = {
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "report_fingerprint": result["report_fingerprint"],
        "workflow_run_id": args.workflow_run_id,
    }

    retired = _load(root / RETIRED_PATH) if (root / RETIRED_PATH).exists() else {"schema_version": 1, "entries": []}
    if not any(x.get("trial_id") == TRIAL_ID for x in retired.get("entries", [])):
        retired.setdefault("entries", []).append({
            "path": AUTH_PATH,
            "trial_id": TRIAL_ID,
            "status": "RETIRED_HISTORICAL_AUTHORIZATION",
            "authorization_id": auth.get("authorization_id"),
        })

    (root / LEDGER_PATH).write_text(json.dumps(ledger, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    (root / REGISTRY_PATH).write_text(json.dumps(registry, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    (root / RETIRED_PATH).write_text(json.dumps(retired, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")

    print("C29 LEDGER RECONCILED:", status)
    print("C29 AUTHORIZATION CONSUMED")
    print("C29 REPORT FINGERPRINT:", result["report_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
