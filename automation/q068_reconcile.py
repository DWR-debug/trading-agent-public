"""Reconcile completed Q068 performance evidence into the immutable trial ledger.

This command only runs after a completed, pre-authorized Q068 performance result.
It never ranks arms and never promotes anything.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

TRIAL_ID = "T-2026-09-28-068-PERFORMANCE"
RESULT_PATH = Path("research/evidence/q068_performance_result.json")
LEDGER_PATH = Path("research/evidence/trial_ledger.json")


def reconcile(repo_root: Path = Path(".")) -> str:
    result_path = repo_root / RESULT_PATH
    ledger_path = repo_root / LEDGER_PATH
    result = json.loads(result_path.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    assert result["trial_id"] == TRIAL_ID
    assert result["status"] == "COMPLETED"
    assert result["performance_evaluation"] is True
    assert result["selection_used"] is False
    assert result["holdout_used_for_selection"] is False
    assert result["governance"]["promotion_decision"] is False
    assert result["governance"]["automatic_promotion"] is False
    assert result["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }

    trials = ledger.get("trials")
    if not isinstance(trials, list):
        raise ValueError("trial ledger has no list-valued 'trials'")

    existing = [item for item in trials if item.get("trial_id") == TRIAL_ID]
    if existing:
        raise ValueError("Q068 performance trial already exists; refusing duplicate ledger mutation")

    any_passed = any(
        bool(arm.get("all_gates_passed"))
        for arm in result["arms"].values()
    )
    trial_status = (
        "performance_completed_arm_passed_all_gates"
        if any_passed
        else "performance_completed_no_arm_passed_all_gates"
    )

    entry = {
        "trial_id": TRIAL_ID,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": trial_status,
        "research_family": "q068_e1_e2_fixed_rule_performance",
        "hypothesis": {
            "text": (
                "Evaluate the unchanged Q067 E1 alpha common-mode throttle and E2 "
                "turnover hysteresis mechanisms on the fresh Q068 symbol-disjoint "
                "universe under the unchanged 13-gate contract."
            )
        },
        "data_scope": {
            "research_count": result["research_periods"],
            "holdout_count": result["holdout_periods"],
            "holdout_used_for_selection": False,
            "symbols": result["symbols"],
            "requested_candles": result["requested_candles"],
            "target_common_candles": result["target_common_candles"],
            "coverage_prerequisite": result["coverage_prerequisite"],
            "pit_prerequisite": result["pit_prerequisite"],
        },
        "search_scope": {
            "raw_trial_count": len(result["arms"]),
            "independent_trial_count": 1,
            "parameter_search": False,
            "threshold_search": False,
            "variant_search": False,
            "asset_search": False,
            "horizon_search": False,
            "family_ranking": False,
        },
        "selection": {
            "selected": False,
            "selection_method": "none; all preregistered Q068 arms evaluated symmetrically",
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
            "validation_status": trial_status,
            "scientific_outcome": trial_status,
            "performance_result_fingerprint": result["report_fingerprint"],
            "arms": result["arms"],
            "performance_evaluation": True,
            "oos_evaluation": True,
            "holdout_evaluation": True,
            "holdout_selection_used": False,
            "promotion": False,
        },
        "safety": result["safety"],
    }

    trials.append(entry)
    ledger["generated_at"] = datetime.now(timezone.utc).isoformat()
    ledger_path.write_text(
        json.dumps(
            ledger,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )
    print("Q068 LEDGER RECONCILED:", trial_status)
    return trial_status


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    raise SystemExit(0 if reconcile(Path(args.repo_root)) else 1)
