"""Trial 044: fixed long-only unanimous 63/126/252 TSM signal consistency repair successor.
Research-only; no optimization, selection, promotion or orders.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from automation.candidate_validation_50_50_vol_budget import (
    _build_weight_path,_cs_weights,_return_rows,_stats,_summary,_yahoo_adjclose,load_bars
)
from config import settings
from research.asset_universes import get_universe,list_universes
from research.protocol import dataset_fingerprint
from validation.research_gates import ResearchGateConfig

TRIAL_ID="T-2026-09-25-044"
UNIVERSE="validation_2026_09_25_tsm_signal_consensus_repair"
TREND_SYMBOLS=("WMT","JNJ","PG","KO","PEP","XOM","CVX","CSCO")
CS_SYMBOLS=("MCD","V","ORCL","MRK","PFE")
PORTFOLIO_SYMBOLS=TREND_SYMBOLS+CS_SYMBOLS
REQUESTED_COUNT=3520
TARGET_COUNT=3500
RESEARCH_COUNT=2798
HOLDOUT_COUNT=700
TSM_LOOKBACKS=(63,126,252)
TREND_VOL_WINDOW=60
MAX_ASSET_WEIGHT=0.25
VOL_WINDOW=63
TARGET_VOL=0.10
FEE_RATE=0.001
SLIPPAGE_RATE=0.0005
COST_SCENARIOS=(("base",1.0),("stress_1_5x_cost",1.5),("stress_2x_cost",2.0))

def _canon(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)

def _fp(v):
    return hashlib.sha256(_canon(v).encode()).hexdigest()

def _pf(v):
    return float("inf") if v=="inf" else float(v)

def _manifest(path):
    data=json.loads(path.read_text(encoding="utf-8"))
    universe=get_universe(UNIVERSE)
    symbols=tuple(x["symbol"] for x in data.get("datasets",[]))
    if data.get("universe")!=UNIVERSE or symbols!=tuple(universe.symbols):
        raise ValueError("Manifest passt nicht zum T044-Repair-Universum.")
    if data.get("requested_candles")!=REQUESTED_COUNT or data.get("target_common_calendar")!=TARGET_COUNT:
        raise ValueError("Unerwartete T044 Coverage-Datenbasis.")
    safety=data.get("safety",{})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False or safety.get("orders_enabled") is not False:
        raise RuntimeError("Paper-only-Sicherheitsvertrag verletzt.")
    return data

def _assets(data_dir,manifest):
    out={}
    for item in manifest["datasets"]:
        s=item["symbol"]
        bars=load_bars(data_dir/s/"1d.csv",expected_count=int(item["candle_count"]))
        if len(bars)!=REQUESTED_COUNT or dataset_fingerprint(bars)!=item["fingerprint"]:
            raise ValueError(f"{s}: Dataset-Identität/Fingerprint stimmt nicht.")
        out[s]=bars
    if set(out)!=set(PORTFOLIO_SYMBOLS):
        raise ValueError("T044-Symbole fehlen.")
    common=set.intersection(*[{b.timestamp for b in bars} for bars in out.values()])
    if len(common)<TARGET_COUNT:
        raise ValueError(f"Zu wenig gemeinsame Candles im Repair-Snapshot: {len(common)}")
    selected=sorted(common)[-TARGET_COUNT:]
    return {s:tuple({b.timestamp:b for b in bars}[t] for t in selected) for s,bars in out.items()}

def _month_end_indices(bars):
    out=[]; prev=None; prev_i=None
    for i,b in enumerate(bars):
        key=(b.timestamp.year,b.timestamp.month)
        if prev is not None and key!=prev: out.append(prev_i)
        prev,prev_i=key,i
    if prev_i is not None: out.append(prev_i)
    return tuple(out)

def _tsm_long_flat_signal(closes,index):
    if index<max(TSM_LOOKBACKS): return 0
    changes=[closes[index]/closes[index-lb]-1.0 for lb in TSM_LOOKBACKS]
    return 1 if all(change>0 for change in changes) else 0

def _annualized_vol(closes,index):
    if index<TREND_VOL_WINDOW: return 0.0
    vals=[]
    for i in range(index-TREND_VOL_WINDOW+1,index+1):
        if closes[i-1]>0: vals.append(closes[i]/closes[i-1]-1.0)
    if len(vals)<TREND_VOL_WINDOW//2: return 0.0
    mean=sum(vals)/len(vals)
    return math.sqrt(sum((x-mean)**2 for x in vals)/len(vals))*math.sqrt(252.0)

def _inverse_vol_long_only_weights(signals,vols):
    active={s for s,v in signals.items() if v>0 and vols.get(s,0)>0}
    fixed={}; remaining=1.0
    while active and remaining>1e-12:
        raw={s:1.0/vols[s] for s in active}
        denom=sum(raw.values())
        if denom<=0: break
        proposals={s:raw[s]/denom*remaining for s in active}
        capped={s for s,v in proposals.items() if v>MAX_ASSET_WEIGHT}
        if not capped:
            fixed.update(proposals); remaining=0.0; break
        for s in sorted(capped):
            fixed[s]=MAX_ASSET_WEIGHT; remaining-=MAX_ASSET_WEIGHT; active.remove(s)
    return {s:fixed.get(s,0.0) for s in signals}

def _tsm_weight_path(assets):
    length=len(next(iter(assets.values())))
    month_ends=set(_month_end_indices(next(iter(assets.values()))))
    closes={s:[b.close for b in bars] for s,bars in assets.items()}
    current={s:0.0 for s in assets}; out=[]
    for i in range(length):
        if i in month_ends:
            signals={s:float(_tsm_long_flat_signal(closes[s],i)) for s in assets}
            vols={s:_annualized_vol(closes[s],i) for s in assets}
            current=_inverse_vol_long_only_weights(signals,vols)
        out.append(dict(current))
    return tuple(out)

def _portfolio_rows(trend_assets,cs_assets,trend_weights,adjusted):
    cs_weights=_cs_weights(cs_assets)
    tr=_return_rows(trend_assets,trend_weights,{s:adjusted[s] for s in trend_assets})
    cr=_return_rows(cs_assets,cs_weights,{s:adjusted[s] for s in cs_assets})
    tr={r["timestamp"]:r for r in tr}; cr={r["timestamp"]:r for r in cr}
    common=sorted(set(tr)&set(cr)); expected=RESEARCH_COUNT+HOLDOUT_COUNT
    if len(common)!=expected: raise ValueError(f"{len(common)} Returns statt {expected}.")
    return tuple({"timestamp":t,
        "gross_open":0.5*tr[t]["gross_open"]+0.5*cr[t]["gross_open"],
        "gross_close":0.5*tr[t]["gross_close"]+0.5*cr[t]["gross_close"],
        "gross_adjusted_close":0.5*tr[t]["gross_adjusted_close"]+0.5*cr[t]["gross_adjusted_close"],
        "turnover":0.5*tr[t]["turnover"]+0.5*cr[t]["turnover"]} for t in common)

def _vol(history):
    if len(history)<VOL_WINDOW: return None
    sample=history[-VOL_WINDOW:]; mean=sum(sample)/len(sample)
    return math.sqrt(sum((x-mean)**2 for x in sample)/len(sample))*math.sqrt(252.0)

def _simulate(rows,multiplier,total_return=False):
    history=[]; previous_scale=1.0; cost_rate=(FEE_RATE+SLIPPAGE_RATE)*multiplier; out=[]
    for row in rows:
        scale=1.0; rv=_vol(history)
        if rv is not None and rv>TARGET_VOL: scale=min(1.0,TARGET_VOL/rv)
        gross=row["gross_open"]+(row["gross_adjusted_close"]-row["gross_close"] if total_return else 0.0)
        turnover=scale*row["turnover"]+abs(scale-previous_scale)
        out.append({"timestamp":row["timestamp"],"net_return":scale*gross-cost_rate*turnover,"gross_return":scale*gross,"scale":scale,"realized_vol_estimate":rv})
        previous_scale=scale
        history.append(row["gross_open"]-(FEE_RATE+SLIPPAGE_RATE)*row["turnover"])
    return out

def _summarize(rows):
    research=_stats(rows,0,RESEARCH_COUNT)
    holdout=_stats(rows,RESEARCH_COUNT,RESEARCH_COUNT+HOLDOUT_COUNT)
    width=RESEARCH_COUNT//5; windows=[]; start=0
    for i in range(5):
        end=RESEARCH_COUNT if i==4 else start+width
        windows.append({"window_index":i+1,**_stats(rows,start,end)}); start=end
    return {"research":research,"holdout":holdout,"rolling_windows":windows,
            "rolling_summary":_summary(rows[:RESEARCH_COUNT],windows),
            "oos_to_is_return_ratio":holdout["period_return"]/research["period_return"] if research["period_return"]>0 else 0.0}

def _scenario(fixed_rows,challenger_rows,multiplier):
    return {"fixed_candidate":{"price_only":_summarize(_simulate(fixed_rows,multiplier))},
            "tsm_ensemble_candidate":{"price_only":_summarize(_simulate(challenger_rows,multiplier)),
                                     "total_return_sensitivity":_summarize(_simulate(challenger_rows,multiplier,True))}}

def _gates(scenarios,config):
    base=scenarios["base"]["tsm_ensemble_candidate"]["price_only"]; fixed=scenarios["base"]["fixed_candidate"]["price_only"]
    stress15=scenarios["stress_1_5x_cost"]["tsm_ensemble_candidate"]["price_only"]
    stress2=scenarios["stress_2x_cost"]["tsm_ensemble_candidate"]["price_only"]
    total=scenarios["base"]["tsm_ensemble_candidate"]["total_return_sensitivity"]; roll=base["rolling_summary"]
    absolute={
        "research_return_positive":base["research"]["period_return"]>0,
        "research_drawdown":base["research"]["max_drawdown_percent"]<=config.maximum_drawdown_percent,
        "research_profit_factor":_pf(base["research"]["profit_factor"])>=config.minimum_profit_factor,
        "rolling_profit_factor":_pf(roll["overall_profit_factor"])>=config.minimum_profit_factor,
        "rolling_profitable_window_ratio":roll["profitable_window_ratio"]>=config.minimum_profitable_window_ratio,
        "rolling_average_drawdown":roll["average_drawdown_percent"]<=config.maximum_drawdown_percent,
        "oos_to_is_return_ratio":base["oos_to_is_return_ratio"]>=config.minimum_oos_to_is_return_ratio,
        "holdout_return_positive":base["holdout"]["period_return"]>0,
        "holdout_profit_factor":_pf(base["holdout"]["profit_factor"])>=config.minimum_profit_factor,
        "holdout_drawdown":base["holdout"]["max_drawdown_percent"]<=config.maximum_drawdown_percent,
        "stress_1_5x_nonnegative":stress15["holdout"]["period_return"]>=0,
        "stress_2x_nonnegative":stress2["holdout"]["period_return"]>=0,
        "total_return_sensitivity_nonnegative":total["holdout"]["period_return"]>=0,
    }
    non_worsening={
        "research_return_not_below_fixed":base["research"]["period_return"]>=fixed["research"]["period_return"],
        "research_drawdown_not_worse_vs_fixed":base["research"]["max_drawdown_percent"]<=fixed["research"]["max_drawdown_percent"],
        "research_profit_factor_not_below_fixed":_pf(base["research"]["profit_factor"])>=_pf(fixed["research"]["profit_factor"]),
        "rolling_pf_not_below_fixed":_pf(roll["overall_profit_factor"])>=_pf(fixed["rolling_summary"]["overall_profit_factor"]),
        "rolling_profitable_ratio_not_below_fixed":roll["profitable_window_ratio"]>=fixed["rolling_summary"]["profitable_window_ratio"],
        "rolling_average_drawdown_not_worse_vs_fixed":roll["average_drawdown_percent"]<=fixed["rolling_summary"]["average_drawdown_percent"],
        "oos_to_is_not_below_fixed":base["oos_to_is_return_ratio"]>=fixed["oos_to_is_return_ratio"],
        "holdout_return_not_below_fixed":base["holdout"]["period_return"]>=fixed["holdout"]["period_return"],
        "holdout_pf_not_below_fixed":_pf(base["holdout"]["profit_factor"])>=_pf(fixed["holdout"]["profit_factor"]),
        "holdout_drawdown_not_worse_vs_fixed":base["holdout"]["max_drawdown_percent"]<=fixed["holdout"]["max_drawdown_percent"],
    }
    return {"absolute":absolute,"non_worsening_vs_fixed_candidate":non_worsening,
            "all_absolute_passed":all(absolute.values()),"all_non_worsening_passed":all(non_worsening.values()),
            "all_checks_passed":all(absolute.values()) and all(non_worsening.values())}

def run_validation(data_dir,manifest_path,output_path):
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only Sicherheitsvertrag verletzt.")
    manifest=_manifest(manifest_path)
    expected=set(PORTFOLIO_SYMBOLS)
    for universe in list_universes():
        if universe.name in {UNIVERSE, "validation_2026_09_25_tsm_signal_consensus"}:
            continue
        if expected.intersection(universe.symbols):
            raise ValueError(f"Symbol-Overlap mit bestehendem Universum: {universe.name}")
    assets=_assets(data_dir,manifest)
    adjusted={s:_yahoo_adjclose(s,bars[0].timestamp,bars[-1].timestamp) for s,bars in assets.items()}
    trend={s:assets[s] for s in TREND_SYMBOLS}; cs={s:assets[s] for s in CS_SYMBOLS}
    fixed_rows=_portfolio_rows(trend,cs,_build_weight_path(trend,"sma_50_200_inverse_vol"),adjusted)
    challenger_rows=_portfolio_rows(trend,cs,_tsm_weight_path(trend),adjusted)
    scenarios={name:_scenario(fixed_rows,challenger_rows,m) for name,m in COST_SCENARIOS}
    gates=_gates(scenarios,ResearchGateConfig())
    report={"schema_version":1,"trial_id":TRIAL_ID,"status":"COMPLETED","research_only":True,
            "candidate_status":"VALIDATED_PASS" if gates["all_checks_passed"] else "BLOCKED",
            "hypothesis":"Replace only the fixed SMA 50/200 long-only trend signal with fixed long-only unanimous TSM 63/126/252 while preserving the CS sleeve, 10% volatility budget, costs and PIT execution.",
            "source":{"universe":UNIVERSE,"trend_symbols":list(TREND_SYMBOLS),"cross_sectional_symbols":list(CS_SYMBOLS),"portfolio_symbols":list(PORTFOLIO_SYMBOLS),
                     "target_candles":TARGET_COUNT,"common_returns":len(challenger_rows),"research_count":RESEARCH_COUNT,"holdout_count":HOLDOUT_COUNT,
                     "fully_symbol_disjoint":True,"signal_variant_count":1,"repair_successor":True,"parent_trial_id":"T-2026-09-25-043","coverage_fingerprint":manifest["coverage_fingerprint"]},
            "methodology":{"baseline":"fixed 50/50 SMA 50/200 trend sleeve + 12-1 CS Top-2 + 10% volatility budget",
                           "intervention":"replace only trend signal with long-only unanimous 63/126/252 session consensus",
                           "trend_rebalance":"month-end only","trend_volatility_weighting_window":TREND_VOL_WINDOW,"trend_asset_weight_cap":MAX_ASSET_WEIGHT,
                           "risk_budget_window":VOL_WINDOW,"target_annualized_volatility":TARGET_VOL,
                           "point_in_time":"Close(t) decision -> next Open -> following Open",
                           "costs":{"fee_rate":FEE_RATE,"slippage_rate":SLIPPAGE_RATE},
                           "optimization_used":False,"selection_used":False,"holdout_used_for_selection":False,
                           "parameter_search":False,"variant_search":False,"shorting":False,"leverage_above_one":False,"orders_enabled":False},
            "scenarios":scenarios,"gate_contract":gates,
            "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False}}
    report["report_fingerprint"]=_fp(report)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--data-dir",required=True); p.add_argument("--manifest",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(); r=run_validation(Path(a.data_dir),Path(a.manifest),Path(a.output))
    print("TRIAL_044_STATUS:",r["status"]); print("TRIAL_044_CANDIDATE_STATUS:",r["candidate_status"]); print("TRIAL_044_REPORT_FINGERPRINT:",r["report_fingerprint"]); print("TRIAL_044_CHECKS:",json.dumps(r["gate_contract"],sort_keys=True))
