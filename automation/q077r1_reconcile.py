"""Q077-R1 one-shot immutable reconciliation into the trial ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

TRIAL_ID = "T-2026-09-30-077R1-PERFORMANCE"
RESULT_PATH = "research/evidence/q077r1_performance_result.json"
AUTH_PATH = "research/authorizations/q077r1_performance_2026_09_30.json"
PREREG_PATH = "research/preregistrations/q077r1_ast_literal_audit_2026_09_30.json"
REGISTRY_PATH = "research/governance/active_research_registry.json"
LEDGER_PATH = "research/evidence/trial_ledger.json"
RETIRED_PATH = "research/governance/retired_authorizations.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--workflow-run-id", required=True)
    args = ap.parse_args()
    root = args.repo_root

    result = load(root / RESULT_PATH)
    auth = load(root / AUTH_PATH)
    prereg = load(root / PREREG_PATH)
    registry = load(root / REGISTRY_PATH)
    ledger = load(root / LEDGER_PATH)

    if result.get("trial_id") != TRIAL_ID or result.get("status") != "COMPLETED":
        raise RuntimeError("Q077R1 result invalid")
    if result.get("selection_used") is not False or result.get("holdout_used_for_selection") is not False:
        raise RuntimeError("Q077R1 result records selection")
    if result.get("governance", {}).get("promotion_decision") is not False or result.get("governance", {}).get("automatic_promotion") is not False:
        raise RuntimeError("Q077R1 promotion state invalid")
    if result.get("safety") != {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }:
        raise RuntimeError("Q077R1 result safety invalid")
    if auth.get("trial_id") != TRIAL_ID or auth.get("authorized") is not True or auth.get("performance_execution_authorized") is not True or auth.get("one_shot") is not True:
        raise RuntimeError("Q077R1 authorization invalid")
    if fingerprint(prereg) != auth.get("preregistration_fingerprint"):
        raise RuntimeError("Q077R1 authorization/preregistration fingerprint mismatch")
    entry = next((x for x in registry.get("active_trials", []) if x.get("code") == "077R1"), None)
    if entry is None or entry.get("trial_id") != TRIAL_ID or entry.get("performance_authorization_allowed") is not True:
        raise RuntimeError("Q077R1 registry authorization invalid")

    key = "entries" if "entries" in ledger else "trials"
    entries = ledger.get(key, [])
    status = "performance_completed_arm_passed_all_13_gates" if any(x.get("all_gates_passed") for x in result.get("arms", {}).values()) else "performance_completed_no_arm_passed_all_13_gates"
    existing = next((x for x in entries if x.get("trial_id") == TRIAL_ID), None)
    if existing is not None:
        if existing.get("status") != status or existing.get("report_fingerprint") != result.get("report_fingerprint"):
            raise RuntimeError("Q077R1 duplicate ledger entry conflicts with result")
    else:
        entries.append({
            "trial_id": TRIAL_ID,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "research_family": prereg["research_family"],
            "hypothesis": "Fresh independent fixed-rule reproduction of the frozen Q067 E1/E2 mechanism set on the Q077-R1 symbol-disjoint universe; no new tuning or selection.",
            "data_scope": {
                "research_count": result["research_periods"],
                "holdout_count": result["holdout_periods"],
                "holdout_used_for_selection": False,
                "symbols": result["symbols"],
                "requested_candles": result["requested_candles"],
                "target_common_candles": result["target_common_candles"],
            },
            "search_scope": {
                "raw_trial_count": 1,
                "independent_trial_count": 1,
                "parameter_search": False,
                "threshold_search": False,
                "asset_search": False,
                "horizon_search": False,
                "variant_search": False,
                "family_ranking": False,
            },
            "selection": {
                "selected": False,
                "selection_method": "none; all Q077R1 arms evaluated symmetrically",
                "selection_metric": None,
                "holdout_used_for_selection": False,
            },
            "statistical_evidence": {
                "psr_probability": None,
                "dsr_probability": None,
                "pbo_probability": None,
                "trial_sharpes": None,
                "independent_trial_count": 1,
                "ready": False,
            },
            "outcome": {
                "validation_status": status,
                "scientific_outcome": "performance_completed",
                "performance_result_fingerprint": result["report_fingerprint"],
                "workflow_run_id": args.workflow_run_id,
                "variants": result["arms"],
            },
            "governance": result["governance"],
            "safety": result["safety"],
        })

    ledger[key] = entries
    entry["performance_authorization_allowed"] = False
    entry["state"] = "PERFORMANCE_COMPLETED_ARM_PASSED_ALL_13_GATES" if status == "performance_completed_arm_passed_all_13_gates" else "PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES"
    entry["performance_result"] = {
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "report_fingerprint": result["report_fingerprint"],
        "workflow_run_id": args.workflow_run_id,
    }

    retired = load(root / RETIRED_PATH) if (root / RETIRED_PATH).exists() else {"schema_version": 1, "entries": []}
    if not any(x.get("trial_id") == TRIAL_ID for x in retired.get("entries", [])):
        retired.setdefault("entries", []).append({
            "path": AUTH_PATH,
            "trial_id": TRIAL_ID,
            "status": "RETIRED_HISTORICAL_AUTHORIZATION",
            "authorization_id": auth.get("authorization_id"),
        })

    (root / LEDGER_PATH).write_text(json.dumps(ledger, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (root / REGISTRY_PATH).write_text(json.dumps(registry, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (root / RETIRED_PATH).write_text(json.dumps(retired, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("Q077R1 LEDGER RECONCILED:", entry["state"])
    print("Q077R1 AUTHORIZATION CONSUMED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
