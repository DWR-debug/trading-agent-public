"""Q070 fixed-rule performance evaluation for the unchanged Q069 candidate bank."""
from __future__ import annotations
import argparse, hashlib, json, os, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from automation.q069_candidate_bank import CANDIDATES, candidate_targets_at
from config import settings
from data.canonical_snapshot import load_frozen_snapshot
from execution.cost_contract import validate_research_cost_compatibility

TRIAL_ID="T-2026-09-28-070-PERFORMANCE"
COVERAGE_ID="T-2026-09-28-070-COVERAGE"
PIT_ID="T-2026-09-28-070-PIT"
N=3500; RESEARCH=2798; HOLDOUT=700
FEE=0.001; SLIPPAGE=0.0005
COSTS=(("base",1.0),("stress_1_5x_cost",1.5),("stress_2x_cost",2.0))
YAHOO="https://query1.finance.yahoo.com/v8/finance/chart"
Safety={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}

def _fp(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("utf-8")).hexdigest()

def _load(path): return json.loads(path.read_text(encoding="utf-8"))

def _preflight(root):
    coverage=_load(root/"research/evidence/q070_coverage_result.json")
    pit=_load(root/"research/evidence/q070_pit_result.json")
    freeze=_load(root/"research/evidence/q070_asset_freeze.json")
    prereg=_load(root/"research/preregistrations/q070_performance_2026_09_28.json")
    for obj,trial,status in ((coverage,COVERAGE_ID,"COVERAGE_PASSED"),(pit,PIT_ID,"PIT_PASSED")):
        if obj.get("trial_id")!=trial or obj.get("status")!=status: raise RuntimeError("Q070 preflight receipt invalid")
        if obj.get("performance_trial_authorized") is not False or obj.get("selection_used") is not False: raise RuntimeError("Q070 preflight receipt has forbidden state")
    if prereg.get("trial_id")!=TRIAL_ID or prereg.get("status")!="PREREGISTERED_PERFORMANCE": raise RuntimeError("Q070 performance preregistration invalid")
    if prereg.get("selection_used") is not False or prereg.get("holdout_used_for_selection") is not False: raise RuntimeError("Q070 preregistration records selection")
    if prereg.get("safety")!=Safety: raise RuntimeError("Q070 performance safety mismatch")
    symbols=tuple(freeze["symbols"])
    if tuple(prereg["symbols"])!=symbols: raise RuntimeError("Q070 asset freeze/prereg symbols mismatch")
    snap=root/"research/runs/q070_coverage"/COVERAGE_ID/"snapshot_manifest.json"
    assets=load_frozen_snapshot(snap)
    if tuple(assets)!=symbols or any(len(assets[s])!=N for s in symbols): raise RuntimeError("Q070 snapshot geometry mismatch")
    if freeze.get("snapshot_fingerprint")!=coverage.get("snapshot_fingerprint"): raise RuntimeError("Q070 snapshot fingerprint mismatch")
    if prereg.get("source_discovery_fingerprint")!=freeze.get("source_discovery_fingerprint"): raise RuntimeError("Q070 discovery fingerprint mismatch")
    return assets,symbols,coverage,pit,freeze,prereg

def _adjclose(symbol,start,end):
    params={"period1":int((start-timedelta(days=3)).timestamp()),"period2":int((end+timedelta(days=3)).timestamp()),"interval":"1d","events":"div,splits","includePrePost":"false"}
    url=f"{YAHOO}/{urllib.parse.quote(symbol,safe="")}?{urllib.parse.urlencode(params)}"
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"trading-agent-research/1.0"})
            with urllib.request.urlopen(req,timeout=20) as response: payload=json.loads(response.read().decode("utf-8"))
            result=payload["chart"]["result"][0]
            return {datetime.fromtimestamp(int(ts),tz=timezone.utc):float(value) for ts,value in zip(result["timestamp"],result["indicators"]["adjclose"][0]["adjclose"]) if value is not None}
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,KeyError,IndexError,TypeError,ValueError) as exc:
            if attempt==3: raise RuntimeError(f"adjusted close unavailable for {symbol}: {exc}") from exc
            time.sleep(2**attempt)
    raise RuntimeError("adjusted close retrieval failed")

def _rows(assets,weights,symbols):
    previous={s:0.0 for s in symbols}; rows=[]; count=N-2
    for i in range(count):
        gross=0.0; turnover=0.0
        for s in symbols:
            bars=assets[s]; ret=bars[i+2].open/bars[i+1].open-1.0; w=float(weights[i].get(s,0.0))
            gross += w*ret; turnover += abs(w-previous[s]); previous[s]=w
        rows.append({"timestamp":assets[symbols[0]][i+2].timestamp,"gross":gross,"turnover":turnover})
    return rows

def _stats(values,start,end):
    seg=values[start:end]; equity=1.0; peak=1.0; gain=0.0; loss=0.0; positive=0; dd=0.0
    for v in seg:
        equity*=1.0+v; peak=max(peak,equity); dd=max(dd,1.0-equity/peak if equity>0 else 1.0)
        if v>0: gain+=v; positive+=1
        elif v<0: loss-=v
    return {"period_return":equity-1.0,"max_drawdown_percent":dd*100.0,"profit_factor":gain/loss if loss else ("inf" if gain else 0.0),"positive_day_ratio":positive/len(seg) if seg else 0.0,"day_count":len(seg)}

def _summary(values):
    research=_stats(values,0,RESEARCH); holdout=_stats(values,RESEARCH,RESEARCH+HOLDOUT); width=RESEARCH//5
    rolling=[_stats(values,i*width,RESEARCH if i==4 else (i+1)*width) for i in range(5)]
    pos=sum(max(x["period_return"],0.0) for x in rolling); neg=-sum(min(x["period_return"],0.0) for x in rolling)
    rpf=pos/neg if neg else ("inf" if pos else 0.0)
    return {"research":research,"holdout":holdout,"rolling_windows":[{"window_index":i+1,**x} for i,x in enumerate(rolling)],"rolling_profit_factor":rpf,"rolling_profitable_window_ratio":sum(x["period_return"]>0 for x in rolling)/5.0,"rolling_average_drawdown_percent":sum(x["max_drawdown_percent"] for x in rolling)/5.0,"oos_to_is_return_ratio":holdout["period_return"]/research["period_return"] if research["period_return"]>0 else 0.0}

def _evaluate(assets,weights,adjusted,symbols):
    rows=_rows(assets,weights,symbols); gross=[x["gross"] for x in rows]; turnover=[x["turnover"] for x in rows]
    stressed={name:_summary([v-(FEE+SLIPPAGE)*m*t for v,t in zip(gross,turnover)]) for name,m in COSTS}
    sensitivity=[]
    for i,row in enumerate(rows):
        current=row["timestamp"]; previous=assets[symbols[0]][i+1].timestamp; value=0.0
        for s in symbols:
            ca=adjusted[s].get(current); pa=adjusted[s].get(previous)
            if ca is None or pa is None: raise RuntimeError(f"{s}: adjusted close missing at {current}")
            b=assets[s]; open_ret=b[i+2].open/b[i+1].open-1.0; close_ret=b[i+2].close/b[i+1].close-1.0; adj_ret=ca/pa-1.0
            value += float(weights[i].get(s,0.0))*(open_ret+adj_ret-close_ret)
        sensitivity.append(value-(FEE+SLIPPAGE)*turnover[i])
    base=stressed["base"]; sens=_summary(sensitivity); pf=base["research"]["profit_factor"]; rpf=base["rolling_profit_factor"]; hpf=base["holdout"]["profit_factor"]
    gates={
        "research_return_positive":base["research"]["period_return"]>0.0,
        "research_drawdown_lte_10pct":base["research"]["max_drawdown_percent"]<=10.0,
        "research_profit_factor_gte_1_10":pf=="inf" or pf>=1.10,
        "rolling_profit_factor_gte_1_10":rpf=="inf" or rpf>=1.10,
        "rolling_profitable_window_ratio_gte_0_50":base["rolling_profitable_window_ratio"]>=0.50,
        "rolling_average_drawdown_lte_10pct":base["rolling_average_drawdown_percent"]<=10.0,
        "oos_to_is_return_ratio_gte_0_25":base["oos_to_is_return_ratio"]>=0.25,
        "holdout_return_positive":base["holdout"]["period_return"]>0.0,
        "holdout_profit_factor_gte_1_10":hpf=="inf" or hpf>=1.10,
        "holdout_drawdown_lte_10pct":base["holdout"]["max_drawdown_percent"]<=10.0,
        "stress_1_5x_holdout_nonnegative":stressed["stress_1_5x_cost"]["holdout"]["period_return"]>=0.0,
        "stress_2x_holdout_nonnegative":stressed["stress_2x_cost"]["holdout"]["period_return"]>=0.0,
        "total_return_sensitivity_holdout_nonnegative":sens["holdout"]["period_return"]>=0.0}
    return {"base":base,"stress_1_5x_cost":stressed["stress_1_5x_cost"],"stress_2x_cost":stressed["stress_2x_cost"],"total_return_sensitivity":sens,"gates":gates,"gates_passed":sum(bool(v) for v in gates.values()),"gates_total":13,"all_gates_passed":all(gates.values()),"turnover":{"mean":sum(turnover)/len(turnover),"sum":sum(turnover)}}

def run(root:Path,output:Path)->dict:
    assets,symbols,coverage,pit,freeze,prereg=_preflight(root)
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False: raise RuntimeError("runtime safety invalid")
    validate_research_cost_compatibility(fee_rate=FEE,slippage_rate=SLIPPAGE)
    weights={name:tuple(candidate_targets_at(assets,i,symbols=symbols)[name] for i in range(N)) for name in CANDIDATES}
    adjusted={s:_adjclose(s,assets[s][0].timestamp,assets[s][-1].timestamp) for s in symbols}
    arms={name:_evaluate(assets,weights[name],adjusted,symbols) for name in CANDIDATES}
    result={"schema_version":"1.0","trial_id":TRIAL_ID,"status":"COMPLETED","code_version":os.getenv("GITHUB_SHA","UNVERIFIED"),"universe":freeze["universe"],"symbols":list(symbols),"requested_candles":4000,"target_common_candles":N,"research_periods":RESEARCH,"holdout_periods":HOLDOUT,"initial_capital_eur":2000.0,"coverage_prerequisite":{"trial_id":COVERAGE_ID,"result_fingerprint":coverage["result_fingerprint"],"snapshot_fingerprint":coverage["snapshot_fingerprint"]},"pit_prerequisite":{"trial_id":PIT_ID,"result_fingerprint":pit["result_fingerprint"]},"asset_freeze_fingerprint":_fp(freeze),"arms":arms,"performance_evaluation":True,"oos_evaluation":True,"holdout_evaluation":True,"selection_used":False,"holdout_used_for_selection":False,"parameter_search":False,"threshold_search":False,"asset_search":False,"horizon_search":False,"variant_search":False,"family_ranking":False,"governance":{"performance_trial_authorized":True,"selection":False,"holdout_used_for_selection":False,"promotion_decision":False,"automatic_promotion":False},"safety":Safety}
    result["report_fingerprint"]=_fp(result); output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    for name,report in arms.items(): print(name,report["gates_passed"],"/13")
    print("Q070_REPORT_FINGERPRINT:",result["report_fingerprint"]); return result

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--repo-root",required=True); p.add_argument("--output",required=True); a=p.parse_args(); run(Path(a.repo_root),Path(a.output))