"""Seven-key feasibility probe for transaction-level recipient_parent_uei."""
import argparse,csv,hashlib,io,json,re,time,urllib.error,urllib.parse,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path

BASE="https://api.usaspending.gov"
SOURCE_PATH="research/evidence/q221_historical_public_boundary_latest.json"
SOURCE_BLOB="b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
SOURCE_FP="9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
PROFILE_RUN="38305074104"
PROFILE_ARTIFACT="q221-current-parent-identity-map-38305074104-1"
PROFILE_FP="ae3a3263d5e7d2545dbdaed7ba7ff1cfe3d4cd00e0403352096dcce4d4797602"
MAX_ROWS=10000
MAX_ZIP=20_000_000
SAMPLES=[
("FA865018C7871|P00002|2019-01-02|177a3747-b140-ab6a-b7ae-902f9229758e-C|L1WZRB6JKWJ4","FA865018C7871","P00002","2019-01-02","177a3747-b140-ab6a-b7ae-902f9229758e-C","L1WZRB6JKWJ4"),
("FA955019C0007|0|2019-01-03|0155c8e6-a61a-f6e8-b051-cc6e70b10a9a-C|UGWNU2AMKF63","FA955019C0007","0","2019-01-03","0155c8e6-a61a-f6e8-b051-cc6e70b10a9a-C","UGWNU2AMKF63"),
("75N95019C00046|P00001|2020-01-02|2309d4fa-d2dc-e341-6ba7-b975d2c0bb79-C|MCKWJYCWNVN3","75N95019C00046","P00001","2020-01-02","2309d4fa-d2dc-e341-6ba7-b975d2c0bb79-C","MCKWJYCWNVN3"),
("HQ072721C0002|0|2021-01-04|0320cebe-e833-c369-f529-c9e0a8f6ae8a-C|NJ4NVMXQAXN3","HQ072721C0002","0","2021-01-04","0320cebe-e833-c369-f529-c9e0a8f6ae8a-C","NJ4NVMXQAXN3"),
("HR001119C0085|P00009|2022-01-03|2035a629-ce00-2f40-97a9-433ae84eb2f9-C|T9XKQSKMW4J1","HR001119C0085","P00009","2022-01-03","2035a629-ce00-2f40-97a9-433ae84eb2f9-C","T9XKQSKMW4J1"),
("FA881820F0102|P00023|2023-01-01|20af0683-f17d-1f8f-38ee-2f11bd124559-C|MMLKPW9JLX64","FA881820F0102","P00023","2023-01-01","20af0683-f17d-1f8f-38ee-2f11bd124559-C","MMLKPW9JLX64"),
("693JJ618F000160|P00006|2024-01-02|1259c73d-3f17-85fc-f87e-aca5d2bf99f7-C|EQ76N7H4NW57","693JJ618F000160","P00006","2024-01-02","1259c73d-3f17-85fc-f87e-aca5d2bf99f7-C","EQ76N7H4NW57")]
FROZEN={"RUN_Q221_TRANSACTION_PARENT_UEI_PROBE":"true","REASON":"TEST_DOCUMENTED_TRANSACTION_DOWNLOAD_PARENT_UEI_FIELD_ON_SEVEN_FROZEN_PARENT_LEADS","SOURCE_RECEIPT_PATH":SOURCE_PATH,"SOURCE_RECEIPT_GIT_BLOB_SHA":SOURCE_BLOB,"SOURCE_RECEIPT_FINGERPRINT":SOURCE_FP,"PROFILE_RUN_ID":PROFILE_RUN,"PROFILE_ARTIFACT":PROFILE_ARTIFACT,"PROFILE_RECEIPT_FINGERPRINT":PROFILE_FP,"SAMPLE_COUNT":"7","MAX_ROWS":str(MAX_ROWS),"MAX_DOWNLOAD_BYTES":str(MAX_ZIP),"APPLY_HISTORICAL_MAPPING":"false","FREEZE_RECIPIENT_TO_ISSUER_MAPPING":"false","PERFORMANCE":"false","HOLDOUT_SELECTION":"false","RANKING":"false","TUNING":"false","PROMOTION":"false","LIVE_EXECUTION":"false"}
class ProbeError(ValueError): pass
def sha(b): return hashlib.sha256(b).hexdigest()
def blob(b): return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def fp(v):
 d=dict(v);d.pop("receipt_fingerprint",None)
 return sha(json.dumps(d,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode())
def norm(v): return "" if v is None else str(v).strip()
def read_request(p):
 d={}
 for n,line in enumerate(p.read_text().splitlines(),1):
  if not line or line.strip()!=line or "=" not in line: raise ProbeError(f"REQUEST_LINE_INVALID:{n}")
  k,v=line.split("=",1)
  if not k or not v or k in d: raise ProbeError(f"REQUEST_KEY_INVALID:{n}")
  d[k]=v
 if set(d)!=set(FROZEN)|{"REQUEST_SEQUENCE"}: raise ProbeError("REQUEST_KEYS_MISMATCH")
 for k,v in FROZEN.items():
  if d[k]!=v: raise ProbeError("REQUEST_VALUE_MISMATCH:"+k)
 if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",d["REQUEST_SEQUENCE"]): raise ProbeError("REQUEST_SEQUENCE_INVALID")
 return d
def validate_inputs(source_path,profile_path):
 raw=source_path.read_bytes()
 if blob(raw)!=SOURCE_BLOB or (lambda x: x.get("receipt_fingerprint")!=SOURCE_FP or fp(x)!=SOURCE_FP)(json.loads(raw)): raise ProbeError("SOURCE_RECEIPT_MISMATCH")
 source=json.loads(raw)
 profile=json.loads(profile_path.read_text())
 if profile.get("record_type")!="q221_current_parent_identity_lead_map" or profile.get("status")!="CURRENT_PARENT_MAP_COMPLETE_HISTORY_UNPROVEN" or profile.get("receipt_fingerprint")!=PROFILE_FP or fp(profile)!=PROFILE_FP: raise ProbeError("PROFILE_MAP_RECEIPT_MISMATCH")
 tx={x["transaction_key"]:x for x in source["transactions"]}
 pm={x["recipient_id"]:x for x in profile["recipients"]}
 if len(pm)!=247 or profile.get("verified_profile_count")!=247: raise ProbeError("PROFILE_MAP_COUNT_MISMATCH")
 for key,award,mod,date,rid,uei in SAMPLES:
  row=tx.get(key); p=pm.get(rid)
  if not row or any(row.get(k)!=v for k,v in (("award_id",award),("modification",mod),("action_date",date),("recipient_id",rid),("recipient_uei",uei))): raise ProbeError("FROZEN_TRANSACTION_MISMATCH:"+key)
  if not p or p.get("recipient_uei")!=uei or p.get("current_parent_classification")!="CURRENT_PARENT_ENTITY_LEAD": raise ProbeError("PROFILE_LEAD_MISMATCH:"+rid)
 return source,profile,pm
MAX_API_ATTEMPTS=4
RETRYABLE_HTTP_STATUSES={429,500,502,503,504}
def api(url,body=None):
 h={"User-Agent":"DWR-debug/trading-agent-public Q221 transaction parent UEI probe/1.0","Accept":"application/json","Connection":"close"}; data=None
 if body is not None: h["Content-Type"]="application/json";data=json.dumps(body,separators=(",",":")).encode()
 last_error=None
 for attempt in range(MAX_API_ATTEMPTS):
  req=urllib.request.Request(url,data=data,headers=h,method="POST" if body is not None else "GET")
  try:
   with urllib.request.urlopen(req,timeout=30) as r:
    b=r.read(2_000_001)
    if len(b)>2_000_000: raise ProbeError("API_JSON_OVER_LIMIT")
    try: payload=json.loads(b.decode())
    except (UnicodeDecodeError,json.JSONDecodeError) as e: raise ProbeError("API_JSON_INVALID") from e
    return payload,len(b)
  except urllib.error.HTTPError as e:
   detail=e.read(500).decode(errors="replace")
   last_error=ProbeError("API_HTTP_ERROR:"+str(e.code)+":"+detail)
   if e.code not in RETRYABLE_HTTP_STATUSES or attempt+1>=MAX_API_ATTEMPTS: raise last_error from e
  except (urllib.error.URLError,TimeoutError,OSError) as e:
   last_error=ProbeError("API_TRANSPORT_ERROR:"+type(e).__name__+":"+str(getattr(e,"reason",e))[:300])
   if attempt+1>=MAX_API_ATTEMPTS: raise last_error from e
  time.sleep(min(2**attempt,8))
 raise ProbeError("API_RETRY_EXHAUSTED:"+str(last_error))
def incomplete_receipt(req,error):
 receipt={"schema_version":1,"record_type":"q221_transaction_parent_uei_feasibility_probe","candidate_id":"Q221","status":"TRANSACTION_PARENT_UEI_PROBE_INCOMPLETE","generated_at_utc":datetime.now(timezone.utc).isoformat(),"request_sequence":req.get("REQUEST_SEQUENCE") if isinstance(req,dict) else None,"source_receipt_path":SOURCE_PATH,"source_receipt_git_blob_sha":SOURCE_BLOB,"source_receipt_fingerprint":SOURCE_FP,"profile_map_run_id":PROFILE_RUN,"profile_map_artifact":PROFILE_ARTIFACT,"profile_map_receipt_fingerprint":PROFILE_FP,"error_type":type(error).__name__,"error":str(error)[:900],"preflight_count":None,"download_rows_matched":0,"matches":[],"historical_parent_lineage_proven":False,"recipient_to_issuer_mapping_frozen":False,"historical_first_public_observation_proven":False,"gate_positive":False,"performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False,"next_gate":"Bounded probe did not complete. Inspect the recorded error and retry at most once after a transient upstream outage; no mapping or historical gate may change.","safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
 receipt["receipt_fingerprint"]=fp(receipt)
 return receipt
def main_run(req,source_path,profile_path,out):
 source,profile,pm=validate_inputs(source_path,profile_path)
 filters={"award_ids":[f'"{s[1]}"' for s in SAMPLES],"time_period":[{"start_date":s[3],"end_date":s[3],"date_type":"action_date"} for s in SAMPLES]}
 count,cb=api(BASE+"/api/v2/download/count/",{"filters":filters,"spending_level":"transactions"})
 n=int(count.get("calculated_count",count.get("calculated_transaction_count",-1)))
 if n<0 or n>MAX_ROWS or count.get("rows_gt_limit") is True or count.get("transaction_rows_gt_limit") is True: raise ProbeError("COUNT_OUT_OF_BOUNDS:"+str(n))
 cols=["award_id_piid","action_date","modification_number","recipient_id","recipient_uei","recipient_parent_uei","generated_internal_id","internal_id","last_modified_date","issued_date"]
 dl,db=api(BASE+"/api/v2/download/transactions/",{"filters":filters,"columns":cols,"file_format":"csv","limit":MAX_ROWS})
 if not dl.get("status_url"): raise ProbeError("DOWNLOAD_STATUS_URL_MISSING")
 status_url=dl["status_url"]; u=urllib.parse.urlparse(status_url)
 if u.hostname in ("localhost","127.0.0.1"): status_url=urllib.parse.urljoin(BASE,u.path+("?"+u.query if u.query else ""))
 status=None; pb=0; file_url=None
 for _ in range(96):
  status,sb=api(status_url);pb+=sb
  state=norm(status.get("status")).lower()
  if state in ("ready","complete","completed"):
   file_url=status.get("file_url") or status.get("url") or dl.get("file_url");break
  if state in ("failed","error"): raise ProbeError("DOWNLOAD_FAILED:"+str(status.get("message","")))
  time.sleep(5)
 if not file_url: raise ProbeError("DOWNLOAD_POLL_TIMEOUT_OR_NO_URL")
 file_url=urllib.parse.urljoin(BASE+"/",file_url)
 with urllib.request.urlopen(urllib.request.Request(file_url,headers={"User-Agent":"DWR-debug/trading-agent-public Q221 parent UEI probe/1.0"}),timeout=30) as r: zbytes=r.read(MAX_ZIP+1)
 if len(zbytes)>MAX_ZIP: raise ProbeError("DOWNLOAD_ZIP_OVER_LIMIT")
 matches=[]
 with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
  csvs=[n for n in z.namelist() if n.lower().endswith(".csv")]
  for name in csvs:
   with z.open(name) as f:
    reader=csv.DictReader(io.TextIOWrapper(f,encoding="utf-8-sig",errors="replace",newline=""))
    if "recipient_parent_uei" not in (reader.fieldnames or []) or "award_id_piid" not in (reader.fieldnames or []): continue
    rows=list(reader)
    for key,award,mod,date,rid,uei in SAMPLES:
     found=[x for x in rows if norm(x.get("award_id_piid"))==award and norm(x.get("modification_number"))==mod and norm(x.get("action_date"))==date and norm(x.get("recipient_id"))==rid and norm(x.get("recipient_uei"))==uei]
     if len(found)!=1: raise ProbeError("EXACT_ROW_MATCH_COUNT:"+key+":"+str(len(found)))
     row=found[0];current=norm((pm[rid].get("current_profile_observation") or {}).get("profile",{}).get("parent_uei"));parent=norm(row.get("recipient_parent_uei"))
     matches.append({"transaction_key":key,"recipient_parent_uei_transaction":parent or None,"recipient_parent_uei_current_profile":current or None,"exact_field_equality":(parent==current) if parent and current else None,"last_modified_date":norm(row.get("last_modified_date")) or None,"issued_date":norm(row.get("issued_date")) or None,"download_row_sha256":sha(json.dumps(row,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode())})
    break
 if len(matches)!=7: raise ProbeError("MATCHED_ROW_COUNT_INVALID:"+str(len(matches)))
 receipt={"schema_version":1,"record_type":"q221_transaction_parent_uei_feasibility_probe","candidate_id":"Q221","status":"TRANSACTION_PARENT_UEI_PROBE_COMPLETE","generated_at_utc":datetime.now(timezone.utc).isoformat(),"request_sequence":req["REQUEST_SEQUENCE"],"source_receipt_path":SOURCE_PATH,"source_receipt_git_blob_sha":SOURCE_BLOB,"source_receipt_fingerprint":SOURCE_FP,"profile_map_run_id":PROFILE_RUN,"profile_map_artifact":PROFILE_ARTIFACT,"profile_map_receipt_fingerprint":PROFILE_FP,"count_endpoint":BASE+"/api/v2/download/count/","download_endpoint":BASE+"/api/v2/download/transactions/","preflight_count":n,"download_rows_matched":len(matches),"download_zip_bytes":len(zbytes),"download_zip_sha256":sha(zbytes),"api_json_bytes":{"count":cb,"download_post":db,"polling":pb},"columns":cols,"filters":filters,"matches":matches,"transaction_parent_field":"recipient_parent_uei","field_semantics":"USAspending transaction download maps recipient_parent_uei to ultimate_parent_uei from the FPDS/FABS transaction record; current downloadable view is not an immutable first-public snapshot.","historical_parent_lineage_proven":False,"recipient_to_issuer_mapping_frozen":False,"historical_first_public_observation_proven":False,"performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False,"next_gate":"If the transaction field is available, plan a count-preflighted extraction for the full 348 frozen transaction keys; separately prove historical lineage and parent-UEI-to-issuer identity.","safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
 receipt["transaction_parent_uei_observed_count"]=sum(bool(x["recipient_parent_uei_transaction"]) for x in matches)
 receipt["exact_field_equality_count"]=sum(x["exact_field_equality"] is True for x in matches)
 receipt["receipt_fingerprint"]=fp(receipt);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"status":receipt["status"],"receipt_fingerprint":receipt["receipt_fingerprint"],"preflight_count":n,"matched":len(matches),"parent_uei_observed":receipt["transaction_parent_uei_observed_count"],"exact_field_equality":receipt["exact_field_equality_count"],"zip_bytes":len(zbytes)},sort_keys=True))
def main():
 p=argparse.ArgumentParser();p.add_argument("--request",type=Path,required=True);p.add_argument("--source",type=Path,required=True);p.add_argument("--profile-map",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
 req=None
 try:
  req=read_request(a.request)
  main_run(req,a.source,a.profile_map,a.output)
  return 0
 except Exception as error:
  receipt=incomplete_receipt(req,error)
  a.output.parent.mkdir(parents=True,exist_ok=True)
  a.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\\n",encoding="utf-8")
  print(json.dumps({"status":receipt["status"],"error_type":receipt["error_type"],"receipt_fingerprint":receipt["receipt_fingerprint"],"performance_authorization":False,"gate_positive":False},sort_keys=True))
  return 2
if __name__=="__main__":raise SystemExit(main())
