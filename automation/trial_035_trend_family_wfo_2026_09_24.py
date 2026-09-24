"""Trial 035: fixed trend-family walk-forward control on a new multi-asset universe.

Research-only. Exactly three already-tested strategy families are selected using
training profit factor in five rolling windows. The selected family is frozen for
the following OOS block; the family from the final Research window is frozen for
the blind 700-day Holdout. No parameter search and no production promotion.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

from automation.cross_asset_trend_replication import (
    BASE_FEE, BASE_SLIPPAGE, COST_SCENARIOS, _build_weight_path, _daily_returns
)
from automation.literature_strategy_lab import dataset_fingerprint, load_bars
from config import settings
from research.asset_universes import get_universe, list_universes

TRIAL_ID="T-2026-09-24-035"
UNIVERSE="validation_2026_09_24_trend_family_wfo_candidate"
TARGET_COUNT=3500
RESEARCH_COUNT=2798
HOLDOUT_COUNT=700
TRAIN_SIZE=1398
TEST_SIZE=280
STEP_SIZE=280
FAMILIES=("tsm_monthly_equal","sma_50_200_inverse_vol","blend_tsm_sma_inverse_vol")
REFERENCE="buy_and_hold_equal"

def _canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)
def _fp(v): return hashlib.sha256(_canon(v).encode()).hexdigest()

def _stats(returns,start,end):
    seg=returns[max(0,start):min(end,len(returns))]
    if not seg: return {"period_return":0.0,"max_drawdown_percent":0.0,"profit_factor":0.0,"day_count":0}
    equity=peak=1.0; dd=gp=gl=0.0
    for x in seg:
        equity*=1+x; peak=max(peak,equity); dd=max(dd,1-equity/peak)
        if x>0: gp+=x
        elif x<0: gl-=x
    pf=gp/gl if gl>0 else ("inf" if gp>0 else 0.0)
    return {"period_return":equity-1.0,"max_drawdown_percent":dd*100.0,"profit_factor":pf,"day_count":len(seg)}

def _pf(v): return float("inf") if v=="inf" else float(v)

def _manifest(path):
    m=json.loads(path.read_text(encoding="utf-8"))
    u=get_universe(UNIVERSE)
    syms=tuple(x["symbol"] for x in m.get("datasets",[]))
    if m.get("universe")!=UNIVERSE or syms!=tuple(u.symbols): raise ValueError("Manifest mismatch.")
    if m.get("target_count")!=TARGET_COUNT: raise ValueError("Unexpected target count.")
    if m.get("source")!="yahoo_chart": raise ValueError("Unexpected source.")
    safety=m.get("safety",{})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False or safety.get("orders_enabled") is not False:
        raise RuntimeError("Paper-only contract violated.")
    return m

def _assets(data_dir,manifest):
    out={}
    for item in manifest["datasets"]:
        s=item["symbol"]
        bars=load_bars(data_dir/s/"1d.csv",expected_count=int(item["candle_count"]))
        if len(bars)!=TARGET_COUNT: raise ValueError(f"{s}: wrong count")
        if dataset_fingerprint(bars)!=item["fingerprint"]: raise ValueError(f"{s}: fingerprint mismatch")
        out[s]=bars
    common=set.intersection(*[{b.timestamp for b in bars} for bars in out.values()])
    if len(common)<TARGET_COUNT: raise ValueError(f"Common calendar only {len(common)}")
    sel=sorted(common)[-TARGET_COUNT:]
    return {s:tuple({b.timestamp:b for b in bars}[t] for t in sel) for s,bars in out.items()}

def _select(training):
    scored=[]
    for family,returns in training.items():
        st=_stats(returns,0,len(returns))
        scored.append({"family":family,"profit_factor":_pf(st["profit_factor"]),"period_return":st["period_return"],"max_drawdown_percent":st["max_drawdown_percent"]})
    selected=sorted(scored,key=lambda x:(-x["profit_factor"],-x["period_return"],x["max_drawdown_percent"],x["family"]))[0]
    return {"selected_family":selected["family"],"candidates":scored,
            "rule":"highest training profit factor; tie-break higher training return; tie-break lower training drawdown; final lexicographic family name"}

def _windows():
    return tuple((i + 1, i * STEP_SIZE, i * STEP_SIZE + TRAIN_SIZE, i * STEP_SIZE + TRAIN_SIZE + TEST_SIZE) for i in range(5))

def run_validation(data_dir,manifest_path,output_path):
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False: raise RuntimeError("Paper-only contract violated.")
    m=_manifest(manifest_path)
    expected=set(get_universe(UNIVERSE).symbols)
    for u in list_universes():
        if u.name!=UNIVERSE and expected.intersection(u.symbols): raise ValueError(f"Symbol overlap: {u.name}")
    assets=_assets(data_dir,m)
    streams_base={}; streams_stress={}
    for family in (REFERENCE,*FAMILIES):
        w=_build_weight_path(assets,family)
        streams_base[family]=_daily_returns(assets,w,1.0)
        streams_stress[family]=_daily_returns(assets,w,2.0)

    selections=[]; oos_base=[]; oos_stress=[]
    for idx,train_start,train_end,test_end in _windows():
        training={f:streams_base[f][train_start:train_end] for f in FAMILIES}
        sel=_select(training); fam=sel["selected_family"]
        base_test=_stats(streams_base[fam],train_end,test_end)
        stress_test=_stats(streams_stress[fam],train_end,test_end)
        selections.append({"window_index":idx,"train_start":train_start,"train_end":train_end,"test_end":test_end,
                           "selected_family":fam,"selection":sel,"base_oos":base_test,"stress_oos":stress_test})
        oos_base.extend(streams_base[fam][train_end:test_end])
        oos_stress.extend(streams_stress[fam][train_end:test_end])

    final_family=selections[-1]["selected_family"]
    holdout_base=_stats(streams_base[final_family],RESEARCH_COUNT,TARGET_COUNT)
    holdout_stress=_stats(streams_stress[final_family],RESEARCH_COUNT,TARGET_COUNT)
    ref_holdout=_stats(streams_base[REFERENCE],RESEARCH_COUNT,TARGET_COUNT)
    ref_research=_stats(streams_base[REFERENCE],0,RESEARCH_COUNT)

    oos_stats={
        "base":_stats(oos_base,0,len(oos_base)),
        "stress_2x_cost":_stats(oos_stress,0,len(oos_stress)),
        "positive_window_count":sum(x["base_oos"]["period_return"]>0 for x in selections),
        "window_count":len(selections),
        "positive_window_ratio":sum(x["base_oos"]["period_return"]>0 for x in selections)/len(selections),
    }

    holdout_checks={
        "return_positive":holdout_base["period_return"]>0,
        "profit_factor":_pf(holdout_base["profit_factor"])>=1.10,
        "drawdown":holdout_base["max_drawdown_percent"]<=10.0,
        "stress_2x_nonnegative":holdout_stress["period_return"]>=0.0,
    }
    oos_checks={
        "return_positive":oos_stats["base"]["period_return"]>0,
        "profit_factor":_pf(oos_stats["base"]["profit_factor"])>=1.10,
        "positive_window_ratio":oos_stats["positive_window_ratio"]>=0.50,
    }
    gate_contract={"oos":oos_checks,"holdout":holdout_checks,
                   "all_checks_passed":all(oos_checks.values()) and all(holdout_checks.values())}

    counts={}
    for x in selections: counts[x["selected_family"]]=counts.get(x["selected_family"],0)+1

    report={
      "schema_version":1,"trial_id":TRIAL_ID,"status":"COMPLETED","research_only":True,
      "candidate_status":"PASSED_CONTROL" if gate_contract["all_checks_passed"] else "BLOCKED",
      "hypothesis":"A fixed family-level WFO selector among three already-tested trend families transfers OOS and remains positive in the blind Holdout on a new multi-asset universe.",
      "source":{"universe":UNIVERSE,"symbols":list(assets),"target_candles":TARGET_COUNT,"research_count":RESEARCH_COUNT,"holdout_count":HOLDOUT_COUNT,
                "fully_symbol_disjoint":True,"coverage_preflight_common_calendar_count":3520,"manifest_fingerprint":m["manifest_fingerprint"]},
      "methodology":{"families":list(FAMILIES),"reference":REFERENCE,"train_size":TRAIN_SIZE,"test_size":TEST_SIZE,"step_size":STEP_SIZE,"research_windows":5,
                     "selection_rule":"training-only PF, then training return, then training DD, then family-name tiebreak",
                     "holdout_rule":"freeze family selected in final Research WFO window",
                     "holdout_used_for_selection":False,"parameter_search":False,"variant_search":False,"selection_profile_used":False,
                     "base_fee":BASE_FEE,"base_slippage":BASE_SLIPPAGE,"stress_multiplier":2.0,
                     "execution":"close_t_decision_then_next_open_execution_and_following_open_return","orders_enabled":False},
      "selection":{"per_window":selections,"selection_counts":counts,"final_holdout_family":final_family},
      "oos":oos_stats,"holdout":{"selected_family":final_family,"base":holdout_base,"stress_2x_cost":holdout_stress},
      "reference":{"research":ref_research,"holdout":ref_holdout},
      "gate_contract":gate_contract,
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False}
    }
    report["report_fingerprint"]=_fp(report)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--data-dir",required=True); p.add_argument("--manifest",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(); r=run_validation(Path(a.data_dir),Path(a.manifest),Path(a.output))
    print("TRIAL_035_STATUS:",r["status"]); print("TRIAL_035_CANDIDATE_STATUS:",r["candidate_status"]); print("TRIAL_035_REPORT_FINGERPRINT:",r["report_fingerprint"]); print("TRIAL_035_CHECKS:",json.dumps(r["gate_contract"],sort_keys=True))
