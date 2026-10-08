"""Q218 frozen preregistration + immutable authorization reconciliation.

This routine is idempotently re-run whenever upstream source/event/PIT fingerprints change; it never grants performance authority.

This gate freezes the candidate contract after the current independent PIT
reproduction. It reconciles the exact upstream receipt fingerprints and creates
an explicit *not-authorized* performance authorization record. It never grants
performance authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "research/candidates/orthogonal_candidate_specs_2026-10-05.json"
INDEX_PATH = ROOT / "research/evidence/q218_focus_gate_receipt_index_latest.json"
INDEP_PATH = ROOT / "research/evidence/q218_independent_architecture_pit_reproduction_latest.json"
REGISTRY_PATH = ROOT / "research/governance/active_research_registry.json"

PREREG_PATH = ROOT / "research/preregistrations/q218_mandatory_voluntary_disclosure_2026_10_08.json"
AUTH_PATH = ROOT / "research/authorizations/q218_performance_2026_10_08.json"
RECEIPT_PATH = ROOT / "research/evidence/q218_prereg_authorization_reconcile_latest.json"
PERFORMANCE_CONTRACT_PATH = ROOT / "research/governance/q218_performance_contract_2026_10_08.json"
INPUT_BUNDLE_RECEIPT_PATH = ROOT / "research/evidence/q218_performance_input_bundle_latest.json"
ROBUSTNESS_RECEIPT_PATH = ROOT / "research/evidence/q218_pre_performance_robustness_latest.json"
CANDIDATE_ROBUSTNESS_RECEIPT_PATH = ROOT / "research/evidence/q218_candidate_robustness_latest.json"

FORBIDDEN_TRUE = (
    "performance_authorization",
    "promotion_authorization",
    "live_execution",
    "holdout_selection",
    "ranking",
    "tuning",
    "parameter_search",
    "threshold_search",
    "horizon_search",
    "asset_selection",
    "variant_search",
)


def sha256_json(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def load(path: Path) -> dict:
    if not path.is_file():
        raise RuntimeError(f"missing input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_no_forbidden_true(obj: dict, label: str) -> None:
    for key in FORBIDDEN_TRUE:
        if obj.get(key) is True:
            raise RuntimeError(f"{label}: forbidden boundary {key}=true")


def build() -> tuple[dict, dict, dict]:
    spec_root = load(SPEC_PATH)
    spec = next((x for x in spec_root.get("candidates", []) if x.get("id") == "Q218"), None)
    if not isinstance(spec, dict):
        raise RuntimeError("Q218 candidate contract missing")

    index = load(INDEX_PATH)
    indep = load(INDEP_PATH)
    registry = load(REGISTRY_PATH)
    performance_contract = load(PERFORMANCE_CONTRACT_PATH)
    input_bundle = load(INPUT_BUNDLE_RECEIPT_PATH) if INPUT_BUNDLE_RECEIPT_PATH.is_file() else None
    robustness = load(ROBUSTNESS_RECEIPT_PATH) if ROBUSTNESS_RECEIPT_PATH.is_file() else None
    candidate_robustness = load(CANDIDATE_ROBUSTNESS_RECEIPT_PATH) if CANDIDATE_ROBUSTNESS_RECEIPT_PATH.is_file() else None
    if performance_contract.get("trial_id") != "T-2026-10-08-Q218-PERFORMANCE-01":
        raise RuntimeError("Q218 performance contract trial identity mismatch")
    if performance_contract.get("status") != "FROZEN_PRE_PERFORMANCE_CONTRACT":
        raise RuntimeError("Q218 performance contract is not frozen")

    if index.get("status") != "Q218_SOURCE_AND_EVENT_PAIR_GATES_COMPLETE":
        raise RuntimeError("Q218 source/event receipt index is not positive-complete")
    if index.get("source_gate", {}).get("verified_positive_complete") is not True:
        raise RuntimeError("Q218 source gate is not positive-complete")
    if index.get("event_pair_gate", {}).get("verified_positive_complete") is not True:
        raise RuntimeError("Q218 event-pair gate is not positive-complete")

    source_fp = index["source_gate"]["receipt_fingerprint"]
    event_fp = index["event_pair_gate"]["receipt_fingerprint"]
    if indep.get("status") != "Q218_INDEPENDENT_ARCHITECTURE_PIT_REPRODUCED":
        raise RuntimeError("Q218 independent PIT receipt is not positive")
    if indep.get("upstream_receipts", {}).get("source_receipt_fingerprint") != source_fp:
        raise RuntimeError("Q218 independent receipt/source fingerprint mismatch")
    if indep.get("upstream_receipts", {}).get("event_pair_receipt_fingerprint") != event_fp:
        raise RuntimeError("Q218 independent receipt/event fingerprint mismatch")
    if indep.get("reproduction", {}).get("all_checks_passed") is not True:
        raise RuntimeError("Q218 independent reproduction checks are not all positive")
    if indep.get("scientific_boundary", {}).get("performance", False):
        raise RuntimeError("Q218 independent receipt crosses performance boundary")
    assert_no_forbidden_true(indep.get("scientific_boundary", {}), "Q218 independent scientific boundary")

    registry_candidates = [
        x for x in registry.get("active_design_families", [])
        if isinstance(x, dict) and x.get("code") == "Q218"
    ]
    entry = registry_candidates[0] if registry_candidates else None
    if not isinstance(entry, dict):
        raise RuntimeError("Q218 design registry entry missing")
    if entry.get("performance_authorization_allowed") is not False:
        raise RuntimeError("Q218 registry already authorizes performance")

    trial_id = "T-2026-10-08-Q218-PERFORMANCE-01"
    prereg = {
        "schema_version": "1.0",
        "record_type": "q218_frozen_preregistration",
        "candidate_id": "Q218",
        "trial_id": trial_id,
        "status": "FROZEN_PREREGISTRATION_RECONCILED",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "contract": {
            "name": spec["name"],
            "mechanism": spec["mechanism"],
            "event_clock": spec["event_clock"],
            "features": spec["features"],
            "direction": spec["direction"],
            "cheap_falsifiers": spec["cheap_falsifiers"],
            "non_overlap": spec["non_overlap"],
        },
        "upstream_receipts": {
            "source_gate_receipt_fingerprint": source_fp,
            "event_pair_gate_receipt_fingerprint": event_fp,
            "independent_pit_receipt_fingerprint": indep["receipt_fingerprint"],
        },
        "performance_contract": {
            "path": "research/governance/q218_performance_contract_2026_10_08.json",
            "contract_sha256": hashlib.sha256(PERFORMANCE_CONTRACT_PATH.read_bytes()).hexdigest(),
            "revision": performance_contract.get("revision"),
        },
        "feature_construction": performance_contract["feature_construction"],
        "outcome_contract": performance_contract["outcome_contract"],
        "input_bundle_contract": performance_contract["input_bundle"],
        "independent_replication": performance_contract["replication_contract"],
        "input_bundle": (
            {
                "status": input_bundle.get("status"),
                "bundle_fingerprint": input_bundle.get("bundle_fingerprint"),
                "artifact_path": input_bundle.get("artifact_path"),
                "artifact_sha256": input_bundle.get("artifact_sha256"),
                "artifact": input_bundle.get("artifact"),
            } if isinstance(input_bundle, dict) and input_bundle.get("status") == "INPUT_BUNDLE_FROZEN" else None
        ),
        "pre_performance_robustness": (
            {
                "trial_id": robustness.get("trial_id"),
                "status": robustness.get("status"),
                "artifact_path": robustness.get("artifact_path"),
                "artifact_sha256": robustness.get("artifact_sha256"),
                "research_only": robustness.get("research_only"),
                "screen_is_descriptive_only": robustness.get("screen_is_descriptive_only"),
                "no_post_hoc_tuning": robustness.get("no_post_hoc_tuning"),
                "bundle_fingerprint": robustness.get("bundle_fingerprint"),
                "receipt_fingerprint": robustness.get("receipt_fingerprint"),
            } if isinstance(robustness, dict) and robustness.get("status") == "PRE_PERFORMANCE_ROBUSTNESS_COMPLETED" else None
        ),
        "candidate_robustness_gate": (
            candidate_robustness
            if isinstance(candidate_robustness, dict) and candidate_robustness.get("status") == "PRE_FORMAL_ROBUSTNESS_COMPLETED"
            else None
        ),
        "fixed_observation_scope": {
            "independent_pit_window_start": indep.get("fixed_window", {}).get("start"),
            "independent_pit_window_end": indep.get("fixed_window", {}).get("end"),
            "same_day_decision_use_allowed": indep.get("reproduction", {}).get("same_day_decision_use_allowed", False),
            "future_cutoff_used": indep.get("reproduction", {}).get("future_cutoff_used"),
        },
        "selection": {
            "candidate_selection_used": False,
            "holdout_selection_used": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "ranking": False,
        },
        "governance": {
            "performance_trial_authorized": False,
            "authorization_reconcile_complete": False,
            "one_shot_performance_requires_separate_explicit_authorization": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    prereg["preregistration_fingerprint"] = sha256_json(prereg)

    auth = {
        "schema_version": "1.0",
        "record_type": "q218_performance_authorization_reconcile",
        "authorization_id": "AUTH-Q218-2026-10-08-RECONCILE-01",
        "trial_id": trial_id,
        "authorized": False,
        "performance_execution_authorized": False,
        "one_shot": True,
        "status": "RECONCILED_NOT_AUTHORIZED",
        "preregistration_fingerprint": prereg["preregistration_fingerprint"],
        "upstream_receipts": prereg["upstream_receipts"],
        "authorization_basis": {
            "source_gate_receipt": source_fp,
            "event_pair_gate_receipt": event_fp,
            "independent_pit_receipt": indep["receipt_fingerprint"],
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
        "safety": prereg["safety"],
    }
    auth["authorization_reconcile_fingerprint"] = sha256_json(auth)

    receipt = {
        "schema_version": "1.0",
        "record_type": "q218_prereg_authorization_reconcile",
        "candidate_id": "Q218",
        "trial_id": trial_id,
        "status": "Q218_FROZEN_PREREGISTRATION_AND_AUTHORIZATION_RECONCILED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "candidate_contract_frozen": True,
            "source_gate_current": True,
            "event_pair_gate_current": True,
            "independent_pit_current": True,
            "preregistration_fingerprint_reconciled": True,
            "authorization_record_explicitly_not_authorized": True,
            "performance_execution_authorized": False,
        },
        "fingerprints": {
            "source_gate": source_fp,
            "event_pair_gate": event_fp,
            "independent_pit": indep["receipt_fingerprint"],
            "preregistration": prereg["preregistration_fingerprint"],
            "authorization_reconcile": auth["authorization_reconcile_fingerprint"],
        },
        "next_gate": "SEPARATE_EXPLICIT_ONE_SHOT_PERFORMANCE_AUTHORIZATION",
        "scientific_boundary": {
            "performance_authorized": False,
            "holdout_selection_allowed": False,
            "ranking_allowed": False,
            "parameter_search_allowed": False,
            "threshold_search_allowed": False,
            "horizon_search_allowed": False,
            "promotion_allowed": False,
            "live_execution_allowed": False,
        },
        "safety": prereg["safety"],
    }
    receipt["receipt_fingerprint"] = sha256_json(receipt)
    return prereg, auth, receipt


def existing_reconcile_is_current() -> tuple[bool, dict | None]:
    try:
        prereg = load(PREREG_PATH)
        auth = load(AUTH_PATH)
        receipt = load(RECEIPT_PATH)
    except (RuntimeError, json.JSONDecodeError):
        return False, None
    index = load(INDEX_PATH)
    indep = load(INDEP_PATH)
    if index.get("source_gate", {}).get("verified_positive_complete") is not True:
        return False, None
    if index.get("event_pair_gate", {}).get("verified_positive_complete") is not True:
        return False, None
    source_fp = index.get("source_gate", {}).get("receipt_fingerprint")
    event_fp = index.get("event_pair_gate", {}).get("receipt_fingerprint")
    if indep.get("status") != "Q218_INDEPENDENT_ARCHITECTURE_PIT_REPRODUCED":
        return False, None
    if indep.get("upstream_receipts", {}).get("source_receipt_fingerprint") != source_fp:
        return False, None
    if indep.get("upstream_receipts", {}).get("event_pair_receipt_fingerprint") != event_fp:
        return False, None
    if prereg.get("status") != "FROZEN_PREREGISTRATION_RECONCILED":
        return False, None
    if auth.get("authorized") is not False or auth.get("performance_execution_authorized") is not False:
        return False, None
    if receipt.get("status") != "Q218_FROZEN_PREREGISTRATION_AND_AUTHORIZATION_RECONCILED":
        return False, None
    if receipt.get("fingerprints", {}).get("source_gate") != source_fp:
        return False, None
    if receipt.get("fingerprints", {}).get("event_pair_gate") != event_fp:
        return False, None
    if receipt.get("fingerprints", {}).get("independent_pit") != indep.get("receipt_fingerprint"):
        return False, None
    if receipt.get("fingerprints", {}).get("preregistration") != prereg.get("preregistration_fingerprint"):
        return False, None
    if receipt.get("fingerprints", {}).get("authorization_reconcile") != auth.get("authorization_reconcile_fingerprint"):
        return False, None
    return True, receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=ROOT / "research")
    args = ap.parse_args()

    current, receipt = existing_reconcile_is_current()
    if current and receipt is not None:
        print(json.dumps({
            "status": receipt["status"],
            "trial_id": receipt["trial_id"],
            "preregistration_fingerprint": receipt["fingerprints"]["preregistration"],
            "receipt_fingerprint": receipt["receipt_fingerprint"],
            "performance_execution_authorized": False,
            "idempotent_reuse": True,
        }, sort_keys=True))
        return 0

    prereg, auth, receipt = build()

    (args.output_dir / "preregistrations").mkdir(parents=True, exist_ok=True)
    (args.output_dir / "authorizations").mkdir(parents=True, exist_ok=True)
    (args.output_dir / "evidence").mkdir(parents=True, exist_ok=True)

    PREREG_PATH.write_text(json.dumps(prereg, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    AUTH_PATH.write_text(json.dumps(auth, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": receipt["status"],
        "trial_id": receipt["trial_id"],
        "preregistration_fingerprint": prereg["preregistration_fingerprint"],
        "receipt_fingerprint": receipt["receipt_fingerprint"],
        "performance_execution_authorized": False,
        "idempotent_reuse": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
