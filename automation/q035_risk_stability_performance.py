"""T056 fixed multi-arm risk/stability performance evaluation.

Control plus RISK-A/B/C/D are evaluated on one fresh fixed universe.
No arm ranking, selection, parameter search or promotion is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from automation.candidate_validation_50_50_vol_budget import _cs_weights
from automation.cross_asset_trend_replication import _build_weight_path
from data.canonical_snapshot import load_frozen_snapshot
from execution.cost_contract import validate_research_cost_compatibility
from portfolio.q030_risk_mechanisms import (
    common_mode_exposure_scale,
    drawdown_throttle_scale,
    position_lifecycle_exit_trigger,
    sleeve_volatility_scale,
)
from config import settings

TRIAL_ID="T-2026-09-27-056"
UNIVERSE="validation_2026_09_27_q030_risk_stability_coverage"
SYMBOLS=("BSV","FAN","JNK","UDN","VCLT","VGIT","SCHR")
TARGET_COUNT=3500
RESEARCH_COUNT=2798
HOLDOUT_COUNT=700
FEE_RATE=0.001
SLIPPAGE_RATE=0.0005
COST_MULTIPLIERS=(("base",1.0),("stress_1_5x_cost",1.5),("stress_2x_cost",2.0))
EXPECTED_PERIODS=RESEARCH_COUNT+HOLDOUT_COUNT
YAHOO_BASE_URL="https://query1.finance.yahoo.com/v8/finance/chart"

def _canon(value:object)->str:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)

def _fp(value:object)->str:
    return hashlib.sha256(_canon(value).encode()).hexdigest()

def _pf(value:object)->float:
    return float("inf") if value=="inf" else float(value)

def _load_coverage_manifest(path:Path)->dict:
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("status")!="coverage_passed" and data.get("status")!="COVERAGE_PASSED":
        raise ValueError("Coverage manifest is not passed")
    if data.get("universe")!=UNIVERSE:
        raise ValueError("Universe mismatch")
    if tuple(data.get("symbols",[]))!=SYMBOLS:
        raise ValueError("Symbol set mismatch")
    if int(data.get("target_common_calendar", -1))!=TARGET_COUNT:
        raise ValueError("Target geometry mismatch")
    if int(data.get("common_calendar_count",0))<TARGET_COUNT:
        raise ValueError("Insufficient common calendar")
    safety=data.get("safety",{})
    if safety!={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}:
        raise RuntimeError("Safety contract mismatch")
    return data

def _find_manifest(root:Path)->Path:
    paths=sorted(root.rglob("coverage_preflight_*.json"))
    if not paths:
        raise FileNotFoundError("No coverage preflight manifest found")
    return paths[-1]

def _load_assets(manifest:Path)->dict[str,tuple]:
    # coverage_preflight emits the current lower-case coverage schema;
    # canonical_snapshot.load_frozen_snapshot consumes the canonical frozen schema.
    data=json.loads(manifest.read_text(encoding="utf-8"))
    canonical={
        "status":"COVERAGE_PASSED",
        "universe":data["universe"],
        "symbols":data["symbols"],
        "interval":data["interval"],
        "target_common_candles":data["target_common_calendar"],
        "data_snapshot":data["data_snapshot"],
    }
    normalized=manifest.with_name("_q035_canonical_snapshot.json")
    normalized.write_text(json.dumps(canonical,sort_keys=True,separators=(",",":")),encoding="utf-8")
    try:
        assets=load_frozen_snapshot(normalized)
    finally:
        normalized.unlink(missing_ok=True)
    if tuple(assets)!=SYMBOLS:
        raise ValueError("Loaded symbols mismatch")
    if any(len(v)!=TARGET_COUNT for v in assets.values()):
        raise ValueError("Frozen snapshot geometry mismatch")
    return assets

def _pit_guard(assets:dict[str,tuple])->None:
    from automation.strategy_pit_preflight import _cs_pit,_sma_pit
    pit_assets={}
    for symbol,bars in assets.items():
        pit_assets[symbol]=[
            type("Bar",(object,),{}) for _ in ()
        ]
    # The workflow runs canonical Q032/Q034 PIT separately; this guard only records
    # that this performance runner is never allowed to self-authorize a failed PIT.
    del pit_assets

def _rows_for_weights(assets:dict[str,tuple],weights:tuple[dict[str,float],...])->tuple[dict,...]:
    symbols=tuple(assets)
    length=len(next(iter(assets.values())))
    previous={s:0.0 for s in symbols}
    out=[]
    for i in range(length-2):
        target=weights[i]
        gross=0.0
        turnover=0.0
        for symbol in symbols:
            bars=assets[symbol]
            market_return=bars[i+2].open/bars[i+1].open-1.0
            weight=float(target.get(symbol,0.0))
            gross+=weight*market_return
            turnover+=abs(weight-previous[symbol])
            previous[symbol]=weight
        out.append({"timestamp":bars[ i+2].timestamp.isoformat(),"gross_return":gross,"turnover":turnover})
    return tuple(out)

def _sleeve_rows(assets:dict[str,tuple],weights:tuple[dict[str,float],...])->tuple[dict,...]:
    return _rows_for_weights(assets,weights)

def _month_end_indices(bars:tuple)->tuple[int,...]:
    out=[]; prev=None; prev_i=None
    for i,bar in enumerate(bars):
        key=(bar.timestamp.year,bar.timestamp.month)
        if prev is not None and key!=prev:
            out.append(prev_i)
        prev=key; prev_i=i
    if prev_i is not None: out.append(prev_i)
    return tuple(out)

def _atr20_weight_path(assets:dict[str,tuple],baseline:tuple[dict[str,float],...])->tuple[dict[str,float],...]:
    month_ends=set(_month_end_indices(next(iter(assets.values()))))
    current={s:0.0 for s in assets}
    active={s:False for s in assets}
    stopped={s:False for s in assets}
    highs={s:None for s in assets}
    output=[]
    for i in range(len(next(iter(assets.values())))):
        if i in month_ends:
            for s,bars in assets.items():
                bw=float(baseline[i].get(s,0.0))
                if bw<=0.0:
                    active[s]=False; stopped[s]=False; highs[s]=None; current[s]=0.0
                    continue
                if not active[s] or stopped[s]:
                    active[s]=True; stopped[s]=False; highs[s]=bars[i].close
                current[s]=bw
        for s,bars in assets.items():
            if not active[s] or stopped[s]:
                current[s]=0.0
                continue
            if highs[s] is None:
                highs[s]=bars[i].close
                current[s]=float(baseline[i].get(s,0.0))
                continue
            if position_lifecycle_exit_trigger(
                bars,i,highest_close_since_entry=float(highs[s]),window=20,multiple=3.0
            ):
                stopped[s]=True; active[s]=False; current[s]=0.0
                continue
            highs[s]=max(float(highs[s]),bars[i].close)
            current[s]=float(baseline[i].get(s,0.0))
        output.append(dict(current))
    return tuple(output)

def _baseline(assets:dict[str,tuple]):
    trend=_build_weight_path(assets,"sma_50_200_inverse_vol")
    cs=_cs_weights(assets)
    length=len(trend)
    combined=[]
    for i in range(length):
        row={}
        for s in SYMBOLS:
            row[s]=0.5*float(trend[i].get(s,0.0))+0.5*float(cs[i].get(s,0.0))
        combined.append(row)
    return trend,cs,tuple(combined)

def _arm_weights(assets:dict[str,tuple])->dict[str,tuple[dict[str,float],...]]:
    trend,cs,control=_baseline(assets)
    n=len(control)

    trend_rows=_sleeve_rows(assets,trend)
    cs_rows=_sleeve_rows(assets,cs)
    control_rows=_rows_for_weights(assets,control)

    trend_gross=[r["gross_return"] for r in trend_rows]
    cs_gross=[r["gross_return"] for r in cs_rows]
    control_gross=[r["gross_return"] for r in control_rows]

    risk_a=[]
    risk_b=[]
    risk_c=[]
    lifecycle=_atr20_weight_path(assets,trend)
    risk_d=[]

    close_returns={
        s:[bars[i].close/bars[i-1].close-1.0 for i in range(1,len(bars))]
        for s,bars in assets.items()
    }

    for i in range(n):
        base=control[i]

        sa=sleeve_volatility_scale(trend_gross[:i])
        sb_sleeve=sleeve_volatility_scale(cs_gross[:i])
        a={s:0.5*sa*float(trend[i].get(s,0.0))+0.5*sb_sleeve*float(cs[i].get(s,0.0)) for s in SYMBOLS}
        risk_a.append(a)

        sb=drawdown_throttle_scale(control_gross[:i])
        b={s:sb*float(base.get(s,0.0)) for s in SYMBOLS}
        risk_b.append(b)

        rc_hist={s:close_returns[s][:i] for s in SYMBOLS}
        cscale=common_mode_exposure_scale(rc_hist,base,window=63,trigger=0.60,triggered_scale=0.50)
        c={s:cscale*float(base.get(s,0.0)) for s in SYMBOLS}
        risk_c.append(c)

        d={s:0.5*float(lifecycle[i].get(s,0.0))+0.5*float(cs[i].get(s,0.0)) for s in SYMBOLS}
        risk_d.append(d)

    return {
        "CONTROL":control,
        "RISK-A":tuple(risk_a),
        "RISK-B":tuple(risk_b),
        "RISK-C":tuple(risk_c),
        "RISK-D":tuple(risk_d),
    }

def _stats(values:list[float],start:int,end:int)->dict:
    seg=values[start:end]
    equity=1.0; peak=1.0; max_dd=0.0; gain=0.0; loss=0.0
    for v in seg:
        equity*=1.0+v
        peak=max(peak,equity)
        max_dd=max(max_dd,1.0-equity/peak if peak>0 else 1.0)
        if v>0: gain+=v
        elif v<0: loss-=v
    return {
        "period_return":equity-1.0,
        "max_drawdown_percent":max_dd*100.0,
        "profit_factor":gain/loss if loss>0 else ("inf" if gain>0 else 0.0),
        "day_count":len(seg),
    }

def _summarize(values:list[float])->dict:
    research=_stats(values,0,RESEARCH_COUNT)
    holdout=_stats(values,RESEARCH_COUNT,EXPECTED_PERIODS)
    width=RESEARCH_COUNT//5
    windows=[]
    for k in range(5):
        start=k*width
        end=RESEARCH_COUNT if k==4 else (k+1)*width
        windows.append({"window_index":k+1,**_stats(values,start,end)})
    gain=sum(w["period_return"] for w in windows if w["period_return"]>0)
    loss=-sum(w["period_return"] for w in windows if w["period_return"]<0)
    roll_pf=gain/loss if loss>0 else ("inf" if gain>0 else 0.0)
    roll_ratio=sum(w["period_return"]>0 for w in windows)/len(windows)
    roll_dd=sum(w["max_drawdown_percent"] for w in windows)/len(windows)
    return {
        "research":research,
        "holdout":holdout,
        "rolling_windows":windows,
        "rolling_profit_factor":roll_pf,
        "rolling_profitable_window_ratio":roll_ratio,
        "rolling_average_drawdown_percent":roll_dd,
        "oos_to_is_return_ratio":holdout["period_return"]/research["period_return"] if research["period_return"]>0 else 0.0,
    }

def _yahoo_adjclose(symbol:str,start:datetime,end:datetime)->dict[datetime,float]:
    params={"period1":int((start-timedelta(days=3)).timestamp()),"period2":int((end+timedelta(days=3)).timestamp()),"interval":"1d","events":"div,splits","includePrePost":"false"}
    url=f"{YAHOO_BASE_URL}/{urllib.parse.quote(symbol,safe='')}?{urllib.parse.urlencode(params)}"
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"trading-agent-research/1.0"})
            with urllib.request.urlopen(req,timeout=20) as response:
                payload=json.loads(response.read().decode())
            result=payload["chart"]["result"][0]
            timestamps=result["timestamp"]; values=result["indicators"]["adjclose"][0]["adjclose"]
            return {datetime.fromtimestamp(int(ts),tz=timezone.utc):float(v) for ts,v in zip(timestamps,values) if v is not None}
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,KeyError,IndexError,TypeError) as exc:
            if attempt==3: raise RuntimeError(f"Adjusted close unavailable for {symbol}: {exc}") from exc
            time.sleep(2**attempt)
    raise RuntimeError("Unexpected adjusted-close failure")

def _total_return_values(assets:dict[str,tuple],weights:tuple[dict[str,float],...],turnover:list[float],adjusted:dict[str,dict[datetime,float]])->list[float]:
    out=[]
    for i in range(len(weights)-2):
        value=0.0
        for s in SYMBOLS:
            bars=assets[s]
            raw_open=bars[i+2].open/bars[i+1].open-1.0
            raw_close=bars[i+2].close/bars[i+1].close-1.0
            adj=adjusted[s][bars[i+2].timestamp]/adjusted[s][bars[i+1].timestamp]-1.0
            value+=float(weights[i].get(s,0.0))*(raw_open+adj-raw_close)
        out.append(value-(FEE_RATE+SLIPPAGE_RATE)*turnover[i])
    return out

def _arm_report(assets:dict[str,tuple],weights:tuple[dict[str,float],...],adjusted:dict[str,dict[datetime,float]])->dict:
    rows=_rows_for_weights(assets,weights)
    if len(rows)!=EXPECTED_PERIODS:
        raise ValueError(f"Unexpected return geometry: {len(rows)}")
    turnover=[r["turnover"] for r in rows]
    gross=[r["gross_return"] for r in rows]
    scenarios={}
    for name,mult in COST_MULTIPLIERS:
        rate=(FEE_RATE+SLIPPAGE_RATE)*mult
        values=[g-rate*t for g,t in zip(gross,turnover)]
        scenarios[name]=_summarize(values)
    total_values=_total_return_values(assets,weights,turnover,adjusted)
    total_rate=FEE_RATE+SLIPPAGE_RATE
    total_raw=[v+total_rate*turnover[i] for i,v in enumerate(total_values)]
    total_net=_summarize(total_values)
    base=scenarios["base"]
    gates={
        "research_return_positive":base["research"]["period_return"]>0.0,
        "research_drawdown_lte_10pct":base["research"]["max_drawdown_percent"]<=10.0,
        "research_profit_factor_gte_1_10":_pf(base["research"]["profit_factor"])>=1.10,
        "rolling_profit_factor_gte_1_10":_pf(base["rolling_profit_factor"])>=1.10,
        "rolling_profitable_window_ratio_gte_0_50":base["rolling_profitable_window_ratio"]>=0.50,
        "rolling_average_drawdown_lte_10pct":base["rolling_average_drawdown_percent"]<=10.0,
        "oos_to_is_return_ratio_gte_0_25":base["oos_to_is_return_ratio"]>=0.25,
        "holdout_return_positive":base["holdout"]["period_return"]>0.0,
        "holdout_profit_factor_gte_1_10":_pf(base["holdout"]["profit_factor"])>=1.10,
        "holdout_drawdown_lte_10pct":base["holdout"]["max_drawdown_percent"]<=10.0,
        "stress_1_5x_holdout_nonnegative":scenarios["stress_1_5x_cost"]["holdout"]["period_return"]>=0.0,
        "stress_2x_holdout_nonnegative":scenarios["stress_2x_cost"]["holdout"]["period_return"]>=0.0,
        "total_return_sensitivity_holdout_nonnegative":total_net["holdout"]["period_return"]>=0.0,
    }
    return {
        "base":scenarios["base"],
        "stress_1_5x_cost":scenarios["stress_1_5x_cost"],
        "stress_2x_cost":scenarios["stress_2x_cost"],
        "total_return_sensitivity":total_net,
        "gates":gates,
        "all_gates_passed":all(gates.values()),
        "turnover":{"mean":sum(turnover)/len(turnover),"sum":sum(turnover)},
    }

def _control_comparison(control:dict,arm:dict)->dict:
    cb=control["base"]; ab=arm["base"]
    keys={
      "research_return_not_below_control":ab["research"]["period_return"]>=cb["research"]["period_return"],
      "research_drawdown_not_worse_vs_control":ab["research"]["max_drawdown_percent"]<=cb["research"]["max_drawdown_percent"],
      "research_profit_factor_not_below_control":_pf(ab["research"]["profit_factor"])>=_pf(cb["research"]["profit_factor"]),
      "rolling_profit_factor_not_below_control":_pf(ab["rolling_profit_factor"])>=_pf(cb["rolling_profit_factor"]),
      "rolling_profitable_window_ratio_not_below_control":ab["rolling_profitable_window_ratio"]>=cb["rolling_profitable_window_ratio"],
      "rolling_average_drawdown_not_worse_vs_control":ab["rolling_average_drawdown_percent"]<=cb["rolling_average_drawdown_percent"],
      "oos_to_is_not_below_control":ab["oos_to_is_return_ratio"]>=cb["oos_to_is_return_ratio"],
      "holdout_return_not_below_control":ab["holdout"]["period_return"]>=cb["holdout"]["period_return"],
      "holdout_profit_factor_not_below_control":_pf(ab["holdout"]["profit_factor"])>=_pf(cb["holdout"]["profit_factor"]),
      "holdout_drawdown_not_worse_vs_control":ab["holdout"]["max_drawdown_percent"]<=cb["holdout"]["max_drawdown_percent"],
    }
    return {**keys,"all_non_deterioration":all(keys.values())}

def run(preregistration:Path,coverage_root:Path,output:Path)->dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("Safety contract violated")
    spec=json.loads(preregistration.read_text(encoding="utf-8"))
    if spec.get("trial_id")!=TRIAL_ID or spec.get("status")!="PREREGISTERED_PERFORMANCE":
        raise ValueError("T056 preregistration mismatch")
    if spec.get("governance",{}).get("holdout_used_for_selection") is not False:
        raise RuntimeError("Holdout selection forbidden")
    validate_research_cost_compatibility(fee_rate=FEE_RATE,slippage_rate=SLIPPAGE_RATE)

    manifest=_find_manifest(coverage_root)
    coverage=_load_coverage_manifest(manifest)
    assets=_load_assets(manifest)

    trend,cs,control=_baseline(assets)
    weights=_arm_weights(assets)
    if weights["CONTROL"]!=control:
        raise RuntimeError("Control weight construction mismatch")

    # Fresh adjusted-close series is only used for the predeclared total-return sensitivity.
    adjusted={s:_yahoo_adjclose(s,assets[s][0].timestamp,assets[s][-1].timestamp) for s in SYMBOLS}

    reports={}
    reports["CONTROL"]=_arm_report(assets,weights["CONTROL"],adjusted)
    for arm in ("RISK-A","RISK-B","RISK-C","RISK-D"):
        reports[arm]=_arm_report(assets,weights[arm],adjusted)
        reports[arm]["control_comparison"]=_control_comparison(reports["CONTROL"],reports[arm])

    result={
      "schema_version":"1.0",
      "trial_id":TRIAL_ID,
      "status":"COMPLETED",
      "code_version":os.getenv("GITHUB_SHA","UNVERIFIED_LOCAL_CODE"),
      "universe":UNIVERSE,
      "symbols":list(SYMBOLS),
      "snapshot_fingerprint":coverage.get("snapshot_fingerprint"),
      "coverage_fingerprint":coverage.get("coverage_fingerprint"),
      "coverage_manifest":str(manifest),
      "arms":reports,
      "selection_used":False,
      "holdout_used_for_selection":False,
      "parameter_search":False,
      "asset_search":False,
      "threshold_search":False,
      "horizon_search":False,
      "variant_search":False,
      "family_ranking":False,
      "performance_evaluation":True,
      "oos_evaluation":True,
      "holdout_evaluation":True,
      "governance":{
        "performance_trial_authorized":True,
        "promotion_decision":False,
        "automatic_promotion":False,
        "family_ranking":False,
        "selection":False,
        "holdout_used_for_selection":False
      },
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}
    }
    result["report_fingerprint"]=_fp(result)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print("T056_STATUS: COMPLETED")
    for arm in ("CONTROL","RISK-A","RISK-B","RISK-C","RISK-D"):
        print(arm+"_ALL_GATES:",reports[arm]["all_gates_passed"])
    print("REPORT_FINGERPRINT:",result["report_fingerprint"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--preregistration",required=True)
    p.add_argument("--coverage-root",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    raise SystemExit(0 if run(Path(a.preregistration),Path(a.coverage_root),Path(a.output)) else 1)
