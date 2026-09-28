"""Q077 fixed source-order coverage-only discovery.
No performance, returns, holdout or ranking is consulted.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import settings
from data.yahoo_loader import load_yahoo_history
from research.asset_universes import list_universes

STUDY_START=date(2011,1,1)
STUDY_END=date(2025,9,24)
TARGET=3500
RAW=5000
# New fixed candidate source-order, created for Q077 only. Order is not performance-derived.
CANDIDATE_POOL=(
 "ABT","ADP","ADI","AMGN","AMAT","APD","BDX","BK","BLK","BMY",
 "CAT","CL","DHR","DIS","FDX","GD","GILD","HAL","HD","HON",
 "IBM","JCI","LMT","LOW","LRCX","MDT","MMM","NKE","NSC","OXY",
 "QCOM","SBUX","SO","TGT","TJX","TXN","UNP","UPS","V","WMT",
 "XEL","CSCO","CMCSA","COST","CVS","DELL","ORCL","PFE"
)

def fp(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def fixed_used_symbols(payload):
    used=set()
    for t in payload.get("trials",[]):
        scope=t.get("data_scope",{})
        if not isinstance(scope,dict): continue
        for k in ("symbols","trend_symbols","cross_sectional_symbols","requested_symbols","universe_symbols"):
            vals=scope.get(k)
            if isinstance(vals,list): used.update(str(x) for x in vals)
    return used

def fetch(symbol):
    quality={}
    bars=load_yahoo_history(symbol,"1d",RAW,allow_partial=True,skip_invalid_ohlc=True,quality_report=quality)
    ts=sorted({b.timestamp.isoformat() for b in bars if STUDY_START<=b.timestamp.date()<=STUDY_END})
    return ts,quality

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    ap.add_argument("--workers",type=int,default=12)
    args=ap.parse_args()
    assert settings.PAPER_ONLY is True
    assert settings.LIVE_TRADING_ENABLED is False
    assert settings.ORDERS_ENABLED is False
    assert settings.AUTOMATIC_PROMOTION is False

    ledger=json.loads((ROOT/"research/evidence/trial_ledger.json").read_text(encoding="utf-8"))
    registered=fixed_used_symbols(ledger)
    registered.update(str(s) for u in list_universes() for s in u.symbols)
    excluded=[s for s in CANDIDATE_POOL if s in registered]
    candidates=[s for s in CANDIDATE_POOL if s not in registered]
    if len(candidates)<8:
        raise RuntimeError("Q077 candidate pool leaves fewer than eight unused symbols")

    results={}
    cache={}
    with ThreadPoolExecutor(max_workers=max(1,args.workers)) as pool:
        futures={pool.submit(fetch,s):s for s in candidates}
        for f in as_completed(futures):
            s=futures[f]
            try:
                ts,q=f.result()
                cache[s]=ts
                results[s]={"symbol":s,"status":"WINDOW_COVERAGE_VALID" if len(ts)>=TARGET else "DATA_INVALID","window_count":len(ts),"window_start":ts[0] if ts else None,"window_end":ts[-1] if ts else None,"quality":q}
            except Exception as exc:
                results[s]={"symbol":s,"status":"DATA_INVALID","window_count":0,"window_start":None,"window_end":None,"quality":{},"error":f"{type(exc).__name__}: {exc}"}

    ordered=[results[s] for s in candidates]
    valid=[x for x in ordered if x["status"]=="WINDOW_COVERAGE_VALID"]
    intersection=None
    selected=[]
    for item in valid:
        s=item["symbol"]
        ts=set(cache[s])
        intersection=ts if intersection is None else intersection & ts
        if intersection is not None and len(intersection)>=TARGET:
            selected.append(item)
        if len(selected)>=12:
            break

    common=sorted(intersection or set())
    common=common[-TARGET:] if len(common)>TARGET else common
    selected_symbols=[x["symbol"] for x in selected]
    payload={
      "schema_version":"1.0",
      "discovery_id":"Q077-FIXED-SOURCE-ORDER-COVERAGE-DISCOVERY-2026-09-28",
      "recorded_at":datetime.now(timezone.utc).isoformat(),
      "study_window":{"start":STUDY_START.isoformat(),"end":STUDY_END.isoformat(),"target_common_count":TARGET,"raw_fetch_count":RAW},
      "source_order_rule":"Q077 CANDIDATE_POOL is frozen in source; registered symbols are excluded; the first unused symbols satisfying only fixed coverage are selected.",
      "candidate_pool":list(CANDIDATE_POOL),
      "eligible_candidate_pool":candidates,
      "excluded_existing_universe_symbols":excluded,
      "results":ordered,
      "coverage_valid_candidates":[x["symbol"] for x in valid],
      "selected_coverage_batch":selected_symbols,
      "selected_common_count":len(common),
      "selected_common_start":common[0] if common else None,
      "selected_common_end":common[-1] if common else None,
      "performance_evaluation":False,
      "holdout_evaluation":False,
      "selection_used":False,
      "asset_selection_by_performance":False,
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}
    }
    payload["fingerprint"]=fp(payload)
    out=Path(args.output)
    if not out.is_absolute(): out=ROOT/out
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Q077_STATUS:", "CANDIDATES_AVAILABLE" if selected_symbols else "NO_COVERAGE_VALID_BATCH")
    print("Q077_SELECTED:",selected_symbols)
    print("Q077_COMMON_COUNT:",len(common))
    print("Q077_FINGERPRINT:",payload["fingerprint"])
    return 0 if selected_symbols else 2

if __name__=="__main__":
    raise SystemExit(main())
