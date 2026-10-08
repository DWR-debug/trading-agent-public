"""Issue a single explicit Q218 performance authorization after current G4 and exact Master CI.

The authorization enables only the governance permission for one future fixed one-shot
performance execution. It does not create an execution trigger and does not change
paper-only/live safety invariants.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research/preregistrations/q218_mandatory_voluntary_disclosure_2026_10_08.json"
RECONCILE = ROOT / "research/evidence/q218_prereg_authorization_reconcile_latest.json"
REGISTRY = ROOT / "research/governance/active_research_registry.json"
AUTH = ROOT / "research/authorizations/q218_performance_2026_10_08.json"

TRIAL_ID = "T-2026-10-08-Q218-PERFORMANCE-01"
AUTH_ID = "AUTH-Q218-2026-10-08-ONE-SHOT-01"


def fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-ci-run-id", type=int, required=True)
    args = ap.parse_args()

    prereg = load(PREREG)
    reconcile = load(RECONCILE)
    registry = load(REGISTRY)

    if prereg.get("trial_id") != TRIAL_ID:
        raise RuntimeError("Q218 trial id mismatch")
    if prereg.get("status") != "FROZEN_PREREGISTRATION_RECONCILED":
        raise RuntimeError("Q218 preregistration is not frozen/reconciled")
    if reconcile.get("status") != "Q218_FROZEN_PREREGISTRATION_AND_AUTHORIZATION_RECONCILED":
        raise RuntimeError("Q218 G4 receipt is not positive")
    if reconcile.get("checks", {}).get("candidate_contract_frozen") is not True:
        raise RuntimeError("Q218 candidate contract is not frozen")
    if reconcile.get("checks", {}).get("source_gate_current") is not True:
        raise RuntimeError("Q218 source gate is stale")
    if reconcile.get("checks", {}).get("event_pair_gate_current") is not True:
        raise RuntimeError("Q218 event-pair gate is stale")
    if reconcile.get("checks", {}).get("independent_pit_current") is not True:
        raise RuntimeError("Q218 independent PIT is stale")

    for key in ("candidate_selection_used", "holdout_selection_used", "parameter_search",
                "threshold_search", "horizon_search", "asset_search", "variant_search", "ranking"):
        if prereg.get("selection", {}).get(key) is not False:
            raise RuntimeError(f"Q218 prereg selection boundary invalid: {key}")

    safety = prereg.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False or safety.get("orders_enabled") is not False or safety.get("automatic_promotion") is not False:
        raise RuntimeError("Q218 safety invariant violated")

    active_trials = registry.setdefault("active_trials", [])
    existing = next((x for x in active_trials if isinstance(x, dict) and x.get("trial_id") == TRIAL_ID), None)

    authorization = {
        "schema_version": "1.0",
        "record_type": "q218_explicit_one_shot_performance_authorization",
        "authorization_id": AUTH_ID,
        "candidate_id": "Q218",
        "trial_id": TRIAL_ID,
        "authorized": True,
        "performance_execution_authorized": True,
        "one_shot": True,
        "authorized_at_utc": datetime.now(timezone.utc).isoformat(),
        "authorization_basis": {
            "requested_by_user": True,
            "master_exact_ci_run_id": args.master_ci_run_id,
            "g4_reconcile_receipt_fingerprint": reconcile["receipt_fingerprint"],
            "preregistration_fingerprint": prereg["preregistration_fingerprint"],
        },
        "source_receipts": {
            "source_gate": reconcile["fingerprints"]["source_gate"],
            "event_pair_gate": reconcile["fingerprints"]["event_pair_gate"],
            "independent_pit": reconcile["fingerprints"]["independent_pit"],
        },
        "selection_used": False,
        "holdout_used_for_selection": False,
        "parameter_search": False,
        "threshold_search": False,
        "asset_search": False,
        "horizon_search": False,
        "variant_search": False,
        "family_ranking": False,
        "promotion_decision": False,
        "execution_trigger_created": False,
        "execution_workflow": None,
        "execution_readiness_note": "Authorization is valid, but the Q218 public repository currently has no fixed performance executor. No execution trigger is created until an exact executor and input bundle are frozen.",
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    authorization["authorization_fingerprint"] = fp(authorization)

    if existing is None:
        existing = {
            "code": "Q218",
            "trial_id": TRIAL_ID,
            "class": "orthogonal_candidate_performance",
            "state": "PERFORMANCE_AUTHORIZED",
            "issue_number": 1094,
            "preregistration_path": str(PREREG.relative_to(ROOT)).replace("\\", "/"),
            "performance_authorization_allowed": True,
            "authorization_id": AUTH_ID,
        }
        active_trials.append(existing)
    else:
        existing["state"] = "PERFORMANCE_AUTHORIZED"
        existing["performance_authorization_allowed"] = True
        existing["authorization_id"] = AUTH_ID

    AUTH.parent.mkdir(parents=True, exist_ok=True)
    AUTH.write_text(json.dumps(authorization, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "Q218_PERFORMANCE_AUTHORIZED",
        "authorization_id": AUTH_ID,
        "trial_id": TRIAL_ID,
        "authorization_fingerprint": authorization["authorization_fingerprint"],
        "performance_execution_authorized": True,
        "execution_trigger_created": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
