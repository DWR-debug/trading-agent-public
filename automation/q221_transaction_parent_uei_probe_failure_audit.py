"""Offline audit of the single authorized Q221 transaction-parent probe failure.

The probe stopped at the documented download-count preflight with HTTP 503.
This audit consumes only its immutable receipt plus the frozen request file;
it does not call USAspending or authorize a same-route retry.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SOURCE_RUN_ID = 38531250865
SOURCE_ARTIFACT_ID = 11878276634
SOURCE_ARTIFACT_NAME = "q221-transaction-parent-uei-probe-38531250865-1"
SOURCE_RECEIPT_FP = "310cb69e2f58e16effeb8af278b4009c528669caa597a26a39c8ddec92da52a8"
BOUNDARY_FP = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
BOUNDARY_BLOB = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
PROFILE_RUN_ID = "38305074104"
PROFILE_ARTIFACT_NAME = "q221-current-parent-identity-map-38305074104-1"
PROFILE_FP = "ae3a3263d5e7d2545dbdaed7ba7ff1cfe3d4cd00e0403352096dcce4d4797602"
EXPECTED_SEQUENCE = "2026-10-13T17:26:52Z"

class AuditError(ValueError): pass

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def fingerprint(v:dict[str,Any], field:str="receipt_fingerprint")->str:
    p=dict(v); p.pop(field,None)
    return sha(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8"))

def find_receipt(root:Path)->Path:
    if root.is_file(): return root
    found=sorted(root.rglob("q221-transaction-parent-uei-receipt.json"))
    if len(found)!=1:
        found=sorted(root.rglob("receipt.json"))
    if len(found)!=1: raise AuditError(f"Q221_FAILURE_RECEIPT_COUNT_INVALID:{len(found)}")
    return found[0]

def read_request(path:Path)->dict[str,str]:
    values={}
    for line_no,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line or line.strip()!=line or "=" not in line:
            raise AuditError(f"Q221_REQUEST_LINE_INVALID:{line_no}")
        k,v=line.split("=",1)
        if not k or not v or k in values:
            raise AuditError(f"Q221_REQUEST_KEY_VALUE_INVALID:{line_no}")
        values[k]=v
    expected={
        "RUN_Q221_TRANSACTION_PARENT_UEI_PROBE":"true",
        "REASON":"TEST_DOCUMENTED_TRANSACTION_DOWNLOAD_PARENT_UEI_FIELD_ON_SEVEN_FROZEN_PARENT_LEADS",
        "SOURCE_RECEIPT_PATH":"research/evidence/q221_historical_public_boundary_latest.json",
        "SOURCE_RECEIPT_GIT_BLOB_SHA":BOUNDARY_BLOB,
        "SOURCE_RECEIPT_FINGERPRINT":BOUNDARY_FP,
        "PROFILE_RUN_ID":PROFILE_RUN_ID,
        "PROFILE_ARTIFACT":PROFILE_ARTIFACT_NAME,
        "PROFILE_RECEIPT_FINGERPRINT":PROFILE_FP,
        "SAMPLE_COUNT":"7","MAX_ROWS":"10000","MAX_DOWNLOAD_BYTES":"20000000",
        "APPLY_HISTORICAL_MAPPING":"false","FREEZE_RECIPIENT_TO_ISSUER_MAPPING":"false",
        "PERFORMANCE":"false","HOLDOUT_SELECTION":"false","RANKING":"false","TUNING":"false","PROMOTION":"false","LIVE_EXECUTION":"false",
        "REQUEST_SEQUENCE":EXPECTED_SEQUENCE,
    }
    if values!=expected: raise AuditError("Q221_REQUEST_NOT_THE_FROZEN_SINGLE_ATTEMPT")
    return values

def build_audit(receipt:dict[str,Any], request:dict[str,str])->dict[str,Any]:
    if receipt.get("record_type")!="q221_transaction_parent_uei_feasibility_probe":
        raise AuditError("Q221_FAILURE_RECORD_TYPE_MISMATCH")
    if receipt.get("status")!="TRANSACTION_PARENT_UEI_PROBE_INCOMPLETE":
        raise AuditError("Q221_SOURCE_RECEIPT_NOT_THE_EXPECTED_FAILURE")
    if receipt.get("receipt_fingerprint")!=SOURCE_RECEIPT_FP or fingerprint(receipt)!=SOURCE_RECEIPT_FP:
        raise AuditError("Q221_FAILURE_RECEIPT_FINGERPRINT_MISMATCH")
    if receipt.get("request_sequence")!=request["REQUEST_SEQUENCE"]:
        raise AuditError("Q221_FAILURE_REQUEST_SEQUENCE_MISMATCH")
    if receipt.get("source_receipt_fingerprint")!=BOUNDARY_FP or receipt.get("source_receipt_git_blob_sha")!=BOUNDARY_BLOB:
        raise AuditError("Q221_BOUNDARY_SOURCE_PIN_MISMATCH")
    if receipt.get("profile_map_run_id")!=PROFILE_RUN_ID or receipt.get("profile_map_artifact")!=PROFILE_ARTIFACT_NAME or receipt.get("profile_map_receipt_fingerprint")!=PROFILE_FP:
        raise AuditError("Q221_PROFILE_MAP_PIN_MISMATCH")
    error=str(receipt.get("error") or "")
    if not error.startswith("API_HTTP_ERROR:503:"):
        raise AuditError("Q221_FAILURE_IS_NOT_THE_FROZEN_HTTP_503")
    if receipt.get("preflight_count") is not None or receipt.get("download_rows_matched")!=0 or receipt.get("matches")!=[]:
        raise AuditError("Q221_FAILURE_STAGE_OR_PARTIAL_DOWNLOAD_MISMATCH")
    if receipt.get("historical_parent_lineage_proven") is not False or receipt.get("recipient_to_issuer_mapping_frozen") is not False or receipt.get("historical_first_public_observation_proven") is not False:
        raise AuditError("Q221_FAIL_CLOSED_SAFETY_BOUNDARY_MISMATCH")
    core={
        "schema_version":1,"record_type":"q221_transaction_parent_probe_failure_audit",
        "candidate_id":"Q221","status":"Q221_TRANSACTION_PROBE_AUDITED_NO_GATE_CHANGE",
        "source_run_id":SOURCE_RUN_ID,"source_artifact_id":SOURCE_ARTIFACT_ID,"source_artifact_name":SOURCE_ARTIFACT_NAME,
        "source_receipt_fingerprint":SOURCE_RECEIPT_FP,"source_request_sequence":request["REQUEST_SEQUENCE"],
        "source_boundary_fingerprint":BOUNDARY_FP,"source_boundary_blob_sha":BOUNDARY_BLOB,
        "source_profile_run_id":PROFILE_RUN_ID,"source_profile_artifact_name":PROFILE_ARTIFACT_NAME,"source_profile_fingerprint":PROFILE_FP,
        "failure_stage":"DOCUMENTED_DOWNLOAD_COUNT_PREFLIGHT",
        "failure_class":"UPSTREAM_HTTP_503_AFTER_BOUNDED_CLIENT_RETRY_POLICY",
        "error_type":receipt.get("error_type"),"error":error,"preflight_count":None,
        "transaction_download_attempted":False,"download_rows_matched":0,"matched_rows":0,
        "same_route_retry_allowed":False,
        "next_gate":"Do not repeat the identical transaction-download route. Retry only after a materially different, documented route or transport contract is preregistered and independently tested.",
        "interpretation_scope":{
            "source_failure_classification_only":True,"historical_parent_lineage_proven":False,
            "recipient_to_issuer_mapping_frozen":False,"historical_first_public_observation_proven":False,
            "gate_positive":False,"scientific_evidence":False,"performance_authorization":False,
            "holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False,
        },
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
    }
    core["analysis_fingerprint"]=sha(json.dumps(core,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8"))
    return core

def run(source:Path, request_path:Path, output:Path)->dict[str,Any]:
    request=read_request(request_path)
    receipt=json.loads(find_receipt(source).read_text(encoding="utf-8"))
    core=build_audit(receipt,request)
    result={**core,"generated_at_utc":datetime.now(timezone.utc).isoformat()}
    result["receipt_fingerprint"]=fingerprint(result)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"analysis_fingerprint":result["analysis_fingerprint"],"failure_stage":result["failure_stage"],"same_route_retry_allowed":result["same_route_retry_allowed"]},sort_keys=True))
    return result

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-artifact",type=Path,required=True)
    ap.add_argument("--request",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    run(args.source_artifact,args.request,args.output)
    return 0
if __name__=="__main__": raise SystemExit(main())
