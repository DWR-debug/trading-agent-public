"""Q218 SEC multi-channel source gate.

Source/PIT structure only. No market outcomes or authorization.
"""
from __future__ import annotations
import argparse,hashlib,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path

ISSUERS={"AAPL":"320193","MSFT":"789019","AMZN":"1018724","JPM":"19617","XOM":"34088","NVDA":"1045810","WMT":"104169","DIS":"1744489"}
START="2025-01-01"; END="2026-10-05"
UA={"User-Agent":"TradingAgent-Public-Research/1.0 research@example.invalid","Accept-Encoding":"identity"}

def fetch(url:str)->bytes:
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=30) as r:return r.read()

def acceptance(cik:str,accession:str)->str|None:
    base=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-","")}/"
    url=base+f"{accession}-index-headers.html"
    text=fetch(url).decode("utf-8",errors="replace")
    m=re.search(r"<ACCEPTANCE-DATETIME>\s*([0-9]{14})",text,re.I)
    return m.group(1) if m else None

def run(output:Path)->dict:
    issuer_results={}
    for symbol,cik in ISSUERS.items():
        data=json.loads(fetch(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json").decode("utf-8"))
        recent=data.get("filings",{}).get("recent",{})
        forms=recent.get("form",[]); dates=recent.get("filingDate",[]); acc=recent.get("accessionNumber",[]); docs=recent.get("primaryDocument",[]); reports=recent.get("reportDate",[]); items=recent.get("items",[]); accept=[None]*len(forms)
        tenks=[]; earnings=[]; amendments=[]
        for i,form in enumerate(forms):
            fd=dates[i] if i<len(dates) else None
            if form not in {"10-K","10-K/A","8-K","8-K/A"} or not fd or not (START<=fd<=END): continue
            accession=acc[i]; report=reports[i] if i<len(reports) else None; item_field=items[i] if i<len(items) else ""
            if form in {"10-K","10-K/A"}:
                a=acceptance(cik,accession); row={"form":form,"filing_date":fd,"report_date":report,"accession":accession,"primary_document":docs[i] if i<len(docs) else None,"acceptance_datetime":a}
                (amendments if form.endswith("/A") else tenks).append(row)
            elif "2.02" in str(item_field).split(","):
                a=acceptance(cik,accession); earnings.append({"form":form,"filing_date":fd,"report_date":report,"accession":accession,"primary_document":docs[i] if i<len(docs) else None,"acceptance_datetime":a,"items":item_field})
                if form.endswith("/A"): amendments.append({"form":form,"filing_date":fd,"report_date":report,"accession":accession})
        issuer_results[symbol]={"cik":cik,"ten_k_count":len(tenks),"item_2_02_8k_count":len(earnings),"amendment_count":len(amendments),"ten_k_acceptance_count":sum(bool(r["acceptance_datetime"]) for r in tenks),"item_2_02_acceptance_count":sum(bool(r["acceptance_datetime"]) for r in earnings),"ten_k_sample":tenks[:3],"item_2_02_sample":earnings[:5],"event_pairing_deferred":True}
    out={"schema_version":1,"record_type":"q218_sec_multichannel_source_gate","candidate_id":"Q218","generated_at_utc":datetime.now(timezone.utc).isoformat(),"fixed_window":{"start":START,"end":END},"issuer_results":issuer_results,"issuer_count":len(issuer_results),"issuers_with_10k":sum(x["ten_k_count"]>0 for x in issuer_results.values()),"issuers_with_item_2_02_8k":sum(x["item_2_02_8k_count"]>0 for x in issuer_results.values()),"all_required_issuer_channels_observed":all(x["ten_k_count"]>0 and x["item_2_02_8k_count"]>0 and x["ten_k_acceptance_count"]>0 and x["item_2_02_acceptance_count"]>0 for x in issuer_results.values()),"scientific_evidence":False,"performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False}
    out["next_gate"]="DETERMINISTIC_10K_8K_EVENT_PAIR_AND_AMENDMENT_LINEAGE" if out["all_required_issuer_channels_observed"] else "REPAIR_SEC_MULTICHANNEL_COVERAGE"
    out["receipt_fingerprint"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); return out

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args(); print(json.dumps(run(args.output),sort_keys=True))