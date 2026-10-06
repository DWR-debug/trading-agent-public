"""Bounded SEC FOIA log source/PIT gate for Q231."""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT_URL="https://www.sec.gov/foia/frequently-requested-documents/foia-logs"
UA="TradingAgent-Public-Q231-SEC-FOIA-Source-Gate/1.0"
EXPECTED={
 "request id","requester name","requester organization","requester fee category",
 "request description","date of request","date of receipt","request status",
 "closed date","final disposition"
}
CONTROLS=(
 ("latest_monthly",re.compile(r"August 2026\s*$",re.I)),
 ("monthly_midpoint",re.compile(r"January 2020\s*$",re.I)),
 ("annual_recent",re.compile(r"2018\s*$",re.I)),
 ("annual_early",re.compile(r"2006\s*$",re.I)),
)
def get(url):
 req=Request(url,headers={"User-Agent":UA,"Accept":"text/csv,application/octet-stream,text/html,*/*","Accept-Encoding":"identity"})
 with urlopen(req,timeout=45) as r:
  return int(getattr(r,"status",200)),dict(r.headers.items()),r.read()
def links(html):
 out=[]
 for href,inner in re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',html,re.I|re.S):
  txt=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",unescape(inner))).strip()
  u=urljoin(ROOT_URL,href)
  if re.search(r"foia-log-.*\.(?:csv|zip)$",u,re.I): out.append((txt,u))
 return out
def header(body):
 line=body.decode("utf-8-sig","replace").splitlines()[0] if body else ""
 return [x.strip().strip('"').lower() for x in line.split(",")]
def probe(label,txt,url):
 try:
  st,h,b=get(url)
  hd=header(b[:131072])
  return {"label":label,"link_text":txt,"url":url,"reachable":st==200,"http_status":st,
          "content_type":h.get("Content-Type"),"bytes_read":len(b),
          "sha256":hashlib.sha256(b).hexdigest(),"header":hd,
          "expected_columns_present":EXPECTED.issubset(hd),
          "notes":[] if EXPECTED.issubset(hd) else ["schema_header_does_not_cover_documented_foia_log_fields"]}
 except Exception as e:
  return {"label":label,"link_text":txt,"url":url,"reachable":False,"http_status":getattr(e,"code",None),
          "content_type":None,"bytes_read":0,"sha256":None,"header":[],"expected_columns_present":False,
          "notes":[f"{type(e).__name__}:{e}"]}
def main():
 p=argparse.ArgumentParser(); p.add_argument("--output",required=True); a=p.parse_args()
 st,h,b=get(ROOT_URL); html=b.decode("utf-8","replace"); ls=links(html)
 chosen={}
 for label,pat in CONTROLS:
  for txt,u in ls:
   if pat.search(txt): chosen[label]=(txt,u); break
 probes=[probe(k,*v) for k,v in chosen.items()]
 missing=[k for k,_ in CONTROLS if k not in chosen]
 archive_ok=st==200 and not missing
 schema_ok=bool(probes) and all(x["expected_columns_present"] for x in probes)
 payload={
  "schema_version":"1.0","task_id":"Q-2026-10-06-Q231-SEC-FOIA-SOURCE-GATE","candidate_id":"Q231",
  "status":"SOURCE_ARCHIVE_SCHEMA_GATE_COMPLETED" if archive_ok and schema_ok else "SOURCE_ARCHIVE_SCHEMA_GATE_INCOMPLETE",
  "generated_at_utc":datetime.now(timezone.utc).isoformat(),
  "source_contract":{"official_source":ROOT_URL,"historical_log_start":"January 2006",
    "historical_log_end_observed":"August 2026","monthly_logs_observed":True,"annual_logs_observed":True,
    "controls":[x[0] for x in CONTROLS]},
  "archive_page":{"http_status":st,"content_type":h.get("Content-Type"),"bytes_read":len(b),
    "sha256":hashlib.sha256(b).hexdigest(),"discovered_log_link_count":len(ls),"missing_controls":missing},
  "probes":probes,
  "pit_contract":{"latent_request_time_is_not_tradable_clock":True,
    "public_observation_clock":"first public SEC FOIA log release containing the request",
    "monthly_annual_cadence_must_be_reconstructed":True,
    "exact_historical_publication_timestamp_proven_by_this_gate":False,
    "requester_classification_hindsight_allowed":False,"future_closed_disposition_rewrites_historical_prefix":False},
  "orthogonality_contract":{"distinct_from_q224_edgar_access_demand":True,
    "q224_measure":"requests/access to published SEC records","q231_measure":"explicit FOIA requests for otherwise non-public SEC records",
    "formal_orthogonality_testing_allowed":False},
  "scientific_boundary":{"performance_authorized":False,"holdout_selection_allowed":False,"ranking_allowed":False,
    "parameter_search_allowed":False,"threshold_search_allowed":False,"horizon_search_allowed":False,
    "promotion_allowed":False,"live_execution_allowed":False},
  "next_gate":"historical publication-clock reconstruction + deterministic requester/category compiler + request-description issuer mapping + Q224 orthogonality audit + independent PIT reproduction"}
 raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False)
 payload["receipt_fingerprint"]=hashlib.sha256(raw.encode()).hexdigest()
 out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({"status":payload["status"],"receipt_fingerprint":payload["receipt_fingerprint"]},sort_keys=True))
if __name__=="__main__": main()
