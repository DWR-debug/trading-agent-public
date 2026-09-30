"""Freeze Q077-R1 performance metadata from completed coverage/PIT/input-freeze receipts."""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREREG=ROOT/"research/preregistrations/q077r1_performance_2026_09_30.json"
REGISTRY=ROOT/"research/governance/active_research_registry.json"
EXPECTED_SYMBOLS=["AJG","ALGN","AME","AOS","APH","AXON","BAH","BALL","BBWI","BRO","BWA","CDNS"]
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}

def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))

def sha256(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def main()->int:
    prereg=load(PREREG)
    registry=load(REGISTRY)
    coverage=load(ROOT/"research/evidence/q077r1_coverage_result.json")
    pit=load(ROOT/"research/evidence/q077r1_pit_result.json")
    freeze=load(ROOT/"research/evidence/q077r1_input_freeze_result.json")
    manifest=load(ROOT/"research/runs/q077r1_pit/T-2026-09-28-077R1-PIT/snapshot_manifest.json")
    bundle=load(ROOT/"research/runs/q077r1_input_bundle/T-2026-09-28-077R1-INPUT-FREEZE/input_bundle_manifest.json")
    assert prereg["trial_id"]=="T-2026-09-30-077R1-PERFORMANCE"
    assert prereg["status"]=="PREREGISTERED_PERFORMANCE_PREPARATION"
    assert coverage["trial_id"]=="T-2026-09-28-077R1-COVERAGE" and coverage["status"]=="COVERAGE_PASSED"
    assert pit["trial_id"]=="T-2026-09-28-077R1-PIT" and pit["status"]=="PIT_PASSED"
    assert freeze["trial_id"]=="T-2026-09-28-077R1-INPUT-FREEZE" and freeze["status"]=="INPUT_BUNDLE_FROZEN"
    assert coverage["performance_evaluation"] is False and pit["performance_evaluation"] is False and freeze["performance_evaluation"] is False
    assert coverage["selection_used"] is False and pit["selection_used"] is False and freeze["selection_used"] is False
    assert prereg["symbols"]==EXPECTED_SYMBOLS
    assert coverage["symbols"]==EXPECTED_SYMBOLS and pit["symbols"]==EXPECTED_SYMBOLS and freeze["symbols"]==EXPECTED_SYMBOLS
    assert manifest["snapshot_fingerprint"]==coverage["snapshot_fingerprint"]
    assert bundle["bundle_fingerprint"]==freeze["bundle_fingerprint"]
    prereg["status"]="PREREGISTERED_PERFORMANCE"
    dc=prereg["data_contract"]
    dc["coverage_result_fingerprint"]=coverage["result_fingerprint"]
    dc["snapshot_fingerprint"]=coverage["snapshot_fingerprint"]
    dc["pit_result_fingerprint"]=pit["result_fingerprint"]
    dc["input_bundle_fingerprint"]=freeze["bundle_fingerprint"]
    sc=prereg["source_contract"]
    sc["performance_runner_sha256"]=sha256(ROOT/"automation/q077r1_performance.py")
    sc["alpha_mechanism_sha256"]=sha256(ROOT/"automation/q067_alpha_mechanisms.py")
    sc["cost_contract_sha256"]=sha256(ROOT/"execution/cost_contract.py")
    sc["settings_sha256"]=sha256(ROOT/"config/settings.py")
    sc["input_freeze_sha256"]=sha256(ROOT/"automation/q077r1_input_freeze.py")
    prereg["governance"]["performance_trial_authorized"]=False
    prereg["prepared_from_master_sha"]=os.environ.get("GITHUB_SHA","UNVERIFIED")
    entry=next(x for x in registry["active_trials"] if str(x.get("code"))=="077R1")
    entry["trial_id"]=prereg["trial_id"]
    entry["class"]="fresh_validation"
    entry["state"]="PERFORMANCE_READY_FOR_AUTHORIZATION"
    entry["preregistration_path"]="research/preregistrations/q077r1_performance_2026_09_30.json"
    entry["performance_authorization_allowed"]=False
    entry["coverage_result"]={"status":coverage["status"],"selected_symbols":EXPECTED_SYMBOLS,"common_sessions":coverage["common_calendar_count"],"fingerprint":coverage["result_fingerprint"],"source_trial_id":coverage["trial_id"]}
    entry["pit_result"]={"status":pit["status"],"fingerprint":pit["result_fingerprint"],"source_trial_id":pit["trial_id"]}
    entry["input_bundle_result"]={"status":freeze["status"],"fingerprint":freeze["bundle_fingerprint"],"source_trial_id":freeze["trial_id"]}
    PREREG.write_text(json.dumps(prereg,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    REGISTRY.write_text(json.dumps(registry,ensure_ascii=False,indent=2,allow_nan=False)+"\\n",encoding="utf-8")
    print("Q077R1 PERFORMANCE PREREGISTRATION FROZEN")
    print("COVERAGE_FP="+coverage["result_fingerprint"])
    print("PIT_FP="+pit["result_fingerprint"])
    print("INPUT_FP="+freeze["bundle_fingerprint"])
    return 0

if __name__=="__main__": raise SystemExit(main())
