"""Verify the USAspending public-observation clock contract for Q221.

Source/PIT structure only. No market outcomes or authorization.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ABOUT="https://www.usaspending.gov/data/about-the-data-download.pdf"
API="https://api.usaspending.gov/docs/endpoints"

def fetch(url:str)->tuple[int,str,bytes]:
    req=urllib.request.Request(url,headers={"User-Agent":"TradingAgent-Public-Q221-Clock-Gate/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:return int(getattr(r,"status",200)),r.headers.get("Content-Type",""),r.read()

def extract(body:bytes)->str:
    from pypdf import PdfReader
    return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(body)).pages)

def run(output:Path)->dict:
    status,ctype,body=fetch(ABOUT)
    text=extract(body); upper=re.sub(r"\s+"," ",text).upper()
    api_status,api_ctype,api_body=fetch(API); api_text=api_body.decode("utf-8",errors="replace").upper()
    out={
      "schema_version":1,"record_type":"q221_usaspending_public_clock_gate","candidate_id":"Q221",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "about_data_status":status,"about_data_content_type":ctype,"about_data_sha256":hashlib.sha256(body).hexdigest(),"about_data_bytes":len(body),
      "contract_update_within_five_days":"WITHIN FIVE DAYS" in upper,
      "publication_following_morning":"PUBLISHED TO USASPENDING.GOV" in upper and "FOLLOWING MORNING" in upper,
      "contract_modification_language_present":"CONTRACT OR MODIFICATION" in upper or "CONTRACT AWARD OR MODIFICATION" in upper,
      "transactions_endpoint_documented":"/API/V2/TRANSACTIONS/" in api_text,
      "api_status":api_status,"api_content_type":api_ctype,"api_bytes":len(api_body),
      "historical_applicability_proven":False,
      "scientific_evidence":False,"performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False,
    }
    out["source_clock_contract_ready"]=all(out[k] for k in ("contract_update_within_five_days","publication_following_morning","transactions_endpoint_documented"))
    out["receipt_fingerprint"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return out

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True);args=ap.parse_args();print(json.dumps(run(args.output),sort_keys=True))