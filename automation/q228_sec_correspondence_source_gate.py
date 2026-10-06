"""Deterministic SEC filing-review correspondence source gate for Q228.

Source/PIT structure only. No market outcomes, ranking, tuning or authorization.
"""
from __future__ import annotations
import argparse, hashlib, json, re, ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT="https://www.sec.gov/search-filings/edgar-search-assistance/how-search-edgar-correspondence"
SEARCH="https://www.sec.gov/edgar/search/"
UA="TradingAgent-Public-Q228-SEC-Correspondence-Gate/1.0"

def fetch(url):
    req=Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*","Accept-Encoding":"identity"})
    ctx=ssl.create_default_context()
    with urlopen(req,timeout=45,context=ctx) as r:
        b=r.read()
        return int(getattr(r,"status",200)),dict(r.headers.items()),b

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    rows=[]
    for name,url,markers in [
        ("SEC_CORRESPONDENCE_GUIDANCE",ROOT,["publicly releases","20 business days","UPLOAD","CORRESP"]),
        ("SEC_EDGAR_SEARCH",SEARCH,["Filing review correspondence","Last 10 years"])
    ]:
        rec={"name":name,"url":url,"reachable":False,"status":None,"bytes":0,"sha256":None,"missing_markers":[]}
        try:
            st,h,b=fetch(url); t=b.decode("utf-8","replace").lower()
            rec.update(reachable=(st==200),status=st,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),
                       missing_markers=[m for m in markers if m.lower() not in t])
        except Exception as e:
            rec["error"]=f"{type(e).__name__}:{e}"
        rows.append(rec)
    good=all(r["reachable"] and not r["missing_markers"] for r in rows)
    payload={
        "schema_version":1,
        "task_id":"Q-2026-10-06-Q228-SEC-CORRESPONDENCE-SOURCE-GATE",
        "candidate_id":"Q228",
        "status":"SOURCE_STRUCTURE_READY_NO_PERFORMANCE" if good else "SOURCE_STRUCTURE_INCOMPLETE",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "source_contract":{
            "public_release_start":"SEC public release program documented in 2005; guidance covers filing reviews for applicable filings after Aug 1 2004",
            "public_observation":"EDGAR public release boundary of the correspondence record",
            "post_review_delay":"SEC guidance describes at least 20 business days after review completion/effectiveness before public release",
            "forms":{"UPLOAD":"SEC-originated letters to filers","CORRESP":"filer response letters"}
        },
        "results":rows,
        "pit_contract":{
            "public_observation_clock_proven":False,
            "latent_review_start_tradable":False,
            "same_day_use_allowed":False,
            "review_cycle_filing_join_completed":False,
            "future_correspondence_mutation_allowed":False
        },
        "next_gate":"historical correspondence archive census + deterministic filing/review-cycle identity compiler + public release clock reconstruction + amendment/closure lineage + independent PIT reproduction",
        "scientific_boundary":{
            "performance_authorized":False,"holdout_selection_allowed":False,"ranking_allowed":False,
            "tuning_allowed":False,"promotion_allowed":False,"live_execution_allowed":False
        }
    }
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    payload["receipt_fingerprint"]=hashlib.sha256(raw.encode()).hexdigest()
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"receipt_fingerprint":payload["receipt_fingerprint"]},sort_keys=True))
if __name__=="__main__": main()
