"""Q117 live Treasury 10-Year demand-state population validation."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from automation.q115_treasury_demand_state import compile_states

API="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
PARAMS={
 "fields":"record_date,security_type,security_term,auction_date,cusip,bid_to_cover_ratio",
 "filter":"security_type:eq:Note,security_term:eq:10-Year,record_date:gte:2011-01-01,record_date:lte:2025-09-24",
 "sort":"auction_date","page[size]":2000
}
UA="trading-agent-public/Q117 research"

def fetch()->list[dict]:
    req=Request(API+"?"+urlencode(PARAMS),headers={"User-Agent":UA})
    with urlopen(req,timeout=45) as r:
        return json.loads(r.read().decode("utf-8")).get("data",[])

def validate(rows:list[dict])->dict:
    if not rows: raise ValueError("Q117_EMPTY_TREASURY_POPULATION")
    states=compile_states(rows)
    counts={k:0 for k in ("FIRST","IMPROVED","WEAKENED","FLAT")}
    for x in states: counts[x["demand_state"]]+=1
    return {"raw_events":len(rows),"compiled_events":len(states),"state_counts":counts,"first_event":states[0],"last_event":states[-1]}

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=Path("research/runs/q117_treasury_demand_population/result.json"));a=p.parse_args()
    rows=fetch()
    result={"schema_version":"1.0","task_id":"Q-2026-10-01-117-TREASURY-DEMAND-POPULATION","status":"TREASURY_DEMAND_STATE_FEASIBILITY_ONLY",
            "source":API,"filters":PARAMS,"validation":validate(rows),
            "governance":{"performance":False,"holdout":False,"selection":False,"ranking":False,"parameter_search":False,"asset_search":False,"threshold_search":False,"horizon_search":False,"performance_authorized":False},
            "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
    result["receipt_fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Q117_STATUS:",result["status"]);print("Q117_EVENTS:",result["validation"]["raw_events"]);print("Q117_STATES:",result["validation"]["state_counts"]);print("Q117_FINGERPRINT:",result["receipt_fingerprint"])
    return 0
if __name__=="__main__":raise SystemExit(main())
