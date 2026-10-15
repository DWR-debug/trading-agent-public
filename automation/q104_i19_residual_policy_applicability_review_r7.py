"""Bounded Q104:I19 review of the exact 19 remaining frozen filing-date mismatches.

This workpack validates immutable receipts, downloads only three already-pinned quarterly
Form 13F dataset ZIPs, then queries the three EDGAR header routes for 19 fixed accessions.
No daily Feed archives, primary filing documents, census restart, receipt rewrite,
production precedence application, PIT/performance authorization or live execution.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from automation import q104_i19_residual_source_lineage_diagnostic as lineage

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN_ID = 38168441086
SOURCE_PAGE_SHA256 = "b2c4083c3615ce6646764d8e80dc18c2f5484a25c417281be580bdc650817b46"
RECOVERY_RUN_ID = 38250105408
RECOVERY_ARTIFACT_ID = 11747003791
RECOVERY_ARTIFACT_NAME = "q104-i19-targeted-acceptance-repair-38168441086-38250105408-2"
RECOVERY_SHA256 = "5c0a4b41d11efbe3e92af72dc8a4e8b928219f44b7839ce1ad8008eb19265131"
ORIGINAL = {
 "2013-2016":"dbe0651154dd4e34ee1aac729f48cf1536c99e28d17666e70178898ab198a27f",
 "2017-2018":"8175c92b1a899a8993af069d68f9de1553364b84c8c7029c1a1933c61b0a8db8",
 "2019-2020":"cc8b8f678373b131c7382ce15e0e543322d96eb3d1c16593cd52b54d796333e8",
 "2021-2022":"6c8445ada7f1a28cfa44651fad3a113fbad98ccac4fa10a671d038be8c2f5ff1",
 "2023":"1dfade4fc289ef5493989bf487377fe1447c1b22743584767447da5b8a310502",
 "2024-2025-09":"2500f2ee3f07258a9525cd6e7018fd67f380cf0244028c5948866d55c835794e",
}
REPAIRED = {
 "2013-2016":"cb1f2bf7705e4b9cc0500279650fd2d88ffd1180320137e1de8157a6cb129663",
 "2017-2018":"ddc775ee4adb8e7df41a1b7f445b93b95ffc2f28d10d6a71d7be53807d211b38",
 "2019-2020":"220965baee11bb47ed5f00aa1c468285f49fc0199a9d2e0b9870e01433c3f8ff",
 "2021-2022":"0fd72956098c45d68d042ba27150b7925d83f3084e47510549b7a34fc0c8b0f8",
 "2023":"56de6a800fdc9cb4f2108616b19dce6fce405ad88456bdbaf791b5d1edbb4ce4",
 "2024-2025-09":"03b68f86c71f08ff8b1f8318cb54eb254f723b1ee67255a39d7591c2eab3baca",
}
HELPER_BLOBS = {
 "automation/q104_i19_residual_source_lineage_diagnostic.py":"00925a23d92b5d7e900519e59075cd91646aad34",
 "automation/q104_i19_13f_historical_identity_census.py":"366b8bb3b4fdb7fb8a9cefbc217c49e120a3b07b",
 "automation/q104_i19_13f_historical_identity_census_merge.py":"6f44abfc441ad9cf2c45342a6489360615bb74b4",
}
X64_RUN=38557631541
X64_ARTIFACT=11890995910
X64_NAME="q104-cross-vintage-38557631541-1"
X64_FP="95644cd88172dad43cb311ad5b217b4f082185fd3280f7cd5735089eb82ba8cd"
ARM_RUN=38557631541
ARM_ARTIFACT=11891525016
ARM_NAME="q104-cross-vintage-ubuntu-arm-38557631541-1"
ARM_FP="1b9236ed4848b51016426e6a9ad6e1623ea318c9455f66f70736286e602cc8cf"
ANALYSIS_FP="9bff9c1b1b0da2f1415c7aabaa66a5ce97b14abd89015f9d47d61a287189e12b"
PRIOR_HEADER_FP="17fa46e3f49b4bb296122a1f6e80b7fbe7e3c134868803b2ddb910f898521412"
R1_FP="c0881b295d37fa34925103b30acbb893a78bbbe230af6e637576dfda4fac86f7"
R2_FP="d85ad092296b38f29fa25147537f52804f9a32d9969051c7f9e9cadff283fe04"
R3_FP="f4c309fe9f5389fdd726fbdb9aa969a46e376d1bd212c3654cc7ec1a6682015a"
ADDITIONAL = {
 "r4":{"run":38574180245,"artifact":11899236364,"name":"q104-i19-residual-lineage-r4-38574180245-1","fp":"8be8fd68de0324a331d2b587a540b605ac5c6e9a71ec203fa9d2fc089450fb3c","type":"q104_i19_residual_source_lineage_diagnostic_r4","shard":"2017-2018"},
 "r5":{"run":38582684174,"artifact":11902804060,"name":"q104-i19-residual-lineage-r5-38582684174-1","fp":"3d9bc88c1f43e4efac88e4528d5ac2c4b6a017beccdbe2e0e821ff150b7cd8a5","type":"q104_i19_residual_source_lineage_diagnostic_r5","shard":"2013-2016"},
 "r6":{"run":38588100012,"artifact":11905763813,"name":"q104-i19-residual-lineage-r6-38588100012-1","fp":"5571f2a8c496d32583b4b7a6bd5d6fee71533e889a5e75b434d1d84031c59522","type":"q104_i19_residual_source_lineage_diagnostic_r6","shard":"2013-2016"},
}
ARCHIVES = {
 "2013q3_form13f.zip":{"url":"https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2013q3_form13f.zip","sha":"aa20c79d552722cb7bae8cefe3e63cd61a0929a4d5234c0b5d9ce1c75309a616","bytes":36457022,"shard":"2013-2016","accessions":("0000950123-13-006949","0000950123-13-006978","0000950123-13-006995","0000950123-13-007038")},
 "2015q1_form13f.zip":{"url":"https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2015q1_form13f.zip","sha":"96ab4cb60063beb98317ce3e2558b3539546e54485fdb1c68adcd33b5634a6ee","bytes":42434965,"shard":"2013-2016","accessions":("0000950123-15-003218","0000950123-15-003231","0000950123-15-003279","0000950123-15-003335","0000950123-15-003381","0000950123-15-003415","0000950123-15-003443")},
 "2020q3_form13f.zip":{"url":"https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2020q3_form13f.zip","sha":"2bcc0bebb7f9eb66b757e44583c0b51069941b9f87a3b4b107a24abe2b7cd7f3","bytes":49051852,"shard":"2019-2020","accessions":("0000860828-20-000006","0001067532-20-000006","0001104659-20-092190","0001221362-20-000009","0001352776-20-000011","0001541625-20-000008","0001654954-20-008660","0001731169-20-000005")},
}
R7_EXPECTED_INDEX_404_ACCESSIONS = frozenset(ARCHIVES["2013q3_form13f.zip"]["accessions"])
R7_SOURCE_CAPTURE_RUN_ID = 38762761429
R7_SOURCE_CAPTURE_HEAD_SHA = "9caaa609f8793180c6518f52df1f595450d9ff0b"
R7_SOURCE_CAPTURE_RECEIPT_FP = "15828d97f29fe3a2cf9c15a26aa2f145aa96a3b6785693fea556c1fbe4c0d31a"
R7_SOURCE_CAPTURE_SEQUENCE = "2026-10-15T15:42:00Z"
TOTAL_ARCHIVE_BYTES=sum(x["bytes"] for x in ARCHIVES.values())
MAX_ARCHIVE_BYTES=50_000_000
MAX_TOTAL_BYTES=150_000_000
MAX_HEADER_EACH=262_144
MAX_HEADER_TOTAL=8_000_000
DATE_FAILURES={"FILING_DATE_MISMATCH","HEADER_VALIDATION:FILING_DATE_MISMATCH"}
FAILURE_COUNTS={"FILING_DATE_MISMATCH":31,"HEADER_VALIDATION:FILING_DATE_MISMATCH":5,"FILER_CIK_MISMATCH":6,"FORM_MISMATCH":1,"SEC_COMPLETE_SUBMISSION_HTTP_404":10}
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False,"paid_api_budget_usd":0,"performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False}

FROZEN={
 "RUN_Q104_I19_RESIDUAL_POLICY_APPLICABILITY_R7":"true",
 "SOURCE_OF_TRUTH":"DWR-debug/trading-agent-public",
 "REASON":"COMPLETE_HEADER_EVIDENCE_FOR_THE_19_REMAINING_FROZEN_DATE_MISMATCH_ACCESSIONS_ONLY",
 "SOURCE_RUN_ID":str(SOURCE_RUN_ID),"SOURCE_PAGE_SHA256":SOURCE_PAGE_SHA256,
 "SOURCE_ORIGINAL_SHARD_RECEIPT_FINGERPRINTS":"|".join(f"{k}:{v}" for k,v in ORIGINAL.items()),
 "SOURCE_REPAIRED_SHARD_RECEIPT_FINGERPRINTS":"|".join(f"{k}:{v}" for k,v in REPAIRED.items()),
 "RECOVERY_RUN_ID":str(RECOVERY_RUN_ID),"RECOVERY_ARTIFACT_ID":str(RECOVERY_ARTIFACT_ID),"RECOVERY_ARTIFACT_NAME":RECOVERY_ARTIFACT_NAME,
 "RECOVERY_RECEIPT_JSON_SHA256":RECOVERY_SHA256,"RECOVERY_STATUS":"RECOVERY_INCOMPLETE","RECOVERY_UNRESOLVED_COUNT":"53","RECOVERY_DATE_MISMATCH_COUNT":"36",
 "CROSS_VINTAGE_RUN_ID":str(X64_RUN),"CROSS_VINTAGE_X64_ARTIFACT_ID":str(X64_ARTIFACT),"CROSS_VINTAGE_X64_ARTIFACT_NAME":X64_NAME,"CROSS_VINTAGE_X64_RECEIPT_FINGERPRINT":X64_FP,
 "CROSS_VINTAGE_ARM64_ARTIFACT_ID":str(ARM_ARTIFACT),"CROSS_VINTAGE_ARM64_ARTIFACT_NAME":ARM_NAME,"CROSS_VINTAGE_ARM64_RECEIPT_FINGERPRINT":ARM_FP,"CROSS_VINTAGE_ANALYSIS_FINGERPRINT":ANALYSIS_FP,
 "R4_RUN_ID":str(ADDITIONAL["r4"]["run"]),"R4_ARTIFACT_ID":str(ADDITIONAL["r4"]["artifact"]),"R4_ARTIFACT_NAME":ADDITIONAL["r4"]["name"],"R4_RECEIPT_FINGERPRINT":ADDITIONAL["r4"]["fp"],
 "R5_RUN_ID":str(ADDITIONAL["r5"]["run"]),"R5_ARTIFACT_ID":str(ADDITIONAL["r5"]["artifact"]),"R5_ARTIFACT_NAME":ADDITIONAL["r5"]["name"],"R5_RECEIPT_FINGERPRINT":ADDITIONAL["r5"]["fp"],
 "R6_RUN_ID":str(ADDITIONAL["r6"]["run"]),"R6_ARTIFACT_ID":str(ADDITIONAL["r6"]["artifact"]),"R6_ARTIFACT_NAME":ADDITIONAL["r6"]["name"],"R6_RECEIPT_FINGERPRINT":ADDITIONAL["r6"]["fp"],
 "DATE_MISMATCH_TARGET_COUNT":"19","HEADER_ROUTE_COUNT":"57","MAX_SOURCE_ARCHIVE_BYTES_EACH":str(MAX_ARCHIVE_BYTES),"MAX_TOTAL_DOWNLOAD_BYTES":str(MAX_TOTAL_BYTES),
 "EXPECTED_SOURCE_ARCHIVE_DOWNLOAD_BYTES":str(TOTAL_ARCHIVE_BYTES),"MAX_HEADER_RESPONSE_BYTES":str(MAX_HEADER_EACH),"MAX_HEADER_RESPONSE_BUDGET_BYTES":str(MAX_HEADER_TOTAL),
 "SOURCE_ARCHIVE_2013Q3_SHA256":ARCHIVES["2013q3_form13f.zip"]["sha"],"SOURCE_ARCHIVE_2013Q3_BYTES":str(ARCHIVES["2013q3_form13f.zip"]["bytes"]),
 "SOURCE_ARCHIVE_2013Q3_ACCESSIONS":"|".join(ARCHIVES["2013q3_form13f.zip"]["accessions"]),
 "SOURCE_ARCHIVE_2015Q1_SHA256":ARCHIVES["2015q1_form13f.zip"]["sha"],"SOURCE_ARCHIVE_2015Q1_BYTES":str(ARCHIVES["2015q1_form13f.zip"]["bytes"]),
 "SOURCE_ARCHIVE_2015Q1_ACCESSIONS":"|".join(ARCHIVES["2015q1_form13f.zip"]["accessions"]),
 "SOURCE_ARCHIVE_2020Q3_SHA256":ARCHIVES["2020q3_form13f.zip"]["sha"],"SOURCE_ARCHIVE_2020Q3_BYTES":str(ARCHIVES["2020q3_form13f.zip"]["bytes"]),
 "SOURCE_ARCHIVE_2020Q3_ACCESSIONS":"|".join(ARCHIVES["2020q3_form13f.zip"]["accessions"]),
 "LINEAGE_HELPER_CODE_BLOB_SHA1":HELPER_BLOBS["automation/q104_i19_residual_source_lineage_diagnostic.py"],
 "CENSUS_HELPER_CODE_BLOB_SHA1":HELPER_BLOBS["automation/q104_i19_13f_historical_identity_census.py"],
 "CENSUS_MERGE_HELPER_CODE_BLOB_SHA1":HELPER_BLOBS["automation/q104_i19_13f_historical_identity_census_merge.py"],
 "CENSUS_RESTART":"false","REPAIR_RECEIPTS":"false","APPLY_FIELD_PRECEDENCE":"false","CHANGE_PRODUCTION_JOIN":"false",
 "NO_NEW_DAILY_FEED_REQUESTS":"true","NO_PRIMARY_DOCUMENT_REQUESTS":"true","NO_SOURCE_RECEIPT_REWRITES":"true","RESEARCH_GATES_REMAIN_CLOSED":"true","PAID_API_BUDGET_USD":"0",
 "PERFORMANCE":"false","HOLDOUT_SELECTION":"false","RANKING":"false","TUNING":"false","PROMOTION":"false","LIVE_EXECUTION":"false",
}
REQUEST_KEYS=set(FROZEN)|{"REQUEST_SEQUENCE"}

class ReviewError(ValueError): pass

class CombinedBudget:
 def __init__(self,total:int,header:int):
  self.maximum=total;self.header_maximum=header;self.used=0;self.header_used=0;self.is_header_phase=False;self.next_request_at=0.0
 def wait(self):
  if self.next_request_at:
   delay=1.0-(time.monotonic()-self.next_request_at)
   if delay>0: time.sleep(delay)
  self.next_request_at=time.monotonic()
 def add(self,count:int):
  if count<0 or self.used+count>self.maximum: raise ReviewError("TOTAL_DOWNLOAD_BUDGET_EXCEEDED")
  if self.is_header_phase and self.header_used+count>self.header_maximum: raise ReviewError("HEADER_DOWNLOAD_BUDGET_EXCEEDED")
  self.used+=count
  if self.is_header_phase: self.header_used+=count

def sha(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()
def blob_sha(raw:bytes)->str: return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def fp(value:dict[str,Any])->str:
 p=dict(value);p.pop("receipt_fingerprint",None)
 return sha(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode())

def read_request(path:Path)->dict[str,str]:
 vals={}
 for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
  if not line or line.strip()!=line or "=" not in line: raise ReviewError(f"REQUEST_INVALID_LINE:{n}")
  k,v=line.split("=",1)
  if not k or not v or k in vals: raise ReviewError(f"REQUEST_INVALID_KEY_VALUE:{n}")
  vals[k]=v
 if set(vals)!=REQUEST_KEYS: raise ReviewError("REQUEST_KEY_SET_MISMATCH")
 for k,v in FROZEN.items():
  if vals[k]!=v: raise ReviewError("REQUEST_VALUE_MISMATCH:"+k)
 if not __import__("re").fullmatch(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ",vals["REQUEST_SEQUENCE"]): raise ReviewError("REQUEST_SEQUENCE_INVALID")
 datetime.fromisoformat(vals["REQUEST_SEQUENCE"].replace("Z","+00:00"))
 return vals

def find(root:Path,suffix:str)->Path:
 if root.is_file(): return root
 hits=sorted(root.rglob(suffix))
 if len(hits)!=1: raise ReviewError(f"INPUT_FILE_COUNT_INVALID:{suffix}:{len(hits)}")
 return hits[0]

def validate_helpers()->dict[str,str]:
 actual={}
 for path,expected in HELPER_BLOBS.items():
  got=blob_sha((ROOT/path).read_bytes());actual[path]=got
  if got!=expected: raise ReviewError("HELPER_CODE_BLOB_CHANGED:"+path+":"+got)
 return actual

def archive_row(receipt:dict[str,Any],url:str,shard:str)->dict[str,Any]:
 if receipt.get("shard")!=shard or receipt.get("source_page_sha256")!=SOURCE_PAGE_SHA256: raise ReviewError("SHARD_SOURCE_IDENTITY_MISMATCH:"+shard)
 hits=[x for x in receipt.get("archives",[]) if (x.get("archive") or {}).get("url")==url]
 if len(hits)!=1: raise ReviewError("SHARD_ARCHIVE_ROW_COUNT_MISMATCH:"+url)
 return hits[0]

def validate_recovery(root:Path)->tuple[dict[str,Any],dict[str,dict],dict[str,dict],bytes]:
 rp=find(root,"targeted_recovery_receipt.json");raw=rp.read_bytes()
 if sha(raw)!=RECOVERY_SHA256: raise ReviewError("RECOVERY_RECEIPT_RAW_SHA256_MISMATCH")
 rec=json.loads(raw)
 if rec.get("record_type")!="q104_i19_targeted_acceptance_header_recovery" or rec.get("status")!="RECOVERY_INCOMPLETE" or str(rec.get("source_run_id"))!=str(SOURCE_RUN_ID) or rec.get("source_page_sha256")!=SOURCE_PAGE_SHA256: raise ReviewError("RECOVERY_RECEIPT_IDENTITY_MISMATCH")
 unresolved=rec.get("unresolved_accession_set");failed=rec.get("failed_accession_set");attempts=rec.get("attempts")
 if not isinstance(unresolved,list) or not isinstance(failed,list) or not isinstance(attempts,list) or len(unresolved)!=53 or len(set(unresolved))!=53 or set(unresolved)!=set(failed) or len(attempts)!=53: raise ReviewError("RECOVERY_SET_COUNTS_INVALID")
 from collections import Counter
 if dict(Counter(str(x.get("original_failure") or "") for x in attempts))!=FAILURE_COUNTS: raise ReviewError("RECOVERY_FAILURE_COUNTS_INVALID")
 if rec.get("repaired_accession_set")!=[] or rec.get("summary",{}).get("repaired")!=0: raise ReviewError("RECOVERY_MUTATION_STATE_INVALID")
 if rec.get("input_shard_receipt_fingerprints")!=REPAIRED or rec.get("repaired_shard_receipt_fingerprints")!=REPAIRED or rec.get("original_shard_receipt_fingerprints")!=ORIGINAL: raise ReviewError("RECOVERY_SHARD_MAP_INVALID")
 data=rp.parent; originals={};repaired={};bundle={"recovery.json":raw}
 for kind,target,pins in (("input",originals,ORIGINAL),("repaired",repaired,REPAIRED)):
  for shard,wanted in pins.items():
   path=data/kind/shard/"shard_receipt.json"
   b=path.read_bytes();v=json.loads(b)
   if v.get("receipt_fingerprint")!=wanted or fp(v)!=wanted or v.get("shard")!=shard or v.get("source_page_sha256")!=SOURCE_PAGE_SHA256: raise ReviewError("SHARD_RECEIPT_PIN_INVALID:"+kind+":"+shard)
   target[shard]=v;bundle[f"{kind}/{shard}.json"]=b
 page=(data/"source_snapshot"/"source_page.html").read_bytes()
 if sha(page)!=SOURCE_PAGE_SHA256: raise ReviewError("SOURCE_PAGE_PIN_INVALID")
 bundle["source_page.html"]=page
 return rec,originals,repaired,bundle

def validate_cross(root:Path,which:str)->dict[str,Any]:
 v=json.loads(find(root,"receipt.json").read_text())
 wanted=X64_FP if which=="x64" else ARM_FP
 if v.get("record_type")!="q104_i19_cross_vintage_date_change_aggregate" or v.get("status")!="FIELD_PRECEDENCE_EXTENDED_DIAGNOSTIC_ONLY_NOT_APPLIED" or v.get("receipt_fingerprint")!=wanted or fp(v)!=wanted or v.get("analysis_fingerprint")!=ANALYSIS_FP: raise ReviewError("CROSS_VINTAGE_PIN_INVALID:"+which)
 if (v.get("source_prior_receipt_fingerprint"),v.get("source_r1_receipt_fingerprint"),v.get("source_r2_receipt_fingerprint"),v.get("source_r3_lineage_receipt_fingerprint"))!=(PRIOR_HEADER_FP,R1_FP,R2_FP,R3_FP): raise ReviewError("CROSS_VINTAGE_UPSTREAM_PINS_INVALID:"+which)
 expected={"sample_count":14,"bulk_date_differs_from_header":14,"header_filing_date_routes_agree":14,"acceptance_routes_agree":14,"date_change_observed":14,"date_change_routes_agree_where_observed":14,"date_change_equals_header_filing_date":2,"date_change_differs_from_header_filing_date":12}
 if v.get("counts")!=expected or len(v.get("samples",[]))!=14: raise ReviewError("CROSS_VINTAGE_COUNTS_INVALID:"+which)
 if any(x is not False for x in (v.get("interpretation_scope",{}).get("field_precedence_applied"),v.get("interpretation_scope",{}).get("source_receipts_modified"),v.get("interpretation_scope",{}).get("production_join_changed"),v.get("interpretation_scope",{}).get("acceptance_time_gate_cleared"),v.get("interpretation_scope",{}).get("historical_archive_gate_cleared"),v.get("interpretation_scope",{}).get("performance_authorization"))): raise ReviewError("CROSS_VINTAGE_SCOPE_INVALID:"+which)
 for s in v["samples"]:
  if not all(s.get(k) is True for k in ("identity_fields_consistent","bulk_date_differs_from_header","header_filing_date_routes_agree","acceptance_routes_agree")): raise ReviewError("CROSS_VINTAGE_SAMPLE_INVALID:"+str(s.get("accession")))
 return v

def validate_extra(root:Path,key:str,unresolved:set[str],attempts:dict[str,dict])->dict[str,Any]:
 pin=ADDITIONAL[key];v=json.loads(find(root,"receipt.json").read_text())
 if v.get("record_type")!=pin["type"] or v.get("status")!="LINEAGE_DIAGNOSTIC_COMPLETE" or v.get("receipt_fingerprint")!=pin["fp"] or fp(v)!=pin["fp"] or str(v.get("source_run_id"))!=str(SOURCE_RUN_ID) or v.get("source_page_sha256")!=SOURCE_PAGE_SHA256: raise ReviewError("ADDITIONAL_RECEIPT_PIN_INVALID:"+key)
 if v.get("source_shard_receipt_fingerprints",{}).get(pin["shard"])!=ORIGINAL[pin["shard"]]: raise ReviewError("ADDITIONAL_SHARD_PIN_INVALID:"+key)
 samples=v.get("samples",[])
 if len(samples)!=1: raise ReviewError("ADDITIONAL_SAMPLE_COUNT_INVALID:"+key)
 s=samples[0];a=s.get("accession")
 if a not in unresolved or a not in attempts or attempts[a].get("original_failure") not in DATE_FAILURES or s.get("frozen_failure")!="FILING_DATE_MISMATCH" or s.get("archive_sha256_match") is not True: raise ReviewError("ADDITIONAL_SAMPLE_NOT_FIXED_DATE_FAILURE:"+key)
 usable=[p for p in s.get("probes",[]) if isinstance(p.get("observed_identity"),dict)]
 dates={p["observed_identity"].get("filing_date") for p in usable};accepts={p["observed_identity"].get("acceptance_datetime") for p in usable}
 if len(usable) not in (2,3) or len(dates)!=1 or None in dates or len(accepts)!=1 or None in accepts or next(iter(dates))==s.get("source_row",{}).get("filing_date_iso"): raise ReviewError("ADDITIONAL_OBSERVATION_INVALID:"+key)
 return v

def load_inputs(request:dict[str,str],recovery_root:Path,x64_root:Path,arm64_root:Path,extra_roots:dict[str,Path]):
 helpers=validate_helpers()
 rec,originals,repaired,bundle=validate_recovery(recovery_root)
 unresolved=set(rec["unresolved_accession_set"]);attempts={x["accession"]:x for x in rec["attempts"]}
 x64=validate_cross(x64_root,"x64");arm64=validate_cross(arm64_root,"arm64")
 if x64["samples"]!=arm64["samples"]: raise ReviewError("CROSS_ARCH_SAMPLE_DIFFERENCE")
 extras={k:validate_extra(extra_roots[k],k,unresolved,attempts) for k in ("r4","r5","r6")}
 prior={x["accession"] for x in x64["samples"]}|{v["samples"][0]["accession"] for v in extras.values()}
 target={a for q in ARCHIVES.values() for a in q["accessions"]}
 date_set={a for a,v in attempts.items() if v.get("original_failure") in DATE_FAILURES}
 if len(prior)!=17 or not prior.issubset(unresolved) or date_set-prior!=target or len(date_set)!=36 or len(target)!=19: raise ReviewError("FIXED_17_PLUS_19_PARTITION_INVALID")
 for name,raw in (("x64.json",find(x64_root,"receipt.json").read_bytes()),("arm64.json",find(arm64_root,"receipt.json").read_bytes())): bundle[name]=raw
 for k,root in extra_roots.items(): bundle[k+".json"]=find(root,"receipt.json").read_bytes()
 inputs={"request":request,"recovery":rec,"original_shards":originals,"repaired_shards":repaired,"x64":x64,"arm64":arm64,"extras":extras,"attempts":attempts,"unresolved":unresolved,"prior":prior,"target":target,"helper_blobs":helpers}
 return inputs,bundle

def frozen_fingerprints(i:dict[str,Any])->dict[str,Any]:
 return {
  "recovery_run_id":RECOVERY_RUN_ID,"recovery_artifact_id":RECOVERY_ARTIFACT_ID,"recovery_sha256":RECOVERY_SHA256,
  "source_page_sha256":SOURCE_PAGE_SHA256,"original_shards":ORIGINAL,"repaired_shards":REPAIRED,
  "cross_vintage_x64_fp":X64_FP,"cross_vintage_arm64_fp":ARM_FP,"cross_vintage_analysis_fp":ANALYSIS_FP,
  "additional":{k:ADDITIONAL[k]["fp"] for k in ("r4","r5","r6")},"helper_blobs":i["helper_blobs"],
 }


def known_index_header_404_exception(sample:dict[str,Any])->bool:
    """Accept only the four pre-pinned 2013Q3 index-header 404s when both other routes agree."""
    try:
        accession = str(sample.get("accession") or "")
        if accession not in R7_EXPECTED_INDEX_404_ACCESSIONS:
            return False
        if sample.get("source_archive_name") != "2013q3_form13f.zip":
            return False
        source = sample.get("source_row") or {}
        if source.get("accession") != accession:
            return False
        probes = sample.get("probes")
        if not isinstance(probes, list) or len(probes) != 3:
            return False
        by_route = {str(p.get("route") or ""): p for p in probes if isinstance(p, dict)}
        if set(by_route) != {"index_headers", "raw_sgml_header", "complete_submission_header_prefix"}:
            return False
        index = by_route["index_headers"]
        if (
            index.get("http_status") != 404
            or index.get("status") != "HTTP_ERROR"
            or index.get("error") != "HTTP_404"
            or index.get("response_error") != "HTTP_404"
            or int(index.get("response_bytes") or 0) != 0
            or isinstance(index.get("observed_identity"), dict)
            or any(k in index for k in ("_body", "body", "response_body"))
        ):
            return False
        dates = set()
        acceptances = set()
        for route in ("raw_sgml_header", "complete_submission_header_prefix"):
            probe = by_route[route]
            if (
                probe.get("http_status") != 200
                or probe.get("status") not in {"FETCHED", "FETCHED_PREFIX"}
                or not probe.get("response_sha256")
                or int(probe.get("response_bytes") or 0) > MAX_HEADER_EACH
                or any(k in probe for k in ("_body", "body", "response_body"))
            ):
                return False
            observed = probe.get("observed_identity") or {}
            comparison = probe.get("comparison_to_frozen_archive_row") or {}
            if (
                observed.get("accession") != accession
                or observed.get("filer_cik") != source.get("filer_cik")
                or observed.get("form") != source.get("form")
                or not observed.get("filing_date")
                or not observed.get("acceptance_datetime")
                or comparison.get("accession_matches") is not True
                or comparison.get("filer_cik_matches") is not True
                or comparison.get("form_matches") is not True
                or comparison.get("filing_date_matches") is not False
            ):
                return False
            dates.add(observed.get("filing_date"))
            acceptances.add(observed.get("acceptance_datetime"))
        return (
            len(dates) == 1
            and None not in dates
            and next(iter(dates)) != source.get("filing_date_iso")
            and len(acceptances) == 1
            and None not in acceptances
        )
    except (TypeError, ValueError, KeyError):
        return False


def capture_headers(inputs:dict[str,Any])->dict[str,Any]:
 request=inputs["request"];attempts=inputs["attempts"]
 budget=CombinedBudget(MAX_TOTAL_BYTES,MAX_HEADER_TOTAL)
 archive_results={};rows={}
 for name,pin in ARCHIVES.items():
  pr=archive_row(inputs["repaired_shards"][pin["shard"]],pin["url"],pin["shard"])
  orow=archive_row(inputs["original_shards"][pin["shard"]],pin["url"],pin["shard"])
  if any(r.get("archive_sha256")!=pin["sha"] or r.get("archive_bytes")!=pin["bytes"] for r in (pr,orow)): raise ReviewError("ARCHIVE_PIN_NOT_IN_FROZEN_SHARD:"+name)
  for a in pin["accessions"]:
   attempt=attempts.get(a)
   if not attempt or attempt.get("source_archive")!=pin["url"] or attempt.get("original_failure") not in DATE_FAILURES or int(attempt.get("attempts") or 0)!=0 or attempt.get("status")!="NOT_RETRIED_NONTRANSIENT": raise ReviewError("TARGET_REQUEST_STATE_INVALID:"+a)
   if (pr.get("acceptance_failures") or {}).get(a)!=attempt.get("original_failure"): raise ReviewError("TARGET_SHARD_FAILURE_NOT_PINNED:"+a)
  response=lineage.fetch_bounded(pin["url"],budget,max_bytes=MAX_ARCHIVE_BYTES)
  body=response.pop("_body",b"");got=sha(body) if body else None
  ar={"url":pin["url"],"expected_sha256":pin["sha"],"expected_bytes":pin["bytes"],"http":response,"actual_sha256":got,"actual_bytes":len(body),"verified":response.get("status")=="FETCHED" and got==pin["sha"] and len(body)==pin["bytes"]}
  archive_results[name]=ar
  if not ar["verified"]:
   failed={"schema_version":1,"record_type":"q104_i19_residual_policy_applicability_r7_capture","candidate_id":"Q104:I19","status":"Q104_I19_RESIDUAL_R7_CAPTURE_INCOMPLETE","generated_at_utc":datetime.now(timezone.utc).isoformat(),"frozen_request_sequence":request["REQUEST_SEQUENCE"],"frozen_input_receipt_fingerprints":frozen_fingerprints(inputs),"source_archives":archive_results,"samples":[],"source_archive_download_expected_bytes":TOTAL_ARCHIVE_BYTES,"source_archive_download_actual_bytes":sum(x["actual_bytes"] for x in archive_results.values()),"download_budget":{"bytes_consumed":budget.used,"max_total_bytes":MAX_TOTAL_BYTES,"header_bytes_consumed":0,"max_header_response_bytes":MAX_HEADER_TOTAL,"max_header_response_bytes_each":MAX_HEADER_EACH},"source_bodies_persisted":False,"complete_submission_text_bodies_persisted":False,"primary_document_requests":0,"daily_feed_requests":0,"archive_census_restarted":False,"source_receipts_modified":False,"frozen_expected_dates_modified":False,"field_precedence_applied":False,"production_join_changed":False,"acceptance_time_gate_cleared":False,"historical_archive_gate_cleared":False,"performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False,"safety":SAFETY,"errors":["ARCHIVE_HASH_OR_BYTE_LENGTH_MISMATCH:"+name]}
   failed["receipt_fingerprint"]=fp(failed);return failed
  # only selected frozen rows are read from the verified ZIP; the body stays in memory.
  source_rows=lineage.read_source_rows(body,set(pin["accessions"]))
  if set(source_rows)!=set(pin["accessions"]): raise ReviewError("SOURCE_ROW_SET_MISMATCH:"+name)
  ar["requested_accessions"]=sorted(pin["accessions"])
  ar["source_rows_found"]=sorted(source_rows)
  ar["source_rows_missing"]=[]
  rows.update(source_rows)
 budget.is_header_phase=True
 samples=[]
 for name,pin in ARCHIVES.items():
  for acc in pin["accessions"]:
   source=rows[acc];attempt=attempts[acc];normalized=acc.replace("-","")
   base=f"https://www.sec.gov/Archives/edgar/data/{int(source['filer_cik'])}/{normalized}"
   routes=(("index_headers",f"{base}/{acc}-index-headers.html",None),("raw_sgml_header",f"{base}/{acc}.hdr.sgml",None),("complete_submission_header_prefix",f"{base}/{acc}.txt",b"</SEC-HEADER>"))
   probes=[]
   for route,url,marker in routes:
    result=lineage.fetch_bounded(url,budget,max_bytes=MAX_HEADER_EACH,prefix_marker=marker)
    body=result.pop("_body",b"")
    probe={**result,"route":route,"requested_url":url,"observed_identity":None,"comparison_to_frozen_archive_row":None}
    if result.get("http_status")==200 and result.get("status") in {"FETCHED","FETCHED_PREFIX"} and body and (marker is None or result.get("prefix_marker_found") is True):
     obs=lineage.parse_header_observation(body,route)
     probe["observed_identity"]=obs
     probe["comparison_to_frozen_archive_row"]=lineage.compare_observed_to_archive(source,obs)
    else:
     probe["response_error"]=result.get("error") or result.get("status") or "HEADER_NOT_USABLE"
    probes.append(probe)
   usable=[p for p in probes if isinstance(p.get("observed_identity"),dict)]
   dates={p["observed_identity"].get("filing_date") for p in usable}
   accepted={p["observed_identity"].get("acceptance_datetime") for p in usable}
   changes={p["observed_identity"].get("date_of_filing_date_change") for p in usable if p["observed_identity"].get("date_of_filing_date_change")}
   sample_probe={"accession":acc,"source_archive_name":name,"source_row":source,"probes":probes}
   route_404_exception=known_index_header_404_exception(sample_probe)
   identity=(len(usable)==3 or route_404_exception) and all((p.get("comparison_to_frozen_archive_row") or {}).get(k) is True for p in usable for k in ("accession_matches","filer_cik_matches","form_matches")) and all((p.get("comparison_to_frozen_archive_row") or {}).get("filing_date_matches") is False for p in usable)
   summary={"usable_route_count":len(usable),"all_three_routes_usable":len(usable)==3,"identity_fields_match_frozen_source_row":identity,"known_index_header_404_exception":route_404_exception,"header_filing_dates_agree":len(dates)==1 and None not in dates,"acceptance_datetimes_agree":len(accepted)==1 and None not in accepted,"bulk_filing_date_differs_from_header":len(dates)==1 and None not in dates and next(iter(dates))!=source.get("filing_date_iso"),"date_change_observed_on_any_route":bool(changes),"date_change_values_agree_where_observed":len(changes)<=1,"observed_edgar_header_filing_date":next(iter(dates)) if len(dates)==1 else None,"observed_acceptance_datetime":next(iter(accepted)) if len(accepted)==1 else None,"observed_date_of_filing_date_change":next(iter(changes)) if len(changes)==1 else None}
   status="OBSERVED_TWO_ROUTE_INDEX_404" if route_404_exception and identity and summary["header_filing_dates_agree"] and summary["acceptance_datetimes_agree"] and summary["bulk_filing_date_differs_from_header"] and summary["date_change_values_agree_where_observed"] else ("OBSERVED" if summary["all_three_routes_usable"] and identity and summary["header_filing_dates_agree"] and summary["acceptance_datetimes_agree"] and summary["bulk_filing_date_differs_from_header"] and summary["date_change_values_agree_where_observed"] else "OBSERVATION_INCOMPLETE_OR_IDENTITY_CONFLICT")
   samples.append({"accession":acc,"source_archive_name":name,"source_archive_url":pin["url"],"frozen_failure":attempt["original_failure"],"source_row":source,"source_archive_sha256_match":True,"probes":probes,"summary":summary,"status":status})
 complete=sum(x["status"] in {"OBSERVED","OBSERVED_TWO_ROUTE_INDEX_404"} for x in samples)
 receipt={"schema_version":1,"record_type":"q104_i19_residual_policy_applicability_r7_capture","candidate_id":"Q104:I19","status":"Q104_I19_RESIDUAL_R7_CAPTURE_COMPLETE" if len(samples)==19 and complete==19 else "Q104_I19_RESIDUAL_R7_CAPTURE_INCOMPLETE","generated_at_utc":datetime.now(timezone.utc).isoformat(),"frozen_request_sequence":request["REQUEST_SEQUENCE"],"frozen_input_receipt_fingerprints":frozen_fingerprints(inputs),"helper_code_blobs":inputs["helper_blobs"],"source_archives":archive_results,"sample_count":len(samples),"sample_count_complete":complete,"source_row_count":len(rows),"header_route_request_count":sum(len(x["probes"]) for x in samples),"header_route_usable_count":sum(x["summary"]["usable_route_count"] for x in samples),"bulk_date_differs_count":sum(x["summary"]["bulk_filing_date_differs_from_header"] is True for x in samples),"identity_validated_count":sum(x["summary"]["identity_fields_match_frozen_source_row"] is True for x in samples),"acceptance_routes_agree_count":sum(x["summary"]["acceptance_datetimes_agree"] is True for x in samples),"source_archive_download_expected_bytes":TOTAL_ARCHIVE_BYTES,"source_archive_download_actual_bytes":sum(x["actual_bytes"] for x in archive_results.values()),"download_budget":{"bytes_consumed":budget.used,"max_total_bytes":MAX_TOTAL_BYTES,"header_bytes_consumed":budget.header_used,"max_header_response_bytes":MAX_HEADER_TOTAL,"max_header_response_bytes_each":MAX_HEADER_EACH},"samples":samples,"source_bodies_persisted":False,"complete_submission_text_bodies_persisted":False,"primary_document_requests":0,"daily_feed_requests":0,"archive_census_restarted":False,"source_receipts_modified":False,"frozen_expected_dates_modified":False,"field_precedence_applied":False,"production_join_changed":False,"acceptance_time_gate_cleared":False,"historical_archive_gate_cleared":False,"performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False,"safety":SAFETY,"errors":[]}
 receipt["receipt_fingerprint"]=fp(receipt);return receipt

def lineage_case(sample:dict[str,Any],attempt:dict[str,Any],source:str)->dict[str,Any]:
 usable=[p for p in sample.get("probes",[]) if isinstance(p.get("observed_identity"),dict)]
 dates={p["observed_identity"].get("filing_date") for p in usable};accepted={p["observed_identity"].get("acceptance_datetime") for p in usable}
 changes={p["observed_identity"].get("date_of_filing_date_change") for p in usable if p["observed_identity"].get("date_of_filing_date_change")}
 return {"accession":sample["accession"],"source_evidence":source,"original_recovery_failure":attempt["original_failure"],"bulk_filing_date":(sample.get("source_row") or {}).get("filing_date_iso") if sample.get("source_row") else sample.get("bulk_filing_date"),"edgar_header_filing_date":next(iter(dates)) if len(dates)==1 else (sample.get("edgar_header_filing_dates") or [None])[0],"acceptance_datetime":next(iter(accepted)) if len(accepted)==1 else (sample.get("acceptance_datetimes") or [None])[0],"date_of_filing_date_change":next(iter(changes)) if len(changes)==1 else (sample.get("date_change_values") or [None])[0],"identity_fields_consistent":sample.get("identity_fields_consistent") is True if "identity_fields_consistent" in sample else bool(usable) and all((p.get("comparison_to_frozen_archive_row") or {}).get(k) is True for p in usable for k in ("accession_matches","filer_cik_matches","form_matches")),"header_filing_date_routes_agree":sample.get("header_filing_date_routes_agree") is True if "header_filing_date_routes_agree" in sample else len(dates)==1 and None not in dates,"acceptance_routes_agree":sample.get("acceptance_routes_agree") is True if "acceptance_routes_agree" in sample else len(accepted)==1 and None not in accepted,"successful_header_route_count":sample.get("edgar_header_filing_date_route_count",3) if "edgar_header_filing_date_route_count" in sample else len(usable),"date_change_observed":sample.get("date_change_observed") is True if "date_change_observed" in sample else bool(changes),"date_change_routes_agree_where_observed":sample.get("date_change_routes_agree_where_observed") is True if "date_change_routes_agree_where_observed" in sample else len(changes)<=1,"source_archive_pin_status":"FROZEN_ARCHIVE_BYTE_HASH_PINNED","source_archive_name":sample.get("archive_name")}

def validate_capture_payload(inputs:dict[str,Any],capture:dict[str,Any])->None:
 if not isinstance(capture,dict) or capture.get("record_type")!="q104_i19_residual_policy_applicability_r7_capture": raise ReviewError("CAPTURE_RECEIPT_TYPE_INVALID")
 capture_status=capture.get("status")
 if capture.get("receipt_fingerprint")!=fp(capture) or capture_status not in {"Q104_I19_RESIDUAL_R7_CAPTURE_COMPLETE","Q104_I19_RESIDUAL_R7_CAPTURE_INCOMPLETE"}: raise ReviewError("CAPTURE_RECEIPT_FINGERPRINT_OR_STATUS_INVALID")
 if capture.get("frozen_request_sequence")!=inputs["request"].get("REQUEST_SEQUENCE") or capture.get("frozen_input_receipt_fingerprints")!=frozen_fingerprints(inputs) or capture.get("helper_code_blobs")!=inputs["helper_blobs"]: raise ReviewError("CAPTURE_UPSTREAM_PINS_INVALID")
 for key in ("source_bodies_persisted","complete_submission_text_bodies_persisted"):
  if capture.get(key) is not False: raise ReviewError("CAPTURE_BODY_PERSISTENCE_VIOLATION:"+key)
 for key in ("primary_document_requests","daily_feed_requests"):
  if capture.get(key)!=0: raise ReviewError("CAPTURE_PROHIBITED_REQUESTS:"+key)
 for key in ("archive_census_restarted","source_receipts_modified","frozen_expected_dates_modified","field_precedence_applied","production_join_changed","acceptance_time_gate_cleared","historical_archive_gate_cleared","performance_authorization","holdout_selection","ranking","tuning","promotion","live_execution"):
  if capture.get(key) is not False: raise ReviewError("CAPTURE_SCOPE_VIOLATION:"+key)
 if capture.get("safety")!=SAFETY: raise ReviewError("CAPTURE_SAFETY_MISMATCH")
 if capture.get("errors")!=[]: raise ReviewError("CAPTURE_RECORDED_ERRORS_PRESENT")
 archive_rows=capture.get("source_archives")
 if not isinstance(archive_rows,dict) or set(archive_rows)!=set(ARCHIVES): raise ReviewError("CAPTURE_ARCHIVE_SET_INVALID")
 for name,pin in ARCHIVES.items():
  row=archive_rows[name]
  if any((row.get("url")!=pin["url"],row.get("expected_sha256")!=pin["sha"],row.get("expected_bytes")!=pin["bytes"],row.get("actual_sha256")!=pin["sha"],row.get("actual_bytes")!=pin["bytes"],row.get("verified") is not True,(row.get("http") or {}).get("status")!="FETCHED",(row.get("http") or {}).get("http_status")!=200)):
   raise ReviewError("CAPTURE_ARCHIVE_HASH_OR_LENGTH_INVALID:"+name)
  if set(row.get("requested_accessions") or [])!=set(pin["accessions"]) or set(row.get("source_rows_found") or [])!=set(pin["accessions"]) or row.get("source_rows_missing")!=[]: raise ReviewError("CAPTURE_ARCHIVE_ACCESSION_SET_INVALID:"+name)
 samples=capture.get("samples");targets={a for pin in ARCHIVES.values() for a in pin["accessions"]}
 if not isinstance(samples,list) or len(samples)!=19 or {x.get("accession") for x in samples}!=targets: raise ReviewError("CAPTURE_SAMPLE_SET_INVALID")
 usable_total=0
 complete_count=0
 observed_exception_accessions=set()
 actual_identity_count=0
 acceptance_agree_count=0
 for s in samples:
  acc=s.get("accession");name=s.get("source_archive_name")
  if name not in ARCHIVES or acc not in ARCHIVES[name]["accessions"] or s.get("source_archive_sha256_match") is not True: raise ReviewError("CAPTURE_SAMPLE_NOT_VALIDATED:"+str(acc))
  source=s.get("source_row") or {};probes=s.get("probes")
  if source.get("accession")!=acc or not isinstance(probes,list) or len(probes)!=3 or {p.get("route") for p in probes}!={"index_headers","raw_sgml_header","complete_submission_header_prefix"}: raise ReviewError("CAPTURE_SAMPLE_SOURCE_OR_ROUTE_INVALID:"+str(acc))
  route_exception=known_index_header_404_exception(s)
  if route_exception:
   observed_exception_accessions.add(acc)
   expected_status="OBSERVED_TWO_ROUTE_INDEX_404" if capture_status=="Q104_I19_RESIDUAL_R7_CAPTURE_COMPLETE" else "OBSERVATION_INCOMPLETE_OR_IDENTITY_CONFLICT"
   if s.get("status")!=expected_status: raise ReviewError("CAPTURE_ROUTE_EXCEPTION_STATUS_INVALID:"+str(acc))
  elif s.get("status")!="OBSERVED":
   raise ReviewError("CAPTURE_SAMPLE_NOT_VALIDATED:"+str(acc))
  dates=set();accepts=set();changes=set();usable_for_sample=0
  identity_ok=True
  for p in probes:
   if any(k in p for k in ("_body","body","response_body")): raise ReviewError("CAPTURE_ROUTE_BODY_PRESENT:"+str(acc))
   if route_exception and p.get("route")=="index_headers":
    if not (p.get("http_status")==404 and p.get("status")=="HTTP_ERROR" and p.get("error")=="HTTP_404" and p.get("response_error")=="HTTP_404" and int(p.get("response_bytes") or 0)==0 and not isinstance(p.get("observed_identity"),dict)):
     raise ReviewError("CAPTURE_ROUTE_404_EXCEPTION_INVALID:"+str(acc))
    continue
   if p.get("http_status")!=200 or p.get("status") not in {"FETCHED","FETCHED_PREFIX"} or not p.get("response_sha256") or int(p.get("response_bytes") or 0)>MAX_HEADER_EACH:
    raise ReviewError("CAPTURE_ROUTE_HTTP_OR_SIZE_INVALID:"+str(acc))
   obs=p.get("observed_identity") or {};cmp=p.get("comparison_to_frozen_archive_row") or {}
   if obs.get("accession")!=acc or obs.get("filer_cik")!=source.get("filer_cik") or obs.get("form")!=source.get("form") or not obs.get("filing_date") or not obs.get("acceptance_datetime") or cmp.get("accession_matches") is not True or cmp.get("filer_cik_matches") is not True or cmp.get("form_matches") is not True or cmp.get("filing_date_matches") is not False:
    raise ReviewError("CAPTURE_ROUTE_IDENTITY_OR_DATE_INVALID:"+str(acc))
   dates.add(obs.get("filing_date"));accepts.add(obs.get("acceptance_datetime"))
   if obs.get("date_of_filing_date_change"): changes.add(obs["date_of_filing_date_change"])
   usable_for_sample+=1;usable_total+=1
  sm=s.get("summary") or {}
  if len(dates)!=1 or None in dates or len(accepts)!=1 or None in accepts or next(iter(dates))==source.get("filing_date_iso"):
   raise ReviewError("CAPTURE_SAMPLE_DATE_OR_ACCEPTANCE_DISAGREEMENT:"+str(acc))
  if not (sm.get("header_filing_dates_agree") is True and sm.get("acceptance_datetimes_agree") is True and sm.get("bulk_filing_date_differs_from_header") is True and sm.get("date_change_values_agree_where_observed") is True and len(changes)<=1 and sm.get("usable_route_count")==usable_for_sample):
   raise ReviewError("CAPTURE_SAMPLE_SUMMARY_INVALID:"+str(acc))
  if route_exception:
   if sm.get("all_three_routes_usable") is not False: raise ReviewError("CAPTURE_EXCEPTION_THREE_ROUTE_FLAG_INVALID:"+str(acc))
   # Historical capture code marked these 4 rows incomplete because it required 3/3
   # HTTP 200 routes. New captures label the same evidence explicitly as a 2-route exception.
   expected_identity_summary = capture_status=="Q104_I19_RESIDUAL_R7_CAPTURE_COMPLETE"
   if sm.get("identity_fields_match_frozen_source_row") is not expected_identity_summary:
    raise ReviewError("CAPTURE_EXCEPTION_IDENTITY_SUMMARY_INVALID:"+str(acc))
   if "known_index_header_404_exception" in sm and sm.get("known_index_header_404_exception") is not True:
    raise ReviewError("CAPTURE_EXCEPTION_POLICY_FLAG_INVALID:"+str(acc))
  else:
   if usable_for_sample!=3 or sm.get("all_three_routes_usable") is not True or sm.get("identity_fields_match_frozen_source_row") is not True:
    raise ReviewError("CAPTURE_FULL_ROUTE_SUMMARY_INVALID:"+str(acc))
  actual_identity_count+=1
  acceptance_agree_count+=1
  if s.get("status") in {"OBSERVED","OBSERVED_TWO_ROUTE_INDEX_404"}: complete_count+=1
 if observed_exception_accessions!=set(R7_EXPECTED_INDEX_404_ACCESSIONS): raise ReviewError("CAPTURE_EXPECTED_2013_INDEX_404_SET_MISMATCH")
 if capture.get("sample_count")!=19 or capture.get("source_row_count")!=19 or capture.get("header_route_request_count")!=57 or usable_total!=53 or capture.get("header_route_usable_count")!=53 or capture.get("bulk_date_differs_count")!=19 or acceptance_agree_count!=19:
  raise ReviewError("CAPTURE_AGGREGATE_COUNTS_INVALID")
 if capture.get("source_archive_download_expected_bytes")!=TOTAL_ARCHIVE_BYTES or capture.get("source_archive_download_actual_bytes")!=TOTAL_ARCHIVE_BYTES: raise ReviewError("CAPTURE_ARCHIVE_TOTAL_BYTES_INVALID")
 budget=capture.get("download_budget") or {}
 if not (budget.get("bytes_consumed",MAX_TOTAL_BYTES+1)<=MAX_TOTAL_BYTES and budget.get("bytes_consumed",0)>=TOTAL_ARCHIVE_BYTES and budget.get("header_bytes_consumed",MAX_HEADER_TOTAL+1)<=MAX_HEADER_TOTAL and budget.get("header_bytes_consumed")==budget.get("bytes_consumed")-TOTAL_ARCHIVE_BYTES and budget.get("max_total_bytes")==MAX_TOTAL_BYTES and budget.get("max_header_response_bytes")==MAX_HEADER_TOTAL and budget.get("max_header_response_bytes_each")==MAX_HEADER_EACH): raise ReviewError("CAPTURE_DOWNLOAD_BUDGET_INVALID")
 if capture_status=="Q104_I19_RESIDUAL_R7_CAPTURE_INCOMPLETE":
  if complete_count!=15 or capture.get("sample_count_complete")!=15 or capture.get("identity_validated_count")!=15:
   raise ReviewError("CAPTURE_LEGACY_INCOMPLETE_COUNTS_INVALID")
  if any(s.get("status")!="OBSERVATION_INCOMPLETE_OR_IDENTITY_CONFLICT" for s in samples if s.get("accession") in R7_EXPECTED_INDEX_404_ACCESSIONS):
   raise ReviewError("CAPTURE_LEGACY_SAMPLE_STATUS_INVALID")
 elif capture_status=="Q104_I19_RESIDUAL_R7_CAPTURE_COMPLETE":
  if complete_count!=19 or capture.get("sample_count_complete")!=19 or capture.get("identity_validated_count")!=19:
   raise ReviewError("CAPTURE_COMPLETE_COUNTS_INVALID")
 else:
  raise ReviewError("CAPTURE_STATUS_INVALID")


def build_analysis(inputs:dict[str,Any],capture:dict[str,Any])->dict[str,Any]:
 validate_capture_payload(inputs,capture)
 attempts=inputs["attempts"]; unresolved=inputs["unresolved"]
 cases=[lineage_case(s,attempts[s["accession"]],"R1_R2_R3_CROSS_VINTAGE_AGGREGATE") for s in inputs["x64"]["samples"]]
 for key in ("r4","r5","r6"): cases.append(lineage_case(inputs["extras"][key]["samples"][0],attempts[inputs["extras"][key]["samples"][0]["accession"]],key.upper()))
 cases += [lineage_case(s,attempts[s["accession"]],"R7_BOUNDED_THREE_ROUTE_CAPTURE") for s in capture["samples"]]
 cases.sort(key=lambda x:x["accession"])
 expected={a for a,v in attempts.items() if v.get("original_failure") in DATE_FAILURES}
 if len(cases)!=36 or len({x["accession"] for x in cases})!=36 or {x["accession"] for x in cases}!=expected: raise ReviewError("EXACT_36_CASE_SET_INVALID")
 for case in cases:
  if not (case["identity_fields_consistent"] and case["header_filing_date_routes_agree"] and case["acceptance_routes_agree"] and case["bulk_filing_date"] and case["edgar_header_filing_date"] and case["bulk_filing_date"]!=case["edgar_header_filing_date"] and case["acceptance_datetime"]): raise ReviewError("CASE_SOURCE_IDENTITY_OR_DATE_INVALID:"+case["accession"])
 observed=[c for c in cases if c["date_change_observed"]]
 changed=sum(c["date_of_filing_date_change"]!=c["edgar_header_filing_date"] for c in observed)
 same=sum(c["date_of_filing_date_change"]==c["edgar_header_filing_date"] for c in observed)
 route_counts={}
 for c in cases: route_counts[str(c["successful_header_route_count"])]=route_counts.get(str(c["successful_header_route_count"]),0)+1
 failcounts=dict(FAILURE_COUNTS)
 return {"schema_version":1,"record_type":"q104_i19_residual_policy_applicability_review","candidate_id":"Q104:I19","status":"Q104_I19_RESIDUAL_POLICY_APPLICABILITY_REVIEW_COMPLETE_PROPOSAL_NOT_APPLIED","frozen_input_pins":frozen_fingerprints(inputs),"failure_class_counts":failcounts,"counts":{"frozen_unresolved_accessions":53,"frozen_date_mismatch_accessions":36,"frozen_identity_conflict_accessions":7,"frozen_cik_mismatches":6,"frozen_form_mismatches":1,"frozen_complete_submission_http_404":10,"date_mismatch_accessions_with_route_evidence":36,"date_mismatch_accessions_not_yet_identity_or_acceptance_verified":0,"identity_conflict_accessions_outside_date_precedence_scope":7,"http_404_accessions_outside_date_precedence_scope":10,"cross_vintage_aggregate_rows":14,"previously_separate_r4_r6_rows":3,"new_r7_rows":19,"unique_source_verified_date_mismatch_rows":36,"bulk_filing_date_differs_from_edgar_header_date":36,"identity_fields_validated":36,"acceptance_datetime_present_and_cross_route_consistent":36,"date_change_observed_rows":len(observed),"date_change_differs_from_edgar_header_date_where_observed":changed,"date_change_equals_edgar_header_date_where_observed":same,"successful_header_route_counts_by_case":route_counts,"r7_source_archive_count":3,"r7_source_archive_download_bytes":capture["source_archive_download_actual_bytes"],"r7_total_download_bytes_including_headers":capture["download_budget"]["bytes_consumed"],"r7_header_route_requests":capture["header_route_request_count"],"r7_usable_header_route_responses":capture["header_route_usable_count"],"r7_expected_2013_index_header_404s":len(R7_EXPECTED_INDEX_404_ACCESSIONS),"r7_two_route_exception_cases":sum(1 for s in capture["samples"] if known_index_header_404_exception(s)),"r7_three_route_cases":sum(1 for s in capture["samples"] if len([p for p in s["probes"] if isinstance(p.get("observed_identity"),dict)])==3}},"date_mismatch_cases":cases,"capture_provenance":{"source_capture_run_id":R7_SOURCE_CAPTURE_RUN_ID,"source_capture_head_sha":R7_SOURCE_CAPTURE_HEAD_SHA,"source_capture_receipt_fingerprint":capture.get("receipt_fingerprint"),"source_capture_status":capture.get("status"),"source_capture_request_sequence":capture.get("frozen_request_sequence"),"source_capture_receipt_modified":False,"offline_source_requests_made":0,"known_index_header_404_accessions":sorted(R7_EXPECTED_INDEX_404_ACCESSIONS),"route_exception_policy":"Only the four frozen 2013Q3 accessions may use the raw SGML header plus complete-submission header prefix when the index-headers route explicitly returns HTTP 404; both available routes must match the frozen accession/CIK/form, agree on filing date and acceptance datetime, and show a filing-date mismatch. No retries are made."},"proposal":{"acceptance_event_clock":"Retain EDGAR ACCEPTANCE-DATETIME as a distinct event clock only after exact accession/CIK/form identity validation and cross-route agreement.","bulk_filing_date":"Preserve the bulk Form 13F FILING_DATE unchanged as provenance; store the consistent EDGAR header/index filed date separately and flag the discrepancy.","date_of_filing_date_change":"Keep as separate post-acceptance metadata; do not substitute it for filing date or acceptance time.","arithmetic_or_imputation":"None. No date shifting, time-zone arithmetic, imputation, or blanket correction.","applicability_boundary":"This review covers only the 36 residual accessions classified as filing-date mismatches. It does not apply a production rule and does not resolve the seven CIK/form identity conflicts or ten complete-submission HTTP 404 cases."},"interpretation_scope":{"date_precedence_review_only":True,"field_precedence_applied":False,"source_receipts_modified":False,"production_join_changed":False,"census_restarted":False,"source_capture_receipt_modified":False,"offline_route_exception_used":True,"acceptance_time_gate_cleared":False,"historical_archive_gate_cleared":False,"scientific_evidence":False,"performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False},"next_gate":"Separately review whether the proposal is admissible for the now-fully-observed date-mismatch subset; keep the seven CIK/form conflicts and ten HTTP 404 records in their separate unresolved branches. Historical PIT/public-observation and all performance gates remain closed.","safety":SAFETY}

def save_inputs(root:Path,inputs:dict[str,Any],raw:dict[str,bytes])->None:
 root.mkdir(parents=True,exist_ok=True)
 for name,body in raw.items():
  path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)

def save_capture(out:Path,inputs:dict[str,Any],raw:dict[str,bytes],capture:dict[str,Any])->dict[str,Any]:
 out.mkdir(parents=True,exist_ok=True);save_inputs(out/"frozen_inputs",inputs,raw)
 (out/"capture_receipt.json").write_text(json.dumps(capture,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 if capture.get("status")!="Q104_I19_RESIDUAL_R7_CAPTURE_COMPLETE": return {"status":capture.get("status")}
 analysis=build_analysis(inputs,capture);analysis_fp=fp(analysis)
 wrapped={"analysis":analysis,"analysis_fingerprint":analysis_fp}
 (out/"analysis.json").write_text(json.dumps(wrapped,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 return wrapped


def resolve_original_shard_prefix(raw_names:set[str])->str:
    """Resolve the original shard prefix emitted by this workpack's historical bundle writer."""
    for prefix in ("original", "input"):
        required = {f"{prefix}/{shard}.json" for shard in ORIGINAL}
        if required.issubset(raw_names):
            return prefix
    raise ReviewError("BUNDLE_ORIGINAL_SHARD_PREFIX_INVALID")


def replay_inputs(root:Path,request:dict[str,str]):
 raw={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob("*") if p.is_file()}
 required={"recovery.json","x64.json","arm64.json","r4.json","r5.json","r6.json","source_page.html"}
 original_prefix=resolve_original_shard_prefix(set(raw))
 required|={f"{kind}/{shard}.json" for kind,pins in ((original_prefix,ORIGINAL),("repaired",REPAIRED)) for shard in pins}
 if not required.issubset(raw): raise ReviewError("BUNDLE_REQUIRED_INPUT_MISSING:"+",".join(sorted(required-set(raw))))
 rec=json.loads(raw["recovery.json"]);x64=json.loads(raw["x64.json"]);arm=json.loads(raw["arm64.json"]);extra={k:json.loads(raw[k+".json"]) for k in ("r4","r5","r6")}
 if sha(raw["recovery.json"])!=RECOVERY_SHA256: raise ReviewError("BUNDLE_RECOVERY_RAW_SHA_MISMATCH")
 if x64.get("receipt_fingerprint")!=X64_FP or fp(x64)!=X64_FP or arm.get("receipt_fingerprint")!=ARM_FP or fp(arm)!=ARM_FP or x64.get("samples")!=arm.get("samples") or x64.get("analysis_fingerprint")!=ANALYSIS_FP or arm.get("analysis_fingerprint")!=ANALYSIS_FP: raise ReviewError("BUNDLE_CROSS_ARCH_RECEIPTS_INVALID")
 if rec.get("record_type")!="q104_i19_targeted_acceptance_header_recovery" or rec.get("status")!="RECOVERY_INCOMPLETE" or str(rec.get("source_run_id"))!=str(SOURCE_RUN_ID) or rec.get("source_page_sha256")!=SOURCE_PAGE_SHA256: raise ReviewError("BUNDLE_RECOVERY_IDENTITY_INVALID")
 if rec.get("original_shard_receipt_fingerprints")!=ORIGINAL or rec.get("repaired_shard_receipt_fingerprints")!=REPAIRED or rec.get("input_shard_receipt_fingerprints")!=REPAIRED or rec.get("repaired_accession_set")!=[] or rec.get("summary",{}).get("repaired")!=0: raise ReviewError("BUNDLE_RECOVERY_STATE_INVALID")
 unresolved_list=rec.get("unresolved_accession_set",[]);failed_list=rec.get("failed_accession_set",[]);attempt_list=rec.get("attempts",[])
 unresolved=set(unresolved_list);attempts={z.get("accession"):z for z in attempt_list if isinstance(z,dict)}
 from collections import Counter
 if len(unresolved_list)!=53 or len(unresolved)!=53 or set(failed_list)!=unresolved or len(attempts)!=53 or set(attempts)!=unresolved or dict(Counter(str(z.get("original_failure") or "") for z in attempt_list))!=FAILURE_COUNTS: raise ReviewError("BUNDLE_RECOVERY_COUNTS_INVALID")
 originals={};repaired={}
 for kind,dest,pins in ((original_prefix,originals,ORIGINAL),("repaired",repaired,REPAIRED)):
  for shard,wanted in pins.items():
   name=f"{kind}/{shard}.json";value=json.loads(raw[name])
   if value.get("receipt_fingerprint")!=wanted or fp(value)!=wanted or value.get("shard")!=shard or value.get("source_page_sha256")!=SOURCE_PAGE_SHA256: raise ReviewError("BUNDLE_SHARD_PIN_INVALID:"+name)
   dest[shard]=value
 for kind,values in (("original",originals),("repaired",repaired)):
  for name,pin in ARCHIVES.items():
   row=archive_row(values[pin["shard"]],pin["url"],pin["shard"])
   if row.get("archive_sha256")!=pin["sha"] or row.get("archive_bytes")!=pin["bytes"]: raise ReviewError("BUNDLE_ARCHIVE_ROW_PIN_INVALID:"+kind+":"+name)
   for acc in pin["accessions"]:
    z=attempts.get(acc)
    if not z or z.get("source_archive")!=pin["url"] or z.get("original_failure") not in DATE_FAILURES: raise ReviewError("BUNDLE_TARGET_ATTEMPT_INVALID:"+acc)
    if kind=="repaired" and (row.get("acceptance_failures") or {}).get(acc)!=z.get("original_failure"): raise ReviewError("BUNDLE_REPAIRED_FAILURE_INVALID:"+acc)
 if sha(raw["source_page.html"])!=SOURCE_PAGE_SHA256: raise ReviewError("BUNDLE_SOURCE_PAGE_PIN_INVALID")
 for k,value in extra.items():
  pin=ADDITIONAL[k];samples=value.get("samples",[])
  if value.get("record_type")!=pin["type"] or value.get("status")!="LINEAGE_DIAGNOSTIC_COMPLETE" or value.get("receipt_fingerprint")!=pin["fp"] or fp(value)!=pin["fp"] or str(value.get("source_run_id"))!=str(SOURCE_RUN_ID) or value.get("source_page_sha256")!=SOURCE_PAGE_SHA256: raise ReviewError("BUNDLE_EXTRA_RECEIPT_INVALID:"+k)
  if value.get("source_shard_receipt_fingerprints",{}).get(pin["shard"])!=ORIGINAL[pin["shard"]] or len(samples)!=1 or samples[0].get("accession") not in unresolved: raise ReviewError("BUNDLE_EXTRA_SAMPLE_OR_SHARD_INVALID:"+k)
  sample=samples[0];acc=sample["accession"];usable=[p for p in sample.get("probes",[]) if isinstance(p.get("observed_identity"),dict)]
  dates={p["observed_identity"].get("filing_date") for p in usable};accepts={p["observed_identity"].get("acceptance_datetime") for p in usable}
  if attempts[acc].get("original_failure") not in DATE_FAILURES or sample.get("frozen_failure")!="FILING_DATE_MISMATCH" or sample.get("archive_sha256_match") is not True or len(usable) not in (2,3) or len(dates)!=1 or None in dates or len(accepts)!=1 or None in accepts or next(iter(dates))==sample.get("source_row",{}).get("filing_date_iso"): raise ReviewError("BUNDLE_EXTRA_OBSERVATION_INVALID:"+k)
 targets={a for pin in ARCHIVES.values() for a in pin["accessions"]}
 prior={z["accession"] for z in x64.get("samples",[])}|{z["samples"][0]["accession"] for z in extra.values()}
 date_set={a for a,z in attempts.items() if z.get("original_failure") in DATE_FAILURES}
 if len(prior)!=17 or prior&targets or date_set-prior!=targets or len(date_set)!=36: raise ReviewError("BUNDLE_17_PLUS_19_PARTITION_INVALID")
 inputs={"request":request,"recovery":rec,"original":originals,"repaired":repaired,"x64":x64,"arm64":arm,"extras":extra,"attempts":attempts,"unresolved":unresolved,"prior":prior,"target":targets,"helper_blobs":validate_helpers()}
 return inputs,raw

def publish(xdir:Path,adir:Path,run_id:int,attempt:int,out:Path):
 x=json.loads((xdir/"analysis.json").read_text());a=json.loads((adir/"analysis.json").read_text())
 if x.get("analysis_fingerprint")!=fp(x["analysis"]) or a.get("analysis_fingerprint")!=fp(a["analysis"]) or x["analysis_fingerprint"]!=a["analysis_fingerprint"] or x["analysis"]!=a["analysis"]: raise ReviewError("CROSS_ARCH_ANALYSIS_MISMATCH")
 result=dict(x["analysis"]);result.update({"generated_at_utc":datetime.now(timezone.utc).isoformat(),"workflow_run_id":run_id,"workflow_run_attempt":attempt,"cross_arch_reproduction":{"status":"DETERMINISTIC_ANALYSIS_MATCHED","same_analysis_fingerprint":True,"x64_analysis_fingerprint":x["analysis_fingerprint"],"arm64_analysis_fingerprint":a["analysis_fingerprint"],"x64_platform":"ubuntu-24.04","arm64_platform":"ubuntu-24.04-arm","network_requests_made_on_arm64":0},"receipt_fingerprint":""})
 result["receipt_fingerprint"]=fp(result);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({"status":result["status"],"analysis_fingerprint":x["analysis_fingerprint"],"receipt_fingerprint":result["receipt_fingerprint"],"counts":result["counts"],"gate_cleared":False},sort_keys=True))
 return result

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest="mode",required=True)
 c=sub.add_parser("capture")
 for flag in ("request","recovery-artifact","x64-artifact","arm64-artifact","r4-artifact","r5-artifact","r6-artifact","output-dir"): c.add_argument("--"+flag,type=Path,required=True)
 r=sub.add_parser("replay");r.add_argument("--request",type=Path,required=True);r.add_argument("--capture-dir",type=Path,required=True);r.add_argument("--output-dir",type=Path,required=True);r.add_argument("--expected-analysis-fingerprint",default=None)
 q=sub.add_parser("publish");q.add_argument("--x64-dir",type=Path,required=True);q.add_argument("--arm64-dir",type=Path,required=True);q.add_argument("--workflow-run-id",type=int,required=True);q.add_argument("--workflow-run-attempt",type=int,required=True);q.add_argument("--output",type=Path,required=True)
 a=p.parse_args()
 try:
  if a.mode=="capture":
   req=read_request(a.request);inputs,bundle=load_inputs(req,a.recovery_artifact,a.x64_artifact,a.arm64_artifact,{"r4":a.r4_artifact,"r5":a.r5_artifact,"r6":a.r6_artifact})
   receipt=capture_headers(inputs);result=save_capture(a.output_dir,inputs,bundle,receipt);return 0 if receipt["status"]=="Q104_I19_RESIDUAL_R7_CAPTURE_COMPLETE" else 2
  if a.mode=="replay":
   req=read_request(a.request);inputs,raw=replay_inputs(a.capture_dir/"frozen_inputs",req);capture=json.loads((a.capture_dir/"capture_receipt.json").read_text())
   if capture.get("receipt_fingerprint")!=fp(capture) or capture.get("frozen_input_receipt_fingerprints")!=frozen_fingerprints(inputs) or capture.get("sample_count")!=19 or capture.get("header_route_request_count")!=57: raise ReviewError("BUNDLE_CAPTURE_RECEIPT_INVALID")
   analysis=build_analysis(inputs,capture);analysis_fp=fp(analysis)
   if a.expected_analysis_fingerprint and analysis_fp!=a.expected_analysis_fingerprint: raise ReviewError("CROSS_ARCH_ANALYSIS_FINGERPRINT_MISMATCH")
   a.output_dir.mkdir(parents=True,exist_ok=True);(a.output_dir/"analysis.json").write_text(json.dumps({"analysis":analysis,"analysis_fingerprint":analysis_fp},sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
   print(json.dumps({"status":analysis["status"],"analysis_fingerprint":analysis_fp,"network_requests_made":0,"counts":analysis["counts"]},sort_keys=True));return 0
  publish(a.x64_dir,a.arm64_dir,a.workflow_run_id,a.workflow_run_attempt,a.output);return 0
 except (ReviewError,OSError,ValueError,KeyError,TypeError) as e:
  print(json.dumps({"status":"FAILED_CLOSED","error":f"{type(e).__name__}:{e}"},sort_keys=True),file=sys.stderr);return 2

if __name__=="__main__": raise SystemExit(main())
