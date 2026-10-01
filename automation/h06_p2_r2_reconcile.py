"""Durable reconciliation for the H06-P2-R2 corrective one-shot performance trial."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

TRIAL_ID="T-2026-10-01-H06P2R2-PERFORMANCE-01"
RESULT=Path("research/evidence/h06_p2_r2_performance_result.json")
PREREG=Path("research/preregistrations/h06_p2_r2_performance_2026_10_01.json")
AUTH=Path("research/authorizations/h06_p2_r2_performance_2026_10_01.json")
REGISTRY=Path("research/governance/active_research_registry.json")
LEDGER=Path("research/evidence/trial_ledger.json")
RETIRED=Path("research/governance/retired_authorizations.json")

def load(root,p): return json.loads((root/p).read_text(encoding="utf-8"))

def reconcile(root=Path("."),workflow_run_id="UNVERIFIED"):
    root=Path(root).resolve()
    result=load(root,RESULT); prereg=load(root,PREREG); auth=load(root,AUTH); registry=load(root,REGISTRY); ledger=load(root,LEDGER)
    assert result["trial_id"]==TRIAL_ID and result["status"]=="COMPLETED"
    assert result["performance_evaluation"] is True and result["holdout_evaluation"] is True
    for k in ("selection_used","holdout_used_for_selection","parameter_search","threshold_search","asset_search","horizon_search","variant_search","sector_map_search","family_ranking"):
        assert result[k] is False
    assert result["governance"]["performance_trial_authorized"] is True
    assert result["governance"]["promotion_decision"] is False and result["governance"]["automatic_promotion"] is False
    assert result["safety"]=={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}
    assert prereg["trial_id"]==TRIAL_ID and prereg["status"]=="PREREGISTERED_PERFORMANCE"
    assert result["input_bundle_prerequisite"]["bundle_fingerprint"]==prereg["input_contract"]["input_bundle_fingerprint"]
    assert auth["authorized"] is True and auth["performance_execution_authorized"] is True and auth["one_shot"] is True
    assert auth["preregistration_fingerprint"]==__import__("hashlib").sha256(json.dumps(prereg,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
    entry=next(x for x in registry["active_trials"] if x.get("code")=="H06-P2-R2")
    assert entry["trial_id"]==TRIAL_ID and entry["performance_authorization_allowed"] is True
    trials=ledger.setdefault("trials",[])
    if any(x.get("trial_id")==TRIAL_ID for x in trials): raise ValueError("H06P2R2 duplicate ledger entry refused")
    any_passed=any(bool(x.get("all_gates_passed")) for x in result["arms"].values())
    trial_status="performance_completed_arm_passed_all_13_gates" if any_passed else "performance_completed_no_arm_passed_all_13_gates"
    trials.append({
      "trial_id":TRIAL_ID,"recorded_at":datetime.now(timezone.utc).isoformat(),"status":trial_status,
      "research_family":"h06_p2_sector_residual_global_rank",
      "correction":{"type":"implementation_only","prior_trial_id":"T-2026-10-01-H06P2-PERFORMANCE-01","execution_incident_path":"research/evidence/h06_p2_performance_execution_incident.json"},
      "hypothesis":{"text":"Evaluate fixed sector-residual global Top5/Bottom5 against fixed raw global Top5/Bottom5 on the preregistered frozen H06 universe under the unchanged 13-gate contract."},
      "data_scope":{"research_count":result["research_periods"],"holdout_count":result["holdout_periods"],"holdout_used_for_selection":False,"symbols":result["symbols"],"requested_candles":result["requested_candles"],"target_common_candles":result["target_common_candles"],"evaluation_return_periods":result["evaluation_return_periods"],"coverage_prerequisite":result["coverage_prerequisite"],"pit_prerequisite":result["pit_prerequisite"],"input_bundle_prerequisite":result["input_bundle_prerequisite"]},
      "search_scope":{"raw_trial_count":2,"independent_trial_count":1,"parameter_search":False,"threshold_search":False,"variant_search":False,"asset_search":False,"sector_map_search":False,"horizon_search":False,"family_ranking":False},
      "selection":{"selected":False,"selection_method":"none; both preregistered arms evaluated symmetrically","selection_metric":None,"holdout_used_for_selection":False},
      "statistical_evidence":{"psr_probability":None,"dsr_probability":None,"pbo_probability":None,"trial_sharpes":None,"independent_trial_count":1,"ready":False},
      "outcome":{"validation_status":trial_status,"scientific_outcome":trial_status,"performance_result_fingerprint":result["report_fingerprint"],"arms":result["arms"],"control_relative_diagnostics":result["control_relative_diagnostics"],"performance_evaluation":True,"holdout_evaluation":True,"promotion":False},
      "safety":result["safety"]
    })
    entry["performance_authorization_allowed"]=False
    entry["state"]=trial_status.upper()
    entry["performance_result"]={"trial_id":TRIAL_ID,"status":result["status"],"report_fingerprint":result["report_fingerprint"],"workflow_run_id":str(workflow_run_id)}
    retired=load(root,RETIRED) if (root/RETIRED).exists() else {"schema_version":1,"governance_contract_version":2,"description":"Historical performance authorizations retained for provenance but no longer executable.","entries":[]}
    if not any(x.get("path")==AUTH.as_posix() for x in retired.setdefault("entries",[])):
        retired["entries"].append({"path":AUTH.as_posix(),"trial_id":TRIAL_ID,"status":"RETIRED_HISTORICAL_AUTHORIZATION"})
    ledger["generated_at"]=datetime.now(timezone.utc).isoformat()
    (root/LEDGER).write_text(json.dumps(ledger,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    (root/REGISTRY).write_text(json.dumps(registry,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    (root/RETIRED).write_text(json.dumps(retired,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print("H06P2R2_LEDGER_RECONCILED="+trial_status)
    return trial_status

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--repo-root",default="."); p.add_argument("--workflow-run-id",default="UNVERIFIED"); a=p.parse_args(); raise SystemExit(0 if reconcile(Path(a.repo_root),a.workflow_run_id) else 1)
