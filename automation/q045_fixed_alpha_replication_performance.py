"""Q045 fixed eight-arm alpha replication performance runner."""
from __future__ import annotations
import argparse,hashlib,json,os,time,urllib.error,urllib.parse,urllib.request
from datetime import timedelta,timezone,datetime
from pathlib import Path
from automation.candidate_validation_50_50_vol_budget import _cs_weights
from automation.cross_asset_trend_replication import _build_weight_path
from data.canonical_snapshot import load_frozen_snapshot
from execution.cost_contract import validate_research_cost_compatibility
from config import settings

TRIAL_ID="T-2026-09-27-065"
UNIVERSE="validation_2026_09_27_q043_fresh_alpha_replication"
SYMBOLS=("AON","CVS","ADSK","BA","T","F","LUV","NFLX")
N=3500
RESEARCH=2798
HOLDOUT=700
RETURNS=3498
FEE=0.001
SLIPPAGE=0.0005
COSTS=(("base",1.0),("stress_1_5x_cost",1.5),("stress_2x_cost",2.0))
YAHOO="https://query1.finance.yahoo.com/v8/finance/chart"

def _fp(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def _manifest(root):
    paths=sorted(Path(root).rglob("coverage_preflight_*.json"))
    if not paths: raise FileNotFoundError("coverage manifest missing")
    return paths[-1]

def _load(root):
    mp=_manifest(root)
    m=json.loads(mp.read_text(encoding="utf-8"))
    if m.get("status")!="coverage_passed": raise ValueError("coverage not passed")
    if m.get("universe")!=UNIVERSE: raise ValueError("universe mismatch")
    if tuple(m.get("symbols",()))!=SYMBOLS: raise ValueError("symbols mismatch")
    if int(m.get("target_common_calendar",-1))!=N: raise ValueError("calendar target mismatch")
    assets=load_frozen_snapshot(mp)
    if tuple(assets)!=SYMBOLS or any(len(v)!=N for v in assets.values()): raise ValueError("snapshot geometry mismatch")
    safety={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}
    if m.get("safety")!=safety: raise RuntimeError("coverage safety mismatch")
    return assets,m

def _returns(c): return [c[i]/c[i-1]-1.0 for i in range(1,len(c))]

def _a1_signal(c,i):
    if i<252:return 0
    s=sum(1 if c[i]/c[i-l]>1 else -1 for l in (21,63,252))
    return 1 if s>0 else -1 if s<0 else 0

def _a1(assets):
    c={s:[b.close for b in assets[s]] for s in SYMBOLS}; out=[]
    for i in range(N):
        active=[s for s in SYMBOLS if _a1_signal(c[s],i)>0]
        w=1/len(active) if active else 0
        out.append({s:(w if s in active else 0) for s in SYMBOLS})
    return tuple(out)

def _a2(assets):
    c={s:[b.close for b in assets[s]] for s in SYMBOLS}; cur={s:0 for s in SYMBOLS}; out=[]
    for i in range(N):
        a=i-21
        if a>=252:
            scores={s:c[s][a]/c[s][a-252]-1 for s in SYMBOLS}
            top=sorted(scores,key=lambda s:(-scores[s],s))[:2]; cur={s:(0.5 if s in top else 0) for s in SYMBOLS}
        out.append(dict(cur))
    return tuple(out)

def _beta(x,m):
    if not x:return 0
    ax=sum(x)/len(x); am=sum(m)/len(m); var=sum((z-am)**2 for z in m)
    return 0 if var<=0 else sum((a-ax)*(b-am) for a,b in zip(x,m))/var

def _beta_map(assets,i):
    a=i-21
    if a<273:return {}
    r={s:_returns([b.close for b in assets[s]]) for s in SYMBOLS}; st=a-273; en=a-21
    m=[sum(r[s][j] for s in SYMBOLS)/len(SYMBOLS) for j in range(st,en)]
    return {s:_beta(r[s][st:en],m) for s in SYMBOLS}

def _a3(assets):
    c={s:[b.close for b in assets[s]] for s in SYMBOLS}; r={s:_returns(c[s]) for s in SYMBOLS}; cur={s:0 for s in SYMBOLS}; out=[]
    for i in range(N):
        a=i-21
        if a>=273:
            st=a-273; en=a-21; m=[sum(r[s][j] for s in SYMBOLS)/len(SYMBOLS) for j in range(st,en)]
            bet={s:_beta(r[s][st:en],m) for s in SYMBOLS}
            sc={s:sum(x-bet[s]*z for x,z in zip(r[s][st:en],m)) for s in SYMBOLS}
            top=sorted(sc,key=lambda s:(-sc[s],s))[:2]; cur={s:(0.5 if s in top else 0) for s in SYMBOLS}
        out.append(dict(cur))
    return tuple(out)

def _a5(assets):
    cur={s:0 for s in SYMBOLS}; out=[]
    for i in range(N):
        b=_beta_map(assets,i)
        if b:
            top=sorted(b,key=lambda s:(b[s],s))[:2]; cur={s:(0.5 if s in top else 0) for s in SYMBOLS}
        out.append(dict(cur))
    return tuple(out)

def _a1b(assets):
    c={s:[b.close for b in assets[s]] for s in SYMBOLS}; cur={s:0 for s in SYMBOLS}; out=[]
    for i in range(N):
        a=i-21
        if a>=252:
            sc={s:c[s][a]/max(c[s][a-251:a+1]) for s in SYMBOLS}
            top=sorted(sc,key=lambda s:(-sc[s],s))[:2]; cur={s:(0.5 if s in top else 0) for s in SYMBOLS}
        out.append(dict(cur))
    return tuple(out)

def _a6(assets):
    cur={s:0 for s in SYMBOLS}; out=[]
    for i in range(N):
        if i>=21:
            sc={}
            for s in SYMBOLS:
                b=assets[s]; count=0
                for j in range(i-20,i+1):
                    overnight=b[j].open/b[j-1].close-1
                    daytime=b[j].close/b[j].open-1
                    if overnight>0 and daytime<0: count+=1
                sc[s]=count
            top=sorted(sc,key=lambda s:(-sc[s],s))[:2]; cur={s:(0.5 if s in top else 0) for s in SYMBOLS}
        out.append(dict(cur))
    return tuple(out)

def _control(assets):
    tr=_build_weight_path(assets,"sma_50_200_inverse_vol"); cs=_cs_weights(assets)
    return tuple({s:0.5*float(tr[i].get(s,0))+0.5*float(cs[i].get(s,0)) for s in SYMBOLS} for i in range(N))

def _avg(weight_sets):
    n=len(weight_sets); return tuple({s:sum(float(ws[i].get(s,0)) for ws in weight_sets)/n for s in SYMBOLS} for i in range(N))

def _rows(assets,w):
    prev={s:0 for s in SYMBOLS}; out=[]
    for i in range(RETURNS):
        gross=turn=0.0
        for s in SYMBOLS:
            b=assets[s]; ret=b[i+2].open/b[i+1].open-1
            ww=float(w[i].get(s,0)); gross+=ww*ret; turn+=abs(ww-prev[s]); prev[s]=ww
        out.append({"timestamp":assets[SYMBOLS[0]][i+2].timestamp,"gross":gross,"turnover":turn})
    return out

def _adjclose(s,start,end):
    p={"period1":int((start-timedelta(days=3)).timestamp()),"period2":int((end+timedelta(days=3)).timestamp()),"interval":"1d","events":"div,splits","includePrePost":"false"}
    u=f"{YAHOO}/{urllib.parse.quote(s,safe='')}?{urllib.parse.urlencode(p)}"
    for attempt in range(4):
        try:
            req=urllib.request.Request(u,headers={"User-Agent":"trading-agent-research/1.0"})
            with urllib.request.urlopen(req,timeout=20) as resp: d=json.loads(resp.read().decode())
            r=d["chart"]["result"][0]
            return {datetime.fromtimestamp(int(ts),tz=timezone.utc):float(v) for ts,v in zip(r["timestamp"],r["indicators"]["adjclose"][0]["adjclose"]) if v is not None}
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,KeyError,IndexError,TypeError,ValueError) as e:
            if attempt==3: raise RuntimeError(f"adjclose unavailable {s}: {e}")
            time.sleep(2**attempt)
    raise RuntimeError("adjclose failure")

def _stats(v,a,b):
    seg=v[a:b]; eq=peak=1.0; gp=gl=0.0; pos=0; dd=0.0
    for x in seg:
        eq*=1+x; peak=max(peak,eq); dd=max(dd,1-eq/peak if eq>0 else 1)
        if x>0:gp+=x;pos+=1
        elif x<0:gl-=x
    return {"period_return":eq-1,"max_drawdown_percent":dd*100,"profit_factor":gp/gl if gl else ("inf" if gp else 0),"positive_day_ratio":pos/len(seg),"day_count":len(seg)}

def _summary(v):
    r=_stats(v,0,RESEARCH); h=_stats(v,RESEARCH,RETURNS); width=RESEARCH//5
    wins=[_stats(v,k*width,RESEARCH if k==4 else (k+1)*width) for k in range(5)]
    gain=sum(max(x["period_return"],0) for x in wins); loss=-sum(min(x["period_return"],0) for x in wins)
    return {"research":r,"holdout":h,"rolling_windows":[{"window_index":i+1,**x} for i,x in enumerate(wins)],
            "rolling_profit_factor":gain/loss if loss else ("inf" if gain else 0),
            "rolling_profitable_window_ratio":sum(x["period_return"]>0 for x in wins)/5,
            "rolling_average_drawdown_percent":sum(x["max_drawdown_percent"] for x in wins)/5,
            "oos_to_is_return_ratio":h["period_return"]/r["period_return"] if r["period_return"]>0 else 0}

def _eval(assets,w,adj):
    rows=_rows(assets,w); gross=[x["gross"] for x in rows]; turn=[x["turnover"] for x in rows]
    sc={}
    for name,m in COSTS: sc[name]=_summary([g-(FEE+SLIPPAGE)*m*t for g,t in zip(gross,turn)])
    total=[]
    for j,row in enumerate(rows):
        sens=0.0; cur=row["timestamp"]; prev=assets[SYMBOLS[0]][j+1].timestamp
        for s in SYMBOLS:
            ac=adj[s].get(cur); ap=adj[s].get(prev)
            if ac is None or ap is None: raise ValueError(f"{s}: adjusted close missing")
            b=assets[s]; orr=b[j+2].open/b[j+1].open-1; crr=b[j+2].close/b[j+1].close-1; arr=ac/ap-1
            sens+=float(w[j].get(s,0))*(orr+arr-crr)
        total.append(sens-(FEE+SLIPPAGE)*turn[j])
    base=sc["base"]; ts=_summary(total)
    gates={
      "research_return_positive":base["research"]["period_return"]>0,
      "research_drawdown_lte_10pct":base["research"]["max_drawdown_percent"]<=10,
      "research_profit_factor_gte_1_10":float("inf") if base["research"]["profit_factor"]=="inf" else base["research"]["profit_factor"]>=1.10,
      "rolling_profit_factor_gte_1_10":(float("inf") if base["rolling_profit_factor"]=="inf" else base["rolling_profit_factor"]>=1.10),
      "rolling_profitable_window_ratio_gte_0_50":base["rolling_profitable_window_ratio"]>=0.50,
      "rolling_average_drawdown_lte_10pct":base["rolling_average_drawdown_percent"]<=10,
      "oos_to_is_return_ratio_gte_0_25":base["oos_to_is_return_ratio"]>=0.25,
      "holdout_return_positive":base["holdout"]["period_return"]>0,
      "holdout_profit_factor_gte_1_10":(float("inf") if base["holdout"]["profit_factor"]=="inf" else base["holdout"]["profit_factor"]>=1.10),
      "holdout_drawdown_lte_10pct":base["holdout"]["max_drawdown_percent"]<=10,
      "stress_1_5x_holdout_nonnegative":sc["stress_1_5x_cost"]["holdout"]["period_return"]>=0,
      "stress_2x_holdout_nonnegative":sc["stress_2x_cost"]["holdout"]["period_return"]>=0,
      "total_return_sensitivity_holdout_nonnegative":ts["holdout"]["period_return"]>=0
    }
    return {"base":base,"stress_1_5x_cost":sc["stress_1_5x_cost"],"stress_2x_cost":sc["stress_2x_cost"],"total_return_sensitivity":ts,
            "gates":gates,"gates_passed":sum(gates.values()),"gates_total":13,"all_gates_passed":all(gates.values()),
            "turnover":{"mean":sum(turn)/len(turn),"sum":sum(turn)}}

def run(prereg,coverage_root,out):
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False: raise RuntimeError("safety")
    p=json.loads(Path(prereg).read_text()); a=next(iter([json.loads(Path(x).read_text()) for x in [prereg]]))
    if p.get("trial_id")!=TRIAL_ID or p.get("status")!="PREREGISTERED_PERFORMANCE": raise ValueError("prereg")
    if any(p["governance"].get(k) is not False for k in ("parameter_search","threshold_search","horizon_search","family_search","asset_search","family_ranking","selection","holdout_used_for_selection","promotion_decision","automatic_promotion")): raise RuntimeError("governance")
    validate_research_cost_compatibility(fee_rate=FEE,slippage_rate=SLIPPAGE)
    assets,manifest=_load(coverage_root)
    adj={s:_adjclose(s,assets[s][0].timestamp,assets[s][-1].timestamp) for s in SYMBOLS}
    arms={
      "CONTROL":_control(assets),
      "A1_TSM_CONSENSUS":_a1(assets),
      "A2_CS_MOMENTUM_TOP2":_a2(assets),
      "A3_RESIDUAL_MOMENTUM_TOP2":_a3(assets),
      "A5_LOW_BETA_TOP2":_a5(assets),
      "A1B_52W_HIGH_TOP2":_a1b(assets),
      "A6_OVERNIGHT_TUGWAR_TOP2":_a6(assets)
    }
    arms["ENSEMBLE_ALL6"]=_avg([arms[k] for k in ("A1_TSM_CONSENSUS","A2_CS_MOMENTUM_TOP2","A3_RESIDUAL_MOMENTUM_TOP2","A5_LOW_BETA_TOP2","A1B_52W_HIGH_TOP2","A6_OVERNIGHT_TUGWAR_TOP2")])
    reports={k:_eval(assets,w,adj) for k,w in arms.items()}
    result={"schema_version":"1.0","trial_id":TRIAL_ID,"status":"COMPLETED","code_version":os.getenv("GITHUB_SHA","UNVERIFIED_LOCAL_CODE"),
      "universe":UNIVERSE,"symbols":list(SYMBOLS),"requested_candles":4000,"target_common_candles":3500,"research_periods":RESEARCH,"holdout_periods":HOLDOUT,
      "initial_capital_eur":2000.0,"coverage_snapshot_fingerprint":manifest.get("snapshot_fingerprint"),"coverage_fingerprint":manifest.get("coverage_fingerprint"),
      "pit_prerequisite":"T-2026-09-27-064","arms":reports,"performance_evaluation":True,"oos_evaluation":True,"holdout_evaluation":True,
      "selection_used":False,"holdout_used_for_selection":False,"parameter_search":False,"asset_search":False,"threshold_search":False,"horizon_search":False,"variant_search":False,"family_ranking":False,
      "governance":{"performance_trial_authorized":True,"selection":False,"holdout_used_for_selection":False,"promotion_decision":False,"automatic_promotion":False},
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
    result["report_fingerprint"]=_fp(result); Path(out).parent.mkdir(parents=True,exist_ok=True); Path(out).write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print("Q045_STATUS: COMPLETED")
    for k,r in reports.items(): print(k,f"{r['gates_passed']}/{r['gates_total']}")
    print("Q045_REPORT_FINGERPRINT:",result["report_fingerprint"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--preregistration",required=True); p.add_argument("--coverage-root",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(); run(Path(a.preregistration),Path(a.coverage_root),Path(a.output))
