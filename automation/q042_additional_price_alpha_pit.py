"""Q042 PIT-only mutation harness for additional price/OHLCV candidates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

SYMBOLS=("IVE","IWL","DLN","DHS","DON","DES","USRT","ITB")
TARGET_COUNT=3500
DECISION_STEP=113
MIN_HISTORY=252+21+21

def _fp(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def _load(root):
    assets={}
    for s in SYMBOLS:
        rows=[]
        with (Path(root)/s/"1d.csv").open(newline="",encoding="utf-8") as h:
            for r in csv.DictReader(h):
                rows.append({
                    "timestamp":r["timestamp"],"open":float(r["open"]),"high":float(r["high"]),
                    "low":float(r["low"]),"close":float(r["close"]),"volume":float(r["volume"])
                })
        if len(rows)!=TARGET_COUNT:
            raise ValueError(f"{s}: expected {TARGET_COUNT} rows, got {len(rows)}")
        assets[s]=rows
    return assets

def _a1b_scores(assets,index):
    anchor=index-21
    if anchor<252:
        return {}
    scores={}
    for s in SYMBOLS:
        series=[x["close"] for x in assets[s]]
        high=max(series[anchor-251:anchor+1])
        scores[s]=series[anchor]/high if high else 0.0
    return scores

def _a6_scores(assets,index):
    start=index-20
    if start<1:
        return {}
    scores={}
    for s in SYMBOLS:
        count=0
        bars=assets[s]
        for i in range(start,index+1):
            overnight=bars[i]["open"]/bars[i-1]["close"]-1.0
            daytime=bars[i]["close"]/bars[i]["open"]-1.0
            if overnight>0 and daytime<0:
                count+=1
        scores[s]=count
    return scores

def _signals(assets,index):
    a1=_a1b_scores(assets,index)
    a6=_a6_scores(assets,index)
    return {
      "A1B_52W_HIGH_TOP2":tuple(sorted(a1,key=lambda s:(-a1[s],s))[:2]) if a1 else (),
      "A6_OVERNIGHT_TUGWAR_TOP2":tuple(sorted(a6,key=lambda s:(-a6[s],s))[:2]) if a6 else ()
    }

def _mutate(assets,index,mode):
    out={s:[dict(x) for x in bars] for s,bars in assets.items()}
    for s,bars in out.items():
        for i in range(index+1,len(bars)):
            b=bars[i]
            if mode=="future":
                bars[i]={**b,"open":b["open"]*0.2,"high":b["high"]*1.7,"low":b["low"]*0.4,"close":b["close"]*1.5}
            elif mode=="next" and i==index+1:
                bars[i]={**b,"open":b["open"]*9.0,"high":b["high"]*9.0,"low":b["low"]*0.1,"close":b["close"]*0.1}
    return out

def run(root,output):
    assets=_load(root)
    checks=[]
    for index in range(MIN_HISTORY,TARGET_COUNT-1,DECISION_STEP):
        original=_signals(assets,index)
        assert original==_signals(_mutate(assets,index,"future"), index), index
        assert original==_signals(_mutate(assets,index,"next"), index), index
        checks.append({"index":index,"signals":original})
    result={
      "schema_version":"1.0","trial_id":"T-2026-09-27-061","status":"PIT_PASSED",
      "universe":"validation_2026_09_27_q039_price_only_alpha_pit","symbols":list(SYMBOLS),
      "checked_decision_points":len(checks),
      "mechanisms":["A1B_52W_HIGH_TOP2","A6_OVERNIGHT_TUGWAR_TOP2"],
      "future_mutation_checks_passed":True,"next_session_mutation_checks_passed":True,
      "performance_evaluation":False,"oos_evaluation":False,"holdout_evaluation":False,
      "selection_used":False,"holdout_used_for_selection":False,
      "governance":{"performance_trial_authorized":False,"automatic_promotion":False,"parameter_search":False,"family_search":False},
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
      "checks_fingerprint":_fp(checks)
    }
    result["report_fingerprint"]=_fp(result)
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Q042_STATUS:",result["status"])
    print("CHECKED_DECISION_POINTS:",result["checked_decision_points"])
    print("REPORT_FINGERPRINT:",result["report_fingerprint"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--universe-root",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(); run(Path(a.universe_root),Path(a.output))
