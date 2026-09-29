"""Reconcile Q091 one-shot performance into the immutable trial ledger."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

TRIAL_ID="T-2026-09-29-091"
COVERAGE_ID="T-2026-09-29-091-COVERAGE"
PIT_ID="T-2026-09-29-091-PIT"
INPUT_ID="T-2026-09-29-091-INPUT-FREEZE"
RESULT_PATH=Path("research/evidence/q091_performance_result.json")
COVERAGE_PATH=Path("research/evidence/q091_coverage_result.json")
PIT_PATH=Path("research/evidence/q091_pit_result.json")
PREREG_PATH=Path("research/preregistrations/q091_fixed_portfolio_architecture_2026_09_29.json")
AUTH_PATH=Path("research/authorizations/q091_performance_2026_09_29.json")
REGISTRY_PATH=Path("research/governance/active_research_registry.json")
LEDGER_PATH=Path("research/evidence/trial_ledger.json")
RETIRED_AUTH_PATH=Path("research/governance/retired_authorizations.json")
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}


def load(root,path): return json.loads((root/path).read_text(encoding="utf-8"))


def reconcile(root:Path=Path("."),workflow_run_id:str="UNVERIFIED")->str:
    root=root.resolve()
    result=load(root,RESULT_PATH); coverage=load(root,COVERAGE_PATH); pit=load(root,PIT_PATH)
    prereg=load(root,PREREG_PATH); auth=load(root,AUTH_PATH)
    registry=load(root,REGISTRY_PATH); ledger=load(root,LEDGER_PATH)
    trials=ledger.get("trials")
    if not isinstance(trials,list): raise ValueError("trial ledger has no list-valued trials")
    if any(x.get("trial_id")==TRIAL_ID for x in trials):
        raise ValueError("Q091 performance trial already exists; refusing duplicate ledger mutation")

    assert result["trial_id"]==TRIAL_ID and result["status"]=="COMPLETED"
    assert result["performance_evaluation"] is True and result["oos_evaluation"] is True and result["holdout_evaluation"] is True
    for field in ("selection_used","holdout_used_for_selection","parameter_search","threshold_search","asset_search","horizon_search","variant_search","family_ranking"):
        assert result[field] is False, field
    assert result["governance"]["performance_trial_authorized"] is True
    assert result["governance"]["promotion_decision"] is False
    assert result["governance"]["automatic_promotion"] is False
    assert result["safety"]==SAFETY
    assert coverage["trial_id"]==COVERAGE_ID and coverage["status"]=="COVERAGE_PASSED"
    assert pit["trial_id"]==PIT_ID and pit["status"]=="PIT_PASSED"
    assert result["coverage_prerequisite"]["result_fingerprint"]==coverage["result_fingerprint"]
    assert result["pit_prerequisite"]["result_fingerprint"]==pit["result_fingerprint"]
    assert result["input_bundle_prerequisite"]["trial_id"]==INPUT_ID
    assert result["input_bundle_prerequisite"]["bundle_fingerprint"]==prereg["data_contract"]["input_bundle_fingerprint"]
    assert auth["authorized"] is True and auth["performance_execution_authorized"] is True and auth["one_shot"] is True
    assert auth["trial_id"]==TRIAL_ID
    assert auth["preregistration_fingerprint"]==_fp(prereg)
    active=next(x for x in registry.get("active_trials",[]) if x.get("code")=="091")
    assert active["trial_id"]==TRIAL_ID and active["performance_authorization_allowed"] is True

    any_passed=any(bool(arm.get("all_gates_passed")) for arm in result["arms"].values())
    trial_status="performance_completed_arm_passed_all_13_gates" if any_passed else "performance_completed_no_arm_passed_all_13_gates"
    entry={
      "trial_id":TRIAL_ID,"recorded_at":datetime.now(timezone.utc).isoformat(),"status":trial_status,
      "research_family":"fixed_portfolio_architecture_after_q090_diagnosis",
      "hypothesis":{"text":"Test two fixed portfolio constructions over the unchanged five-sleeve Q069 bank on a fresh symbol-disjoint universe under the unchanged 13-gate framework."},
      "data_scope":{"research_count":result["research_periods"],"holdout_count":result["holdout_periods"],
        "holdout_used_for_selection":False,"symbols":result["symbols"],"requested_candles":result["requested_candles"],
        "target_common_candles":result["target_common_candles"],"coverage_prerequisite":result["coverage_prerequisite"],
        "pit_prerequisite":result["pit_prerequisite"],"input_bundle_prerequisite":result["input_bundle_prerequisite"]},
      "search_scope":{"raw_trial_count":len(result["arms"]),"independent_trial_count":1,"parameter_search":False,
        "threshold_search":False,"variant_search":False,"asset_search":False,"horizon_search":False,"family_ranking":False},
      "selection":{"selected":False,"selection_method":"none; both preregistered Q091 variants evaluated symmetrically",
        "selection_metric":None,"holdout_used_for_selection":False},
      "statistical_evidence":{"psr_probability":None,"dsr_probability":None,"pbo_probability":None,"trial_sharpes":None,
        "independent_trial_count":1,"ready":False},
      "outcome":{"validation_status":trial_status,"scientific_outcome":trial_status,
        "performance_result_fingerprint":result["report_fingerprint"],"variants":result["arms"],
        "performance_evaluation":True,"oos_evaluation":True,"holdout_evaluation":True,
        "holdout_selection_used":False,"promotion":False},
      "safety":SAFETY}
    trials.append(entry)
    active["performance_authorization_allowed"]=False
    active["state"]=trial_status.upper()
    active["performance_result"]={"trial_id":TRIAL_ID,"status":result["status"],"report_fingerprint":result["report_fingerprint"],"workflow_run_id":str(workflow_run_id)}

    retired=load(root,RETIRED_AUTH_PATH) if (root/RETIRED_AUTH_PATH).exists() else {
      "schema_version":1,"governance_contract_version":2,
      "description":"Historical authorization receipts retained for provenance but no longer eligible for execution.","entries":[]}
    entries=retired.setdefault("entries",[])
    if not any(x.get("path")==AUTH_PATH.as_posix() for x in entries):
        entries.append({"path":AUTH_PATH.as_posix(),"trial_id":TRIAL_ID,"status":"RETIRED_HISTORICAL_AUTHORIZATION"})
    ledger["generated_at"]=datetime.now(timezone.utc).isoformat()
    (root/LEDGER_PATH).write_text(json.dumps(ledger,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    (root/REGISTRY_PATH).write_text(json.dumps(registry,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    (root/RETIRED_AUTH_PATH).write_text(json.dumps(retired,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print("Q091 LEDGER RECONCILED:",trial_status)
    return trial_status


def _fp(value):
    return __import__("hashlib").sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("utf-8")
    ).hexdigest()


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--repo-root",default=".");p.add_argument("--workflow-run-id",default="UNVERIFIED")
    a=p.parse_args();raise SystemExit(0 if reconcile(Path(a.repo_root),str(a.workflow_run_id)) else 1)
