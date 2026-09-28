"""Fail-closed operational state summary for Q070."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DESIGN=ROOT/"research/preregistrations/q070_fixed_candidate_validation_2026_09_28.json"
PERF_PREREG=ROOT/"research/preregistrations/q070_performance_2026_09_28.json"
COVERAGE=ROOT/"research/evidence/q070_coverage_result.json"
PIT=ROOT/"research/evidence/q070_pit_result.json"
AUTH=ROOT/"research/authorizations/q070_performance_2026_09_28.json"
RESULT=ROOT/"research/evidence/q070_performance_result.json"
LEDGER=ROOT/"research/evidence/trial_ledger.json"
PERF_ID="T-2026-09-28-070-PERFORMANCE"
COVERAGE_ID="T-2026-09-28-070-COVERAGE"
PIT_ID="T-2026-09-28-070-PIT"
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}
AUTH_SAFETY={"PAPER_ONLY":True,"LIVE_TRADING_ENABLED":False,"ORDERS_ENABLED":False,"AUTOMATIC_PROMOTION":False}

def _load(path):
    try: data=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError): return None
    return data if isinstance(data,dict) else None

def summarize(repo_root: Path=ROOT):
    design=_load(repo_root/DESIGN.relative_to(ROOT))
    prereg=_load(repo_root/PERF_PREREG.relative_to(ROOT))
    coverage=_load(repo_root/COVERAGE.relative_to(ROOT))
    pit=_load(repo_root/PIT.relative_to(ROOT))
    auth=_load(repo_root/AUTH.relative_to(ROOT))
    result=_load(repo_root/RESULT.relative_to(ROOT))
    ledger=_load(repo_root/LEDGER.relative_to(ROOT)) or {}
    trials=ledger.get("trials",[]) if isinstance(ledger.get("trials",[]),list) else []
    ledger_ids={x.get("trial_id") for x in trials if isinstance(x,dict)}
    blockers=[]
    if design is None:
        blockers.append("Q070 design preregistration missing")
        return _state("DESIGN_FROZEN",blockers,coverage,pit,auth,result,ledger_ids,prereg)
    if design.get("status")!="PREREGISTERED_DESIGN_ONLY": blockers.append("Q070 design status invalid")
    if design.get("source_candidate_bank",{}).get("definitions_locked") is not True: blockers.append("Q070 Q069 candidate definitions are not locked")
    state="DESIGN_FROZEN"
    if prereg is None:
        blockers.append("Q070 performance preregistration not materialized by coverage")
    else:
        if prereg.get("trial_id")!=PERF_ID or prereg.get("status")!="PREREGISTERED_PERFORMANCE": blockers.append("Q070 performance preregistration identity/status invalid")
        if prereg.get("selection_used") is not False or prereg.get("holdout_used_for_selection") is not False: blockers.append("Q070 performance preregistration records selection")
        if prereg.get("safety")!=SAFETY: blockers.append("Q070 performance preregistration safety invalid")
    for label,payload,tid,expected in (("coverage",coverage,COVERAGE_ID,"COVERAGE_PASSED"),("pit",pit,PIT_ID,"PIT_PASSED")):
        if payload is None: blockers.append(f"{label} receipt missing"); continue
        if payload.get("trial_id")!=tid or payload.get("status")!=expected: blockers.append(f"{label} receipt identity/status invalid")
        if payload.get("selection_used") is not False or payload.get("performance_trial_authorized") is not False: blockers.append(f"{label} receipt records forbidden state")
        if payload.get("safety")!=SAFETY: blockers.append(f"{label} receipt safety invalid")
    if coverage is not None and pit is not None and coverage.get("status")=="COVERAGE_PASSED" and pit.get("status")=="PIT_PASSED" and not any("receipt" in x and "invalid" in x for x in blockers):
        state="PREFLIGHT_PASSED_WAITING_FOR_AUTO_AUTH"
        if auth is not None:
            if auth.get("authorized") is True and auth.get("performance_execution_authorized") is True and auth.get("execution_scope")=="Q070_FIXED_CANDIDATE_PERFORMANCE_ONLY" and auth.get("safety")==AUTH_SAFETY and auth.get("source_receipts",{}).get("coverage_result_fingerprint")==coverage.get("result_fingerprint") and auth.get("source_receipts",{}).get("pit_result_fingerprint")==pit.get("result_fingerprint"): state="PERFORMANCE_AUTHORIZED"
            else: blockers.append("Q070 performance authorization exists but is invalid")
    if result is not None:
        if result.get("trial_id")!=PERF_ID or result.get("status")!="COMPLETED": blockers.append("Q070 performance result identity/status invalid"); state="PERFORMANCE_EVIDENCE_INVALID"
        elif result.get("selection_used") is not False or result.get("holdout_used_for_selection") is not False or result.get("governance",{}).get("promotion_decision") is not False or result.get("governance",{}).get("automatic_promotion") is not False: blockers.append("Q070 performance result records forbidden selection/promotion"); state="PERFORMANCE_EVIDENCE_INVALID"
        elif result.get("coverage_prerequisite",{}).get("result_fingerprint")!=(coverage or {}).get("result_fingerprint") or result.get("pit_prerequisite",{}).get("result_fingerprint")!=(pit or {}).get("result_fingerprint"): blockers.append("Q070 performance result prerequisite fingerprint mismatch"); state="PERFORMANCE_EVIDENCE_INVALID"
        elif PERF_ID in ledger_ids: state="PERFORMANCE_RECONCILED"
        else: state="PERFORMANCE_COMPLETED_PENDING_LEDGER"
    if blockers and state not in {"PERFORMANCE_EVIDENCE_INVALID","PERFORMANCE_COMPLETED_PENDING_LEDGER"}: state="PREFLIGHT_BLOCKED"
    return _state(state,blockers,coverage,pit,auth,result,ledger_ids,prereg)

def _state(state,blockers,coverage,pit,auth,result,ledger_ids,prereg):
    return {"family":"Q070","state":state,"blocking_reasons":sorted(set(blockers)),"coverage_receipt":{"present":coverage is not None,"status":coverage.get("status") if coverage else None,"trial_id":coverage.get("trial_id") if coverage else None},"pit_receipt":{"present":pit is not None,"status":pit.get("status") if pit else None,"trial_id":pit.get("trial_id") if pit else None},"performance_authorization":{"present":auth is not None,"authorized":auth.get("authorized") if auth else None,"execution_scope":auth.get("execution_scope") if auth else None},"performance_result":{"present":result is not None,"status":result.get("status") if result else None,"trial_id":result.get("trial_id") if result else None},"performance_preregistration":{"present":prereg is not None,"status":prereg.get("status") if prereg else None,"trial_id":prereg.get("trial_id") if prereg else None},"ledger_reconciled":PERF_ID in ledger_ids,"no_selection_or_promotion":True,"paper_only":True}

if __name__=="__main__": print(json.dumps(summarize(),ensure_ascii=False,indent=2,sort_keys=True))