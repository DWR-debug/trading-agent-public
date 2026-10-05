"""Q211-Q213 literature-frontier source feasibility. Discovery-only."""
from __future__ import annotations
import argparse,hashlib,json,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INVENTORY=ROOT/"research/frontier/q211_q213_literature_frontier_2026_10_05.json"
PROBES={
 "USPTO_OPEN_DATA":{"url":"https://data.uspto.gov/","markers":["USPTO","Open Data"]},
 "SEC_SUBMISSIONS":{"url":"https://data.sec.gov/submissions/CIK0000320193.json","markers":["filings","accessionNumber"]},
 "YAHOO_5M_RECENT":{"url":"https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=5m&range=60d","markers":["chart","timestamp"]}}
def probe(name,s):
 req=urllib.request.Request(s["url"],headers={"User-Agent":"Trading-Agent-OS/1.0 research-feasibility"})
 start=time.monotonic()
 try:
  with urllib.request.urlopen(req,timeout=20) as r:
   body=r.read(250000).decode("utf-8","replace"); status=getattr(r,"status",200)
  hits=[m for m in s["markers"] if m.lower() in body.lower()]
  return {"name":name,"http_status":status,"marker_hits":hits,"marker_complete":len(hits)==len(s["markers"])}
 except Exception as e:
  return {"name":name,"error":f"{type(e).__name__}: {e}"}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",default=str(ROOT/"research/evidence/q211_q213_literature_source_feasibility")); a=ap.parse_args()
 p={k:probe(k,v) for k,v in PROBES.items()}
 r={"schema_version":"1.0","task_id":"Q-2026-10-05-Q211-Q213-LITERATURE-SOURCE-FEASIBILITY","generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"paper_only":True,"performance_authorization":False,"selection_used":False,"ranking":False,"tuning":False,"probes":p,"candidate_assessments":{
 "Q211":{"source_access":"PASS_SOURCE_ACCESS" if p["USPTO_OPEN_DATA"].get("marker_complete") else "SOURCE_ACCESS_UNPROVEN","pit_status":"NOT_PROVEN","performance_allowed":False},
 "Q212":{"source_access":"PASS_SOURCE_ACCESS" if p["SEC_SUBMISSIONS"].get("marker_complete") else "SOURCE_ACCESS_UNPROVEN","pit_status":"NOT_PROVEN","performance_allowed":False},
 "Q213":{"source_access":"CURRENT_WINDOW_ACCESS_ONLY" if p["YAHOO_5M_RECENT"].get("marker_complete") else "SOURCE_ACCESS_UNPROVEN","pit_status":"BLOCKED_BY_HISTORICAL_INTRADAY_ARCHIVE_REQUIREMENT","performance_allowed":False}},
 "inventory_sha256":hashlib.sha256(INVENTORY.read_bytes()).hexdigest(),
 "safety_invariants":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False,"paid_resources_allowed":False}}
 out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True); (out/"q211_q213_source_feasibility.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8"); print(json.dumps(r,indent=2))
if __name__=="__main__": main()
