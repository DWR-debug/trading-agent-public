"""Reconcile completed Q070 performance evidence exactly once into trial_ledger.json."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

TRIAL_ID="T-2026-09-28-070-PERFORMANCE"
RESULT=Path("research/evidence/q070_performance_result.json")
COVERAGE=Path("research/evidence/q070_coverage_result.json")
PIT=Path("research/evidence/q070_pit_result.json")
AUTH=Path("research/authorizations/q070_performance_2026_09_28.json")
PREREG=Path("research/preregistrations/q070_performance_2026_09_28.json")
FREEZE=Path("research/evidence/q070_asset_freeze.json")
LEDGER=Path("research/evidence/trial_ledger.json")

def reconcile(root: Path="."):
    result=json.loads((root/RESULT).read_text(encoding="utf-8"))
    coverage=json.loads((root/COVERAGE).read_text(encoding="utf-8"))
    pit=json.loads((root/PIT).read_text(encoding="utf-8"))
    auth=json.loads((root/AUTH).read_text(encoding="utf-8"))
    prereg=json.loads((root/PREREG).read_text(encoding="utf-8"))
    freeze=json.loads((root/FREEZE).read_text(encoding="utf-8"))
    ledger=json.loads((root/LEDGER).read_text(encoding="utf-8"))
    assert result["trial_id"]==TRIAL_ID and result["status"]=="COMPLETED"
    assert coverage["trial_id"]=="T-2026-09-28-070-COVERAGE" and coverage["status"]=="COVERAGE_PASSED"
    assert pit["trial_id"]=="T-2026-09-28-070-PIT" and pit["status"]=="PIT_PASSED"
    assert auth["authorized"] is True and auth["performance_execution_authorized"] is True
    assert auth["execution_scope"]=="Q070_FIXED_CANDIDATE_PERFORMANCE_ONLY"
    assert auth["source_receipts"]["coverage_fingerprint"]==prereg["asset_freeze_fingerprint"]
    assert auth["source_receipts"]["pit_result_fingerprint"]==pit["result_fingerprint"]
    assert result["coverage_prerequisite"]["coverage_fingerprint"]==prereg["asset_freeze_fingerprint"]
    assert result["coverage_prerequisite"]["snapshot_fingerprint"]==coverage["snapshot_fingerprint"]
    assert result["pit_prerequisite"]["result_fingerprint"]==pit["result_fingerprint"]
    assert result.get("asset_freeze_fingerprint")==_fp(freeze)
    assert prereg["asset_freeze_fingerprint"]==_fp(freeze)
    assert prereg["symbols"]==result["symbols"]==freeze["symbols"]
    assert result["selection_used"] is False and result["holdout_used_for_selection"] is False
    assert result["governance"]["promotion_decision"] is False and result["governance"]["automatic_promotion"] is False
    trials=ledger.get("trials")
    if not isinstance(trials,list): raise ValueError("trial ledger missing trials")
    if any(x.get("trial_id")==TRIAL_ID for x in trials): raise ValueError("Q070 duplicate ledger entry")
    any_passed=any(bool(a.get("all_gates_passed")) for a in result["arms"].values())
    status="performance_completed_arm_passed_all_gates" if any_passed else "performance_completed_no_arm_passed_all_gates"
    entry={
        "trial_id":TRIAL_ID,
        "recorded_at":datetime.now(timezone.utc).isoformat(),
        "status":status,
        "research_family":"q070_orthogonal_ohlcv_fixed_candidate_performance",
        "hypothesis":{"text":"Evaluate five fixed Q069 OHLCV candidate mechanisms on a fresh symbol-disjoint Q070 universe under the unchanged 13-gate contract."},
        "data_scope":{"research_count":result["research_periods"],"holdout_count":result["holdout_periods"],"holdout_used_for_selection":False,"symbols":result["symbols"],"requested_candles":result["requested_candles"],"target_common_candles":result["target_common_candles"],"coverage_prerequisite":result["coverage_prerequisite"],"pit_prerequisite":result["pit_prerequisite"]},
        "search_scope":{"raw_trial_count":len(result["arms"]),"independent_trial_count":1,"parameter_search":False,"threshold_search":False,"variant_search":False,"asset_search":False,"horizon_search":False,"family_ranking":False},
        "selection":{"selected":False,"selection_method":"none; all five preregistered Q070 arms evaluated symmetrically","selection_metric":None,"holdout_used_for_selection":False},
        "statistical_evidence":{"psr_probability":None,"dsr_probability":None,"pbo_probability":None,"trial_sharpes":None,"independent_trial_count":1,"ready":False},
        "outcome":{"validation_status":status,"scientific_outcome":status,"performance_result_fingerprint":result["report_fingerprint"],"arms":result["arms"],"performance_evaluation":True,"oos_evaluation":True,"holdout_evaluation":True,"holdout_selection_used":False,"promotion":False},
        "safety":result["safety"]
    }
    trials.append(entry); ledger["generated_at"]=datetime.now(timezone.utc).isoformat()
    (root/LEDGER).write_text(json.dumps(ledger,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print("Q070 LEDGER RECONCILED:",status)
    return status

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--repo-root",default="."); a=p.parse_args()
    raise SystemExit(0 if reconcile(Path(a.repo_root)) else 1)
