"""Q094 one-shot immutable reconciliation into the trial ledger."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

TRIAL_ID="T-2026-09-29-094"
RESULT_PATH="research/evidence/q094_performance_result.json"
AUTH_PATH="research/authorizations/q094_performance_2026_09_29.json"
REGISTRY_PATH="research/governance/active_research_registry.json"
LEDGER_PATH="research/evidence/trial_ledger.json"
RETIRED_PATH="research/governance/retired_authorizations.json"


def load(p:Path):
    return json.loads(p.read_text(encoding="utf-8"))


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,default=Path("."))
    ap.add_argument("--workflow-run-id",required=True)
    args=ap.parse_args()
    root=args.repo_root
    result=load(root/RESULT_PATH)
    auth=load(root/AUTH_PATH)
    registry=load(root/REGISTRY_PATH)
    ledger=load(root/LEDGER_PATH)
    if result.get("trial_id")!=TRIAL_ID or result.get("status")!="COMPLETED":
        raise RuntimeError("Q094 result invalid")
    if result.get("selection_used") is not False or result.get("holdout_used_for_selection") is not False:
        raise RuntimeError("Q094 result records selection")
    if result.get("promotion") is not False:
        raise RuntimeError("Q094 promotion state invalid")
    if auth.get("trial_id")!=TRIAL_ID or auth.get("authorized") is not True or auth.get("performance_execution_authorized") is not True or auth.get("one_shot") is not True:
        raise RuntimeError("Q094 authorization invalid")
    if auth.get("preregistration_fingerprint") != __import__("hashlib").sha256(
        __import__("json").dumps(load(root/"research/preregistrations/q094_monthly_rebalance_q091_low_turnover_2026_09_29.json"),sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
    ).hexdigest():
        raise RuntimeError("Q094 authorization/preregistration fingerprint mismatch")
    entry=next((x for x in registry.get("active_trials",[]) if x.get("code")=="094"),None)
    if entry is None or entry.get("trial_id")!=TRIAL_ID or entry.get("performance_authorization_allowed") is not True:
        raise RuntimeError("Q094 registry authorization invalid")
    key="entries" if "entries" in ledger else "trials"
    entries=ledger.get(key,[])
    existing=next((x for x in entries if x.get("trial_id")==TRIAL_ID),None)
    if existing is not None:
        if existing.get("status")!="performance_completed_no_arm_passed_all_13_gates" or existing.get("report_fingerprint")!=result["report_fingerprint"]:
            raise RuntimeError("Q094 duplicate ledger entry conflicts with result")
    else:
        entries.append({
          "trial_id":TRIAL_ID,
          "recorded_at":datetime.now(timezone.utc).isoformat(),
          "status":"performance_completed_no_arm_passed_all_13_gates" if not any(x["all_gates_passed"] for x in result["arms"].values()) else "performance_completed_arm_passed_all_13_gates",
          "research_family":"low_turnover_monthly_rebalance_after_q093_cost_diagnosis",
          "hypothesis":load(root/"research/preregistrations/q094_monthly_rebalance_q091_low_turnover_2026_09_29.json")["hypothesis"],
          "data_scope":{"research_count":result["research_periods"],"holdout_count":result["holdout_periods"],"holdout_used_for_selection":False,"symbols":result["symbols"],"requested_candles":result["requested_candles"],"target_common_candles":result["target_common_candles"]},
          "search_scope":{"raw_trial_count":2,"independent_trial_count":1,"parameter_search":False,"threshold_search":False,"asset_search":False,"horizon_search":False,"variant_search":False,"family_ranking":False},
          "selection":{"selected":False,"selection_method":"none; both Q094 variants evaluated symmetrically","selection_metric":None,"holdout_used_for_selection":False},
          "statistical_evidence":{"psr_probability":None,"dsr_probability":None,"pbo_probability":None,"trial_sharpes":None,"independent_trial_count":1,"ready":False},
          "outcome":{"validation_status":entries[-1].get("status") if False else ("performance_completed_no_arm_passed_all_13_gates" if not any(x["all_gates_passed"] for x in result["arms"].values()) else "performance_completed_arm_passed_all_13_gates"),"scientific_outcome":"performance_completed","performance_result_fingerprint":result["report_fingerprint"],"workflow_run_id":args.workflow_run_id,"variants":result["arms"]},
          "governance":result["governance"],
          "safety":result["safety"]
        })
    ledger[key]=entries
    entry["performance_authorization_allowed"]=False
    entry["state"]= "PERFORMANCE_COMPLETED_ARM_PASSED_ALL_13_GATES" if any(x["all_gates_passed"] for x in result["arms"].values()) else "PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES"
    entry["performance_result"]={"trial_id":TRIAL_ID,"status":"COMPLETED","report_fingerprint":result["report_fingerprint"],"workflow_run_id":args.workflow_run_id}
    retired=load(root/RETIRED_PATH) if (root/RETIRED_PATH).exists() else {"schema_version":1,"entries":[]}
    rentry=next((x for x in retired.get("entries",[]) if x.get("trial_id")==TRIAL_ID),None)
    auth_record={"path":str(Path(AUTH_PATH).relative_to(root)).replace("\\","/"),"trial_id":TRIAL_ID,"status":"RETIRED_HISTORICAL_AUTHORIZATION","authorization_id":auth.get("authorization_id")}
    if rentry is None: retired.setdefault("entries",[]).append(auth_record)
    (root/LEDGER_PATH).write_text(json.dumps(ledger,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    (root/REGISTRY_PATH).write_text(json.dumps(registry,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    (root/RETIRED_PATH).write_text(json.dumps(retired,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Q094 LEDGER RECONCILED:",entry["state"])
    print("Q094 AUTHORIZATION CONSUMED")
    return 0

if __name__=="__main__": raise SystemExit(main())
