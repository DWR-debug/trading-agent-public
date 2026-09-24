"""Trial 031: fixed risk-adjusted 12-1 cross-sectional momentum.

Research-only. Replace only the CS ranking score:
12-1 raw return -> 12-1 raw return divided by formation-period realized volatility.
Everything else stays fixed.
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

TRIAL_ID="T-2026-09-24-031"
UNIVERSE="validation_2026_09_24_risk_adjusted_momentum_candidate"
TREND_SYMBOLS=("EIS","EPU","ECH","EWS","EWM","EZA","TUR","THD")
CS_SYMBOLS=("VDC","VCR","VOX","IAT","XTN")
PORTFOLIO_SYMBOLS=TREND_SYMBOLS+CS_SYMBOLS
TARGET_COUNT=3500
RESEARCH_COUNT=2798
HOLDOUT_COUNT=700
CS_LOOKBACK=252
CS_SKIP=21
CS_REBALANCE=21
CS_TOP_N=2
VOL_WINDOW=63
TARGET_VOL=0.10
FORMATION_VOL_LOOKBACK=252
FEE_RATE=0.001
SLIPPAGE_RATE=0.0005
COST_SCENARIOS=(("base",1.0),("stress_1_5x_cost",1.5),("stress_2x_cost",2.0))

def _canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)
def _fp(v): return hashlib.sha256(_canon(v).encode()).hexdigest()
def _pf(v): return float("inf") if v=="inf" else float(v)

def _manifest(path:Path):
    data=json.loads(path.read_text(encoding="utf-8"))
    u=get_universe(UNIVERSE)
    actual=tuple(x["symbol"] for x in data.get("datasets",[]))
    if data.get("universe")!=UNIVERSE or actual!=tuple(u.symbols): raise ValueError("Manifest passt nicht zu Trial 031.")
    if data.get("target_count")!=TARGET_COUNT or data.get("source")!="yahoo_chart": raise ValueError("Unerwartete Trial-031-Datenbasis.")
    safety=data.get("safety",{})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False or safety.get("orders_enabled") is not False:
        raise RuntimeError("Paper-only Sicherheitsvertrag verletzt.")
    return data

def _assets(data_dir:Path,manifest):
    out={}
    for item in manifest["datasets"]:
        s=item["symbol"]
        bars=load_bars(data_dir/s/"1d.csv",expected_count=int(item["candle_count"]))
        if len(bars)!=TARGET_COUNT or dataset_fingerprint(bars)!=item["fingerprint"]:
            raise ValueError(f"{s}: Dataset-Identität/Fingerprint stimmt nicht.")
        out[s]=bars
    if set(out)!=set(PORTFOLIO_SYMBOLS): raise ValueError("Trial-031-Symbole fehlen.")
    common=set.intersection(*[{b.timestamp for b in bars} for bars in out.values()])
    if len(common)<TARGET_COUNT: raise ValueError(f"Zu wenig gemeinsamer Kalender: {len(common)}")
    selected=sorted(common)[-TARGET_COUNT:]
    return {s:tuple({b.timestamp:b for b in bars}[t] for t in selected) for s,bars in out.items()}

def _risk_adjusted_cs_weights(assets):
    n=min(len(v) for v in assets.values())
    current={s:0.0 for s in assets}
    out=[]
    selection_log=[]
    for i in range(n):
        if i % CS_REBALANCE == 0:
            if i < CS_LOOKBACK + CS_SKIP:
                current={s:0.0 for s in assets}
                selected=()
            else:
                anchor=i-CS_SKIP
                origin=anchor-CS_LOOKBACK
                scores={}
                for s,bars in assets.items():
                    cumulative=bars[anchor].close/bars[origin].close-1.0
                    daily=[]
                    for j in range(origin+1,anchor+1):
                        prev=bars[j-1].close
                        cur=bars[j].close
                        if prev<=0: raise ValueError(f"{s}: nonpositive close in formation window")
                        daily.append(cur/prev-1.0)
                    mean=sum(daily)/len(daily)
                    variance=sum((x-mean)**2 for x in daily)/len(daily)
                    realized_vol=math.sqrt(variance)
                    if realized_vol<=1e-12:
                        score=math.inf if cumulative>0 else (-math.inf if cumulative<0 else 0.0)
                    else:
                        score=cumulative/realized_vol
                    scores[s]=(score,cumulative,realized_vol)
                winners=tuple(sorted(assets,key=lambda s:scores[s][0],reverse=True)[:CS_TOP_N])
                current={s:(1.0/CS_TOP_N if s in winners else 0.0) for s in assets}
                selected=winners
                selection_log.append({"index":i,"timestamp":bars[anchor].timestamp.isoformat(),"selected":list(winners)})
        out.append(dict(current))
    return tuple(out),tuple(selection_log)

def _portfolio_rows(trend_assets,cs_assets,trend_weights,cs_weights,adjusted):
    trend_rows=_return_rows(trend_assets,trend_weights,{s:adjusted[s] for s in trend_assets})
    cs_rows=_return_rows(cs_assets,cs_weights,{s:adjusted[s] for s in cs_assets})
    tr={r["timestamp"]:r for r in trend_rows}; cr={r["timestamp"]:r for r in cs_rows}
    common=sorted(set(tr)&set(cr))
    expected=RESEARCH_COUNT+HOLDOUT_COUNT
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
    research=_stats(rows,0,RESEARCH_COUNT); holdout=_stats(rows,RESEARCH_COUNT,RESEARCH_COUNT+HOLDOUT_COUNT)
    width=RESEARCH_COUNT//5; windows=[]; start=0
    for i in range(5):
        end=RESEARCH_COUNT if i==4 else start+width
        windows.append({"window_index":i+1,**_stats(rows,start,end)}); start=end
    return {"research":research,"holdout":holdout,"rolling_windows":windows,
            "rolling_summary":_summary(rows[:RESEARCH_COUNT],windows),
            "oos_to_is_return_ratio":holdout["period_return"]/research["period_return"] if research["period_return"]>0 else 0.0}

def _scenario(fixed_rows,challenger_rows,multiplier):
    return {"fixed_candidate":{"price_only":_summarize(_simulate(fixed_rows,multiplier))},
            "risk_adjusted_candidate":{"price_only":_summarize(_simulate(challenger_rows,multiplier)),
                                      "total_return_sensitivity":_summarize(_simulate(challenger_rows,multiplier,True))}}

def _gates(scenarios,config):
    base=scenarios["base"]["risk_adjusted_candidate"]["price_only"]; fixed=scenarios["base"]["fixed_candidate"]["price_only"]
    s15=scenarios["stress_1_5x_cost"]["risk_adjusted_candidate"]["price_only"]; s2=scenarios["stress_2x_cost"]["risk_adjusted_candidate"]["price_only"]
    total=scenarios["base"]["risk_adjusted_candidate"]["total_return_sensitivity"]; roll=base["rolling_summary"]
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
        "stress_1_5x_nonnegative":s15["holdout"]["period_return"]>=0,
        "stress_2x_nonnegative":s2["holdout"]["period_return"]>=0,
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
    for u in list_universes():
        if u.name!=UNIVERSE and expected.intersection(u.symbols): raise ValueError(f"Symbol overlap: {u.name}")
    assets=_assets(data_dir,manifest)
    adjusted={s:_yahoo_adjclose(s,b[0].timestamp,b[-1].timestamp) for s,b in assets.items()}
    trend={s:assets[s] for s in TREND_SYMBOLS}; cs={s:assets[s] for s in CS_SYMBOLS}
    fixed_cs=_cs_weights(cs)
    risk_cs,selection_log=_risk_adjusted_cs_weights(cs)
    fixed_rows=_portfolio_rows(trend,cs,_build_weight_path(trend,"sma_50_200_inverse_vol"),fixed_cs,adjusted)
    challenger_rows=_portfolio_rows(trend,cs,_build_weight_path(trend,"sma_50_200_inverse_vol"),risk_cs,adjusted)
    scenarios={name:_scenario(fixed_rows,challenger_rows,m) for name,m in COST_SCENARIOS}
    gates=_gates(scenarios,ResearchGateConfig())
    report={"schema_version":1,"trial_id":TRIAL_ID,"status":"COMPLETED","research_only":True,
            "candidate_status":"VALIDATED_PASS" if gates["all_checks_passed"] else "BLOCKED",
            "hypothesis":"Replace only the 12-1 cross-sectional raw-return ranking with a fixed 12-1 return divided by formation-period realized volatility ranking.",
            "source":{"universe":UNIVERSE,"trend_symbols":list(TREND_SYMBOLS),"cross_sectional_symbols":list(CS_SYMBOLS),
                     "portfolio_symbols":list(PORTFOLIO_SYMBOLS),"target_candles":TARGET_COUNT,"common_returns":len(challenger_rows),
                     "research_count":RESEARCH_COUNT,"holdout_count":HOLDOUT_COUNT,"fully_symbol_disjoint":True,
                     "signal_variant_count":1,"manifest_fingerprint":manifest["manifest_fingerprint"]},
            "methodology":{"baseline":"fixed 50/50 SMA 50/200 inverse-volatility trend + 12-1 raw-return CS Top-2 + aggregate 63-session/10% budget",
                           "intervention":"CS score = 252-session cumulative return divided by daily realized volatility over the same 252-session formation window ending 21 sessions before rebalance",
                           "cs_rebalance":CS_REBALANCE,"cs_lookback":CS_LOOKBACK,"cs_skip":CS_SKIP,"cs_top_n":CS_TOP_N,
                           "formation_vol_window":FORMATION_VOL_LOOKBACK,"risk_budget_window":VOL_WINDOW,"target_annualized_volatility":TARGET_VOL,
                           "selection_scope":"Top-2 only; long-only equal weight","point_in_time":"Close(t) decision -> next Open -> following Open",
                           "costs":{"fee_rate":FEE_RATE,"slippage_rate":SLIPPAGE_RATE},
                           "cost_scenarios":[name for name,_ in COST_SCENARIOS],"optimization_used":False,"selection_used":False,
                           "holdout_used_for_selection":False,"parameter_search":False,"threshold_search":False,"variant_search":False,
                           "shorting":False,"leverage_above_one":False,"orders_enabled":False},
            "selection_diagnostics":{"rebalance_selection_count":len(selection_log),"selection_log_tail":list(selection_log[-10:])},
            "scenarios":scenarios,"gate_contract":gates,
            "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False}}
    report["report_fingerprint"]=_fp(report)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--data-dir",required=True); p.add_argument("--manifest",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(); r=run_validation(Path(a.data_dir),Path(a.manifest),Path(a.output))
    print("TRIAL_031_STATUS:",r["status"]); print("TRIAL_031_CANDIDATE_STATUS:",r["candidate_status"]); print("TRIAL_031_REPORT_FINGERPRINT:",r["report_fingerprint"]); print("TRIAL_031_CHECKS:",json.dumps(r["gate_contract"],sort_keys=True))
