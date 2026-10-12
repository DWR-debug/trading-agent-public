"""Fail-closed Q220 source/PIT receipt-chain state shared by operations views."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PIN = "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
COUNT = 55
POP = "research/evidence/q220_as_filed_xbrl_population_latest.json"
COMP = "research/evidence/q220_historical_representation_pit_latest.json"
IND = "research/evidence/q220_independent_pit_reproduction_latest.json"
CONTRACT = "research/preregistrations/q220_as_filed_xbrl_population_contract_2026_10_06.json"
POP_CODE = "automation/q220_as_filed_xbrl_population_gate.py"
COMP_CODE = "automation/q220_historical_representation_pit.py"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def fingerprint(obj: dict[str, Any]) -> str:
    body = dict(obj)
    body.pop("receipt_fingerprint", None)
    return sha(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))

def load(root: Path, path: str) -> dict[str, Any]:
    try:
        obj = json.loads((root / path).read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def intact(obj: dict[str, Any]) -> bool:
    fp = obj.get("receipt_fingerprint")
    return isinstance(fp, str) and len(fp) == 64 and all(c in "0123456789abcdef" for c in fp.lower()) and fingerprint(obj) == fp

def evaluate_q220_receipt_chain(root: Path = ROOT) -> dict[str, Any]:
    pop, comp, ind = load(root, POP), load(root, COMP), load(root, IND)
    try:
        contract_sha = sha((root / CONTRACT).read_bytes())
        pop_code_sha = sha((root / POP_CODE).read_bytes())
        comp_code_sha = sha((root / COMP_CODE).read_bytes())
    except OSError:
        contract_sha = pop_code_sha = comp_code_sha = ""

    pop_fp = str(pop.get("receipt_fingerprint") or "")
    pop_ok = (
        pop.get("candidate_id") == "Q220" and pop.get("mode") == "population"
        and pop.get("status") == "Q220_AS_FILED_XBRL_POPULATION_COMPLETED"
        and pop.get("failure_count") == 0 and pop.get("record_count") == COUNT
        and pop.get("row_count") == COUNT and len(pop.get("records", [])) == COUNT
        and pop_fp == PIN and intact(pop)
        and pop.get("contract_sha256") == contract_sha
        and pop.get("gate_code_sha256") == pop_code_sha
    )
    comp_fp = str(comp.get("receipt_fingerprint") or "")
    comp_present = bool(comp)
    comp_ok = (
        pop_ok and comp.get("record_type") == "q220_historical_representation_pit_compilation"
        and comp.get("candidate_id") == "Q220"
        and comp.get("status") == "Q220_HISTORICAL_REPRESENTATION_PIT_COMPILED"
        and comp.get("gate_positive") is True and comp.get("source_complete") is True
        and comp.get("textblock_mapping_complete") is True
        and comp.get("historical_prefix_order_valid") is True
        and comp.get("source_population_receipt_fingerprint") == pop_fp
        and comp.get("source_population_contract_sha256") == contract_sha
        and comp.get("source_population_gate_code_sha256") == pop.get("gate_code_sha256")
        and comp.get("compiler_code_sha256") == comp_code_sha
        and comp.get("record_count") == COUNT and comp.get("compiled_event_count") == COUNT
        and comp.get("verified_primary_document_count") == COUNT
        and comp.get("source_hash_failure_count") == 0
        and comp.get("unmapped_or_reconciled_textblock_gap_count") == 0
        and intact(comp) and comp.get("scientific_evidence") is False
        and comp.get("performance_authorization") is False
        and comp.get("holdout_selection") is False and comp.get("ranking") is False
        and comp.get("tuning") is False and comp.get("promotion") is False
        and comp.get("live_execution") is False
        and comp.get("safety", {}).get("paper_only") is True
        and comp.get("safety", {}).get("live_trading_enabled") is False
        and comp.get("safety", {}).get("orders_enabled") is False
        and comp.get("safety", {}).get("automatic_promotion") is False
    )
    ind_fp = str(ind.get("receipt_fingerprint") or "")
    checks = ind.get("checks")
    ind_present = bool(ind)
    ind_ok = (
        comp_ok and ind.get("record_type") == "q220_independent_pit_reproduction"
        and ind.get("candidate_id") == "Q220" and ind.get("status") == "Q220_INDEPENDENT_PIT_REPRODUCED"
        and ind.get("gate_positive") is True and ind.get("trial_id") == "Q-2026-10-06-Q220-AS-FILED-XBRL-REPAIR"
        and ind.get("upstream", {}).get("compiler_receipt_fingerprint") == comp_fp
        and ind.get("upstream", {}).get("population_receipt_fingerprint") == pop_fp
        and ind.get("upstream", {}).get("population_contract_sha256") == contract_sha
        and ind.get("upstream", {}).get("population_gate_code_sha256") == pop.get("gate_code_sha256")
        and ind.get("record_count") == COUNT and ind.get("compiler_event_count") == COUNT
        and ind.get("independently_retrieved_documents") == COUNT
        and ind.get("source_hash_failure_count") == 0 and ind.get("identity_mismatch_count") == 0
        and ind.get("prefix_mismatch_count") == 0 and ind.get("structured_mismatch_count") == 0
        and ind.get("textblock_mismatch_count") == 0 and ind.get("change_state_mismatch_count") == 0
        and ind.get("no_textblock_observed_count") == 5
        and len(ind.get("no_textblock_observed_record_keys", [])) == 5
        and isinstance(checks, dict) and bool(checks) and all(v is True for v in checks.values())
        and ind.get("errors") == [] and intact(ind)
        and ind.get("scientific_evidence") is False
        and ind.get("performance_authorization") is False and ind.get("performance_authorized") is False
        and ind.get("holdout_selection") is False and ind.get("ranking") is False
        and ind.get("tuning") is False and ind.get("promotion") is False and ind.get("live_execution") is False
        and ind.get("safety", {}).get("paper_only") is True
        and ind.get("safety", {}).get("live_trading_enabled") is False
        and ind.get("safety", {}).get("orders_enabled") is False
        and ind.get("safety", {}).get("automatic_promotion") is False
    )

    if not pop_ok:
        stage, status, detail, gate = "As-filed population + mapping", "blocked", "Population receipt or its frozen/current source pins are invalid or stale.", "reconcile fixed-population receipt and current source/contract pins"
    elif not comp_ok:
        stage, status = "Historical prefix / representation-gap PIT compiler", ("blocked" if comp_present else "ready")
        detail = "Existing compiler receipt fails code, source-linkage, completeness, digest or safety validation." if comp_present else "Fixed population is positive; compile and validate historical prefixes and representation states."
        gate = str(comp.get("next_gate") or ("historical prefix/acceptance-time PIT representation-state compiler" if not comp_present else "reconcile the current compiler receipt and frozen source linkage"))
    elif not ind_ok:
        stage, status = "Independent PIT reproduction", ("blocked" if ind_present else "ready")
        detail = "Independent receipt fails upstream linkage, mismatch, digest or safety validation." if ind_present else "Compiler is positive for all 55 records; independent retrieval/parse remains the next gate."
        gate = "independent PIT reproduction on an independent retrieval/parse path"
    else:
        stage, status = "Bounded adversarial robustness review + formal trial-governance reconciliation", "ready"
        detail = "Population, compiler and independent reproduction are positive for 55 records; zero hash, identity, prefix, structured or TextBlock mismatches. Five no-TextBlock observations remain explicitly missing. Source/PIT only; no performance authorization."
        gate = str(ind.get("next_gate") or "bounded adversarial robustness review and formal trial-governance reconciliation; no performance authorization")

    milestones = [
        {"label": "Design contract", "status": "complete", "progress": 100, "detail": "Frozen eight-issuer universe and exact representation contract."},
        {"label": "As-filed population + TextBlock/XSD/presentation mapping", "status": "complete" if pop_ok else "blocked", "progress": 100 if pop_ok else 0, "detail": "Pinned 55-record fixed population." if pop_ok else "Population receipt or source pin is not current and positive."},
        {"label": "Historical prefix / representation-gap PIT compiler", "status": "complete" if comp_ok else ("ready" if pop_ok and not comp_present else "blocked"), "progress": 100 if comp_ok else 0, "detail": "55/55 historical events compiled with zero source/mapping failures." if comp_ok else detail},
        {"label": "Independent PIT reproduction", "status": "complete" if ind_ok else ("ready" if comp_ok and not ind_present else "blocked"), "progress": 100 if ind_ok else 0, "detail": "Independent retrieval/parser agrees across 55 records." if ind_ok else "No current positive independent receipt."},
        {"label": "Bounded adversarial robustness + governance reconciliation", "status": "ready" if ind_ok else "blocked", "progress": 0, "detail": gate if ind_ok else "Closed until independent PIT is positive."},
    ]
    return {
        "population_positive": pop_ok, "compiler_positive": comp_ok, "independent_positive": ind_ok,
        "population_receipt_fingerprint": pop_fp or None, "compiler_receipt_fingerprint": comp_fp or None,
        "independent_receipt_fingerprint": ind_fp or None, "record_count": COUNT,
        "no_textblock_observed_count": 5 if ind_ok else None, "current_milestone": stage,
        "current_milestone_status": status, "current_milestone_progress_percent": 0,
        "current_milestone_detail": detail, "next_gate": gate, "milestones": milestones,
        "next_workpack_required": bool(ind_ok),
        "scientific_evidence": False, "performance_authorization_allowed": False,
    }
