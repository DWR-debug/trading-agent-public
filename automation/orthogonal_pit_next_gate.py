#!/usr/bin/env python3
"""Deterministic next-gate compiler for the orthogonal research frontier.

This compiler does not perform market-performance analysis. It consumes frozen
candidate contracts and existing source/PIT receipts and emits the logically next
bounded research action. It is deliberately conservative: blocked or missing
inputs stay blocked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from automation.source_readiness_snapshot_guard import classify as classify_source_readiness

ROOT = Path(__file__).resolve().parents[1]

CANDIDATE_SPECS = ROOT / "research/candidates/orthogonal_candidate_specs_2026-10-05.json"

RECEIPTS = {
    "Q194": ROOT / "research/evidence/q193_q196_source_feasibility_latest.json",
    "Q195": ROOT / "research/evidence/q193_q196_source_feasibility_latest.json",
    "Q196": ROOT / "research/evidence/q193_q196_source_feasibility_latest.json",
    "Q197": ROOT / "research/evidence/q197_q198_source_feasibility_latest.json",
    "Q198": ROOT / "research/evidence/q198_pit_clock_census_latest.json",
    "Q199": ROOT / "research/evidence/q199_q201_source_feasibility_latest.json",
    "Q201": ROOT / "research/evidence/q199_q201_source_feasibility_latest.json",
    "Q186": ROOT / "research/evidence/q186_pit_readiness_r2_latest.json",
    "Q187-Q192-SOURCE": ROOT / "research/evidence/q187_q192_source_feasibility_latest.json",
    "Q187-Q192-PIT": ROOT / "research/evidence/q187_q192_pit_readiness_r1_latest.json",
    "Q188-Q192-CENSUS": ROOT / "research/evidence/q188_q192_pit_census_r2_latest.json",
    "Q202": ROOT / "research/evidence/q202_q204_information_timing_feasibility_latest.json",
    "Q203": ROOT / "research/evidence/q202_q204_information_timing_feasibility_latest.json",
    "Q204": ROOT / "research/evidence/q202_q204_information_timing_feasibility_latest.json",
}

FORBIDDEN = {
    "performance_authorized": False,
    "holdout_selection": False,
    "ranking": False,
    "tuning": False,
    "promotion": False,
    "live_execution": False,
}

NEXT_GATES = {
    "Q194": "BLOCKED_SOURCE_COMPONENTS",
    "Q195": "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT",
    "Q196": "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT",
    "Q197": "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT",
    "Q198": "CANDIDATE_SPECIFIC_CORRECTION_WITHDRAWAL_LINEAGE_AND_MAPPING",
    "Q199": "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT",
    "Q201": "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT",
    "Q202": "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT",
    "Q203": "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT",
    "Q204": "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT",
    "Q218": "HISTORICAL_SEC_MANDATORY_VOLUNTARY_PAIRING_AND_PIT",
    "Q219": "POST_FILING_OPTIONS_RESPONSE_PIT_REQUIRED",
    "Q220": "DETERMINISTIC_NARRATIVE_XBRL_MAPPING_AND_PIT",
    "Q221": "HISTORICAL_USASPENDING_PUBLIC_BOUNDARY_AND_ISSUER_MAPPING",
    "Q222": "HISTORICAL_SEC_IMPLEMENTATION_EVIDENCE_CLOCK_AND_ENTITY_MAPPING",
    "Q186": "READY_FOR_CITATION_PUBLICATION_ORDERING_AND_HISTORICAL_COMPLETENESS",
    "Q187-Q192": "READY_FOR_CANDIDATE_SPECIFIC_HISTORICAL_PIT_RECONSTRUCTION",
}

def sha256_json(obj: object) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

def load_json(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"missing artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def receipt_boundary(receipt: dict) -> dict:
    s = receipt.get("status")
    sb = receipt.get("scientific_boundary") or {}
    safety = receipt.get("safety") or {}
    return {
        "status": s,
        "scientific_boundary": {k: sb.get(k) for k in (
            "performance", "holdout_selection", "ranking", "selection",
            "parameter_search", "threshold_search", "horizon_search",
            "asset_search", "variant_search", "promotion", "live_execution"
        )},
        "safety": {k: safety.get(k) for k in (
            "paper_only", "PAPER_ONLY", "live_trading_enabled",
            "LIVE_TRADING_ENABLED", "orders_enabled", "ORDERS_ENABLED",
            "automatic_promotion", "AUTOMATIC_PROMOTION"
        )},
        "receipt_fingerprint": receipt.get("receipt_fingerprint"),
    }

def compile_state() -> dict:
    specs = load_json(CANDIDATE_SPECS)
    assert specs.get("schema_version") == "1.0"
    assert specs.get("shared_contract", {}).get("pre_formal_robustness_gate") is True
    assert specs.get("shared_contract", {}).get("performance_authorization") is False
    assert specs.get("shared_contract", {}).get("promotion_authorization") is False
    assert specs.get("shared_contract", {}).get("live_execution") is False

    ids = [c.get("id") for c in specs.get("candidates", [])]
    assert ids == ["Q194", "Q195", "Q196", "Q197", "Q199", "Q201", "Q202", "Q203", "Q204", "Q205", "Q215", "Q216", "Q217", "Q218", "Q219", "Q220", "Q221", "Q222"]

    candidates = []

    # Q202-Q204 are intentionally not mapped to a fabricated evidence receipt.
    # Until their bounded source-feasibility workflow produces a receipt, the
    # compiler emits SOURCE_FEASIBILITY_REQUIRED and remains non-authorizing.
    for cid in ids:
        if cid in {"Q202", "Q203", "Q204"}:
            receipt_path = RECEIPTS[cid]
            if receipt_path.is_file():
                receipt = load_json(receipt_path)
                result = {
                    "candidate_id": cid,
                    "next_gate": "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT",
                    "source_readiness_durability": classify_source_readiness(receipt),
                    "source_or_pit_receipt": receipt_boundary(receipt),
                    "execution_authorized": False,
                    "performance_allowed": False,
                }
                boundary = receipt.get("scientific_boundary") or {}
                if any(boundary.get(k) is True for k in ("performance", "holdout_selection", "ranking",
                                                          "selection", "parameter_search", "threshold_search",
                                                          "horizon_search", "asset_search", "variant_search",
                                                          "promotion", "live_execution")):
                    result["next_gate"] = "BLOCKED_SCIENTIFIC_BOUNDARY_VIOLATION"
                candidates.append(result)
            else:
                candidates.append({
                    "candidate_id": cid,
                    "next_gate": NEXT_GATES[cid],
                    "source_or_pit_receipt": None,
                    "execution_authorized": False,
                    "performance_allowed": False,
                })
            continue
        receipt_path = RECEIPTS.get(cid)
        if receipt_path is None or not receipt_path.is_file():
            candidates.append({
                "candidate_id": cid,
                "next_gate": NEXT_GATES.get(cid, "SOURCE_FEASIBILITY_REQUIRED"),
                "source_or_pit_receipt": None,
                "execution_authorized": False,
                "performance_allowed": False,
                "source_feasibility_required": True,
            })
            continue
        receipt = load_json(receipt_path)
        durability = classify_source_readiness(receipt)
        result = {
            "candidate_id": cid,
            "next_gate": NEXT_GATES[cid],
            "source_readiness_durability": durability,
            "source_or_pit_receipt": receipt_boundary(receipt),
            "execution_authorized": False,
            "performance_allowed": False,
        }
        if durability == "PROVISIONAL_LIVE_PROBE_ONLY" and cid not in {"Q194", "Q198"}:
            result["next_gate"] = "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"
        # Do not silently promote a nominally ready candidate if its receipt
        # explicitly records unsafe scientific-boundary fields.
        boundary = receipt.get("scientific_boundary") or {}
        if any(boundary.get(k) is True for k in ("performance", "holdout_selection", "ranking",
                                                  "selection", "parameter_search", "threshold_search",
                                                  "horizon_search", "asset_search", "variant_search",
                                                  "promotion", "live_execution")):
            result["next_gate"] = "BLOCKED_SCIENTIFIC_BOUNDARY_VIOLATION"
        candidates.append(result)

    # Q186 is outside the six fixed 2026-10-04 contracts but remains a live
    # deeper-PIT priority and is included to preserve the logical research chain.
    q186 = load_json(RECEIPTS["Q186"])
    candidates.append({
        "candidate_id": "Q186",
        "next_gate": NEXT_GATES["Q186"],
        "source_or_pit_receipt": receipt_boundary(q186),
        "execution_authorized": False,
        "performance_allowed": False,
    })

    q187 = load_json(RECEIPTS["Q187-Q192-SOURCE"])
    q187pit = load_json(RECEIPTS["Q187-Q192-PIT"])
    q188c = load_json(RECEIPTS["Q188-Q192-CENSUS"])
    candidates.append({
        "candidate_id": "Q187-Q192",
        "next_gate": NEXT_GATES["Q187-Q192"],
        "source_or_pit_receipt": {
            "source": receipt_boundary(q187),
            "pit_readiness": receipt_boundary(q187pit),
            "census": receipt_boundary(q188c),
        },
        "execution_authorized": False,
        "performance_allowed": False,
    })

    now = datetime.now(timezone.utc).isoformat()
    out = {
        "schema_version": "1.0",
        "receipt_type": "orthogonal_next_gate_compiler",
        "task_id": "Q-2026-10-04-ORTHOGONAL-NEXT-GATE",
        "generated_at_utc": now,
        "source_spec_sha256": sha256_json(specs),
        "status": "NEXT_LOGICAL_GATES_COMPILED_NO_PERFORMANCE",
        "candidates": candidates,
        "global_boundary": FORBIDDEN,
        "rules": {
            "completed_safe_rounds_may_trigger_next_logical_round": True,
            "duplicate_running_work_forbidden": True,
            "no_performance_from_this_compiler": True,
            "blocked_inputs_remain_blocked": True,
            "live_endpoint_source_readiness_is_provisional": True,
            "immutable_historical_binding_required_before_candidate_pit": True,
        },
    }
    out["receipt_fingerprint"] = sha256_json(out)
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    result = compile_state()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
