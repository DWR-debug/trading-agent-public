"""Review-only source-field analysis for frozen Q104:I19 header observations."""
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path

SOURCE_RUN_ID="38304249742"
SOURCE_ARTIFACT="q104-i19-filing-date-change-header-probe-38304249742-1"
SOURCE_FP="17fa46e3f49b4bb296122a1f6e80b7fbe7e3c134868803b2ddb910f898521412"
R1_FP="c0881b295d37fa34925103b30acbb893a78bbbe230af6e637576dfda4fac86f7"
R2_FP="d85ad092296b38f29fa25147537f52804f9a32d9969051c7f9e9cadff283fe04"
FROZEN={
"RUN_Q104_I19_FILING_DATE_PRECEDENCE_REVIEW":"true",
"REASON":"REVIEW_ONLY_ANALYZE_FROZEN_R1_R2_DATE_CHANGE_HEADER_OBSERVATIONS",
"SOURCE_RUN_ID":SOURCE_RUN_ID,"SOURCE_ARTIFACT":SOURCE_ARTIFACT,"SOURCE_RECEIPT_FINGERPRINT":SOURCE_FP,
"R1_RECEIPT_FINGERPRINT":R1_FP,"R2_RECEIPT_FINGERPRINT":R2_FP,"SAMPLE_COUNT":"8",
"APPLY_FIELD_PRECEDENCE":"false","CHANGE_SOURCE_RECEIPTS":"false","CENSUS_RESTART":"false",
"PERFORMANCE":"false","HOLDOUT_SELECTION":"false","RANKING":"false","TUNING":"false","PROMOTION":"false","LIVE_EXECUTION":"false"}
KEYS=set(FROZEN)|{"REQUEST_SEQUENCE"}

class ReviewError(ValueError): pass

def fingerprint(v):
    p=dict(v); p.pop("receipt_fingerprint",None)
    raw=json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def read_request(path):
    d={}
    for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line or line.strip()!=line or "=" not in line: raise ReviewError(f"REQUEST_INVALID_LINE:{n}")
        k,v=line.split("=",1)
        if not k or not v or k in d: raise ReviewError(f"REQUEST_INVALID_KEY_VALUE:{n}")
        d[k]=v
    if set(d)!=KEYS: raise ReviewError("REQUEST_KEY_SET_MISMATCH")
    for k,v in FROZEN.items():
        if d[k]!=v: raise ReviewError("REQUEST_VALUE_MISMATCH:"+k)
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",d["REQUEST_SEQUENCE"]):
        raise ReviewError("REQUEST_SEQUENCE_INVALID")
    return d

def find_receipt(path):
    if path.is_file(): return path
    matches=sorted(path.rglob("q104-date-change-receipt.json"))
    if len(matches)!=1: raise ReviewError("SOURCE_RECEIPT_COUNT_INVALID")
    return matches[0]

def validate_source(path):
    r=json.loads(find_receipt(path).read_text(encoding="utf-8"))
    if r.get("record_type")!="q104_i19_filing_date_change_header_probe" or r.get("status")!="DATE_CHANGE_HEADER_PROBE_COMPLETE":
        raise ReviewError("SOURCE_RECEIPT_NOT_COMPLETE")
    if r.get("receipt_fingerprint")!=SOURCE_FP or fingerprint(r)!=SOURCE_FP: raise ReviewError("SOURCE_FINGERPRINT_MISMATCH")
    if r.get("source_r1_receipt_fingerprint")!=R1_FP or r.get("source_r2_receipt_fingerprint")!=R2_FP: raise ReviewError("UPSTREAM_FINGERPRINT_MISMATCH")
    if r.get("sample_count")!=8 or r.get("probe_count_captured")!=24: raise ReviewError("SOURCE_COUNTS_MISMATCH")
    return r

def analyze(r):
    out=[]
    for s in r.get("samples",[]):
        p={x.get("route"):x.get("observed_fields") or {} for x in s.get("probes",[])}
        if set(p)!={"index_headers","raw_sgml_header","complete_submission_header_prefix"}:
            raise ReviewError("ROUTE_SET_INCOMPLETE:"+str(s.get("accession")))
        a,b,c=(p["index_headers"],p["raw_sgml_header"],p["complete_submission_header_prefix"])
        ident=("accession","filer_cik","form")
        identity=all(a.get(k) and a.get(k)==b.get(k)==c.get(k) for k in ident)
        filed=bool(a.get("filing_date")) and a.get("filing_date")==b.get("filing_date")==c.get("filing_date")
        accept=bool(a.get("acceptance_datetime")) and a.get("acceptance_datetime")==b.get("acceptance_datetime")==c.get("acceptance_datetime")
        change=bool(a.get("date_of_filing_date_change")) and a.get("date_of_filing_date_change")==b.get("date_of_filing_date_change")
        bulk=s.get("bulk_filing_date"); header=a.get("filing_date"); changed=a.get("date_of_filing_date_change")
        out.append({"accession":s.get("accession"),"bulk_filing_date":bulk,"edgar_header_filing_date":header,
          "date_of_filing_date_change":changed,"acceptance_datetime":a.get("acceptance_datetime"),
          "bulk_date_differs":bool(bulk and header and bulk!=header),"identity_routes_agree":identity,
          "filed_date_routes_agree":filed,"acceptance_routes_agree":accept,"date_change_index_sgml_agree":change,
          "date_change_equals_filing_date":(changed==header) if changed else None,
          "prefix_contains_date_change":bool(c.get("date_of_filing_date_change"))})
    n=len(out)
    counts={"sample_count":n,"bulk_date_differs":sum(x["bulk_date_differs"] for x in out),
      "identity_routes_agree":sum(x["identity_routes_agree"] for x in out),
      "filed_date_routes_agree":sum(x["filed_date_routes_agree"] for x in out),
      "acceptance_routes_agree":sum(x["acceptance_routes_agree"] for x in out),
      "date_change_index_sgml_agree":sum(x["date_change_index_sgml_agree"] for x in out),
      "date_change_equals_filing_date":sum(x["date_change_equals_filing_date"] is True for x in out),
      "date_change_differs_from_filing_date":sum(x["date_change_equals_filing_date"] is False for x in out)}
    ok=n==8 and all(counts[k]==8 for k in ("bulk_date_differs","identity_routes_agree","filed_date_routes_agree","acceptance_routes_agree","date_change_index_sgml_agree"))
    return {"status":"FIELD_PRECEDENCE_REVIEW_PROPOSAL_READY_NOT_APPLIED" if ok else "FIELD_PRECEDENCE_REVIEW_PATTERN_INCOMPLETE",
      "counts":counts,"samples":out,"proposal":{
       "acceptance_event_clock":"Use EDGAR ACCEPTANCE-DATETIME after exact accession/CIK/form validation and cross-route agreement.",
       "official_filing_date":"Where bulk Form 13F FILING_DATE conflicts, retain the bulk value unchanged and use EDGAR header/index filed date as the filed-date field, with an explicit discrepancy flag.",
       "date_of_filing_date_change":"Retain as separate post-acceptance-change metadata; do not substitute it for filing date or acceptance time.",
       "arithmetic_or_imputation":"None; no date shifting, timezone arithmetic, or blanket correction."},
      "limitations":["Eight preselected rows do not establish prevalence across every unresolved accession.",
       "Review-only; do not apply to the production join until separately approved and tested on the exact residual population.",
       "Does not resolve source-vintage, first-public-observation, or performance gates."]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--request",type=Path,required=True); ap.add_argument("--source",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    req=read_request(a.request); source=validate_source(a.source); result=analyze(source)
    receipt={"schema_version":1,"record_type":"q104_i19_filing_date_precedence_review","candidate_id":"Q104:I19",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),"request_sequence":req["REQUEST_SEQUENCE"],
      "source_run_id":SOURCE_RUN_ID,"source_artifact":SOURCE_ARTIFACT,"source_receipt_fingerprint":SOURCE_FP,
      "source_r1_receipt_fingerprint":R1_FP,"source_r2_receipt_fingerprint":R2_FP,**result,
      "source_precedence_applied":False,"acceptance_time_gate_cleared":False,"historical_archive_gate_cleared":False,
      "performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False,
      "official_spec":{"url":"https://www.sec.gov/info/edgar/pdsdissemspec051310.pdf",
       "definitions":{"FILED AS OF DATE":"EDGAR assigned official filing date, or post acceptance new filing date (Post Acceptance Correction).",
       "DATE AS OF CHANGE":"Date when the last Post Acceptance occurred. Optional."}},
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
    receipt["receipt_fingerprint"]=fingerprint(receipt); a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":receipt["status"],"receipt_fingerprint":receipt["receipt_fingerprint"],"counts":receipt["counts"],"source_precedence_applied":False},sort_keys=True))
    if receipt["status"]!="FIELD_PRECEDENCE_REVIEW_PROPOSAL_READY_NOT_APPLIED": raise ReviewError("REVIEW_PATTERN_INCOMPLETE")
    return 0
if __name__=="__main__": raise SystemExit(main())
