"""Q044 PIT-only mutation harness for six fixed price/OHLCV alpha mechanisms."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

SYMBOLS=("AON","CVS","ADSK","BA","T","F","LUV","NFLX")
TARGET_COUNT=3500
MIN_HISTORY=273
STEP=113

def _fp(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def _load(root):
    assets={}
    for s in SYMBOLS:
        rows=[]
        with (Path(root)/s/"1d.csv").open(newline="",encoding="utf-8") as h:
            for r in csv.DictReader(h):
                rows.append({k:(r[k] if k=="timestamp" else float(r[k])) for k in ("timestamp","open","high","low","close","volume")})
        if len(rows)!=TARGET_COUNT:
            raise ValueError(f"{s}: expected {TARGET_COUNT} rows, got {len(rows)}")
        assets[s]=rows
    return assets

def _returns(closes):
    return [closes[i]/closes[i-1]-1.0 for i in range(1,len(closes))]

def _a1(assets,index):
    out={}
    for s in SYMBOLS:
        c=[b["close"] for b in assets[s]]
        if index<252: out[s]=0; continue
        score=sum(1 if c[index]/c[index-l]>1 else -1 for l in (21,63,252))
        out[s]=1 if score>0 else -1 if score<0 else 0
    return out

def _anchor(index): return index-21

def _a2(assets,index):
    a=_anchor(index)
    if a<252: return ()
    scores={s:assets[s][a]["close"]/assets[s][a-252]["close"]-1.0 for s in SYMBOLS}
    return tuple(sorted(scores,key=lambda s:(-scores[s],s))[:2])

def _beta(x,m):
    if not x:return 0.0
    xm=sum(x)/len(x); mm=sum(m)/len(m)
    var=sum((z-mm)**2 for z in m)
    if var<=0:return 0.0
    return sum((a-xm)*(b-mm) for a,b in zip(x,m))/var

def _beta_inputs(assets,index):
    a=_anchor(index)
    if a<273:return {}
    r={s:_returns([b["close"] for b in assets[s]]) for s in SYMBOLS}
    start=a-273; end=a-21
    market=[sum(r[s][i] for s in SYMBOLS)/len(SYMBOLS) for i in range(start,end)]
    return {s:_beta(r[s][start:end],market) for s in SYMBOLS}

def _a3(assets,index):
    a=_anchor(index)
    if a<273:return ()
    r={s:_returns([b["close"] for b in assets[s]]) for s in SYMBOLS}
    start=a-273; end=a-21
    market=[sum(r[s][i] for s in SYMBOLS)/len(SYMBOLS) for i in range(start,end)]
    betas={s:_beta(r[s][start:end],market) for s in SYMBOLS}
    scores={s:sum(x-betas[s]*m for x,m in zip(r[s][start:end],market)) for s in SYMBOLS}
    return tuple(sorted(scores,key=lambda s:(-scores[s],s))[:2])

def _a5(assets,index):
    betas=_beta_inputs(assets,index)
    return tuple(sorted(betas,key=lambda s:(betas[s],s))[:2]) if betas else ()

def _a1b(assets,index):
    a=_anchor(index)
    if a<252:return ()
    scores={}
    for s in SYMBOLS:
        c=[b["close"] for b in assets[s]]
        h=max(c[a-251:a+1])
        scores[s]=c[a]/h if h else 0.0
    return tuple(sorted(scores,key=lambda s:(-scores[s],s))[:2])

def _a6(assets,index):
    if index<21:return ()
    start=index-20
    scores={}
    for s in SYMBOLS:
        bars=assets[s]; count=0
        for i in range(start,index+1):
            overnight=bars[i]["open"]/bars[i-1]["close"]-1.0
            daytime=bars[i]["close"]/bars[i]["open"]-1.0
            if overnight>0 and daytime<0: count+=1
        scores[s]=count
    return tuple(sorted(scores,key=lambda s:(-scores[s],s))[:2])

def _signals(assets,index):
    return {"A1":_a1(assets,index),"A2":_a2(assets,index),"A3":_a3(assets,index),"A5":_a5(assets,index),"A1B":_a1b(assets,index),"A6":_a6(assets,index)}

def _mutate(assets,index,mode):
    out={s:[dict(b) for b in bars] for s,bars in assets.items()}
    for s,bars in out.items():
        for i in range(index+1,len(bars)):
            b=bars[i]
            if mode=="future":
                bars[i]={**b,"open":b["open"]*0.2,"high":b["high"]*1.7,"low":b["low"]*0.4,"close":b["close"]*1.5}
            elif mode=="next" and i==index+1:
                bars[i]={**b,"open":b["open"]*9,"high":b["high"]*9,"low":b["low"]*0.1,"close":b["close"]*0.1}
    return out

def run(root,output):
    assets=_load(root); checks=[]
    for idx in range(MIN_HISTORY,TARGET_COUNT-1,STEP):
        original=_signals(assets,idx)
        if original!=_signals(_mutate(assets,idx,"future"),idx):
            raise AssertionError(f"future mutation changed Q044 output at {idx}")
        if original!=_signals(_mutate(assets,idx,"next"),idx):
            raise AssertionError(f"next-session mutation changed Q044 output at {idx}")
        checks.append({"index":idx,"signals":original})
    result={
      "schema_version":"1.0","trial_id":"T-2026-09-27-064","status":"PIT_PASSED",
      "universe":"validation_2026_09_27_q043_fresh_alpha_replication","symbols":list(SYMBOLS),
      "checked_decision_points":len(checks),
      "mechanisms":["A1_TSM_CONSENSUS","A2_CS_MOMENTUM_TOP2","A3_RESIDUAL_MOMENTUM_TOP2","A5_LOW_BETA_TOP2","A1B_52W_HIGH_TOP2","A6_OVERNIGHT_TUGWAR_TOP2"],
      "future_mutation_checks_passed":True,"next_session_mutation_checks_passed":True,
      "performance_evaluation":False,"oos_evaluation":False,"holdout_evaluation":False,
      "selection_used":False,"holdout_used_for_selection":False,
      "governance":{"performance_trial_authorized":False,"automatic_promotion":False,"parameter_search":False,"threshold_search":False,"horizon_search":False,"family_search":False},
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
      "checks_fingerprint":_fp(checks)
    }
    result["report_fingerprint"]=_fp(result)
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Q044_STATUS:",result["status"])
    print("CHECKED_DECISION_POINTS:",result["checked_decision_points"])
    print("REPORT_FINGERPRINT:",result["report_fingerprint"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--universe-root",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(); run(Path(a.universe_root),Path(a.output))
