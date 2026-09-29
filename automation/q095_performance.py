"""Q095 fixed monthly-rebalance performance evaluation.

Network-free after upstream coverage/PIT/input-freeze. The two variants are
evaluated symmetrically under the unchanged 13-gate framework.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

from automation.q069_candidate_bank import CANDIDATES
from config import settings
from data.canonical_snapshot import load_frozen_snapshot
from execution.cost_contract import validate_research_cost_compatibility
from portfolio.q094_monthly_rebalance import MONTHLY_E1_ID, MONTHLY_E2_ID, build_monthly_targets

TRIAL_ID="T-2026-09-29-095"
COVERAGE_ID="T-2026-09-29-095-COVERAGE"
PIT_ID="T-2026-09-29-095-PIT"
INPUT_ID="T-2026-09-29-095-INPUT-FREEZE"
REQUESTED=5000
N=3500
RESEARCH=2798
HOLDOUT=700
INITIAL_CAPITAL_EUR=2000.0
FEE=0.001
SLIPPAGE=0.0005
COSTS=(("base",1.0),("stress_1_5x_cost",1.5),("stress_2x_cost",2.0))
VARIANT_TARGETS={
    "R1_MONTHLY_REBALANCED_Q091_E1": MONTHLY_E1_ID,
    "R2_MONTHLY_REBALANCED_Q091_E2": MONTHLY_E2_ID,
}
VARIANTS=tuple(VARIANT_TARGETS)
GATE_NAMES=(
"research_return_positive","research_drawdown_lte_10pct","research_profit_factor_gte_1_10",
"rolling_profit_factor_gte_1_10","rolling_profitable_window_ratio_gte_0_50",
"rolling_average_drawdown_lte_10pct","oos_to_is_return_ratio_gte_0_25",
"holdout_return_positive","holdout_profit_factor_gte_1_10","holdout_drawdown_lte_10pct",
"stress_1_5x_holdout_nonnegative","stress_2x_holdout_nonnegative",
"total_return_sensitivity_holdout_nonnegative"
)
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}


def canonical(v:object)->str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)

def fp(v:object)->str:
    return hashlib.sha256(canonical(v).encode()).hexdigest()

def load(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))

def preflight(root:Path):
    cov=load(root/"research/evidence/q095_coverage_result.json")
    pit=load(root/"research/evidence/q095_pit_result.json")
    inp=load(root/"research/evidence/q095_input_freeze_result.json")
    prereg=load(root/"research/preregistrations/q095_monthly_rebalance_independent_replication_2026_09_29.json")
    freeze=load(root/"research/evidence/q095_asset_freeze.json")
    if cov.get("trial_id")!=COVERAGE_ID or cov.get("status")!="COVERAGE_PASSED": raise RuntimeError("Q095 coverage invalid")
    if pit.get("trial_id")!=PIT_ID or pit.get("status")!="PIT_PASSED": raise RuntimeError("Q095 PIT invalid")
    if inp.get("trial_id")!=INPUT_ID or inp.get("status")!="INPUT_BUNDLE_FROZEN" or inp.get("performance_evaluation") is not False: raise RuntimeError("Q095 input freeze invalid")
    if prereg.get("trial_id")!=TRIAL_ID or prereg.get("status")!="PREREGISTERED_PERFORMANCE": raise RuntimeError("Q095 performance preregistration invalid")
    if prereg.get("governance",{}).get("performance_trial_authorized") is not True: raise RuntimeError("Q095 performance preregistration not authorized")
    if prereg.get("data_contract",{}).get("coverage_result_fingerprint")!=cov.get("result_fingerprint"): raise RuntimeError("Q095 coverage fingerprint mismatch")
    if prereg.get("data_contract",{}).get("pit_result_fingerprint")!=pit.get("result_fingerprint"): raise RuntimeError("Q095 PIT fingerprint mismatch")
    if prereg.get("data_contract",{}).get("input_bundle_fingerprint")!=inp.get("bundle_fingerprint"): raise RuntimeError("Q095 input bundle fingerprint mismatch")
    if freeze.get("symbols")!=cov.get("symbols"): raise RuntimeError("Q095 asset freeze symbol mismatch")
    assets=load_frozen_snapshot(root/"research/runs/q095_coverage"/COVERAGE_ID/"snapshot_manifest.json")
    symbols=tuple(prereg["data_contract"]["symbols"])
    if tuple(assets)!=symbols or any(len(assets[s])!=N for s in symbols): raise RuntimeError("Q095 snapshot geometry mismatch")
    validate_research_cost_compatibility(fee_rate=FEE,slippage_rate=SLIPPAGE)
    _assert_authorization(root,prereg)
    _assert_source_contract(root,prereg)
    return assets,symbols,prereg,cov,pit,inp

def _assert_authorization(root:Path,prereg:dict)->None:
    reg=load(root/"research/governance/active_research_registry.json")
    entry=next((x for x in reg.get("active_trials",[]) if x.get("code")=="095"),None)
    if entry is None or entry.get("trial_id")!=TRIAL_ID or entry.get("performance_authorization_allowed") is not True: raise RuntimeError("Q095 registry authorization missing")
    authp=root/"research/authorizations/q095_performance_2026_09_29.json"
    if not authp.exists(): raise RuntimeError("Q095 authorization missing")
    auth=load(authp)
    if auth.get("trial_id")!=TRIAL_ID or auth.get("authorized") is not True or auth.get("performance_execution_authorized") is not True or auth.get("one_shot") is not True: raise RuntimeError("Q095 authorization flags invalid")
    if auth.get("preregistration_fingerprint")!=fp(prereg): raise RuntimeError("Q095 authorization/preregistration fingerprint mismatch")
    if auth.get("input_bundle_fingerprint")!=prereg["data_contract"]["input_bundle_fingerprint"]: raise RuntimeError("Q095 authorization/input bundle mismatch")

def _assert_source_contract(root:Path,prereg:dict)->None:
    c=prereg.get("source_contract",{})
    mapping={
      "performance_runner_sha256":root/"automation/q095_performance.py",
      "monthly_overlay_sha256":root/"portfolio/q094_monthly_rebalance.py",
      "candidate_bank_sha256":root/"automation/q069_candidate_bank.py",
      "cost_contract_sha256":root/"execution/cost_contract.py",
      "settings_sha256":root/"config/settings.py",
      "input_freeze_sha256":root/"automation/q095_coverage_pit.py",
    }
    for key,path in mapping.items():
        if c.get(key)!=hashlib.sha256(path.read_bytes()).hexdigest(): raise RuntimeError("Q095 source contract mismatch: "+key)

def load_adjusted(root:Path,prereg:dict,symbols:tuple[str,...])->dict[str,dict[datetime,float]]:
    br=root/"research/runs/q095_input_bundle"/INPUT_ID
    manifest=load(br/"input_bundle_manifest.json")
    if manifest.get("bundle_fingerprint")!=prereg["data_contract"]["input_bundle_fingerprint"]: raise RuntimeError("Q095 input manifest fingerprint mismatch")
    actual=manifest["bundle_fingerprint"]
    copy=dict(manifest); copy.pop("bundle_fingerprint",None)
    if fp(copy)!=actual: raise RuntimeError("Q095 input manifest self fingerprint mismatch")
    out={}
    for item in manifest["datasets"]:
        if item["symbol"] not in symbols: raise RuntimeError("unexpected Q095 input symbol")
        vals=[]
        with (br/item["path"]).open(encoding="utf-8",newline="") as h:
            for row in csv.DictReader(h): vals.append((str(row["timestamp"]),float(row["adjusted_close"])))
        if len(vals)!=item["row_count"] or fp(vals)!=item["fingerprint"]: raise RuntimeError("Q095 adjusted-close fingerprint mismatch")
        out[item["symbol"]]={datetime.fromisoformat(ts):value for ts,value in vals}
    if set(out)!=set(symbols): raise RuntimeError("Q095 adjusted-close symbol set mismatch")
    return out

def stats(values:list[float],start:int,end:int)->dict:
    seg=values[start:end]
    eq=peak=1.0;gain=loss=0.0;positive=0;dd=0.0
    for v in seg:
        eq*=1+v;peak=max(peak,eq);dd=max(dd,1-eq/peak if eq>0 else 1)
        if v>0: gain+=v;positive+=1
        elif v<0: loss-=v
    return {"period_return":eq-1,"max_drawdown_percent":dd*100,"profit_factor":gain/loss if loss else ("inf" if gain else 0.0),"positive_day_ratio":positive/len(seg) if seg else 0.0,"day_count":len(seg)}

def summary(values:list[float])->dict:
    r=stats(values,0,RESEARCH);h=stats(values,RESEARCH,RESEARCH+HOLDOUT)
    width=RESEARCH//5; rw=[]
    for i in range(5):
        s=i*width;e=RESEARCH if i==4 else (i+1)*width;rw.append(stats(values,s,e))
    gp=sum(max(x["period_return"],0) for x in rw);lp=-sum(min(x["period_return"],0) for x in rw)
    rpf=gp/lp if lp else ("inf" if gp else 0.0)
    return {"research":r,"holdout":h,"rolling_windows":[{"window_index":i+1,**x} for i,x in enumerate(rw)],"rolling_profit_factor":rpf,"rolling_profitable_window_ratio":sum(x["period_return"]>0 for x in rw)/5.0,"rolling_average_drawdown_percent":sum(x["max_drawdown_percent"] for x in rw)/5.0,"oos_to_is_return_ratio":h["period_return"]/r["period_return"] if r["period_return"]>0 else 0.0}

def evaluate(values:list[float],sensitivity:list[float],turnover:list[float])->dict:
    costs={}
    gross=summary(values)
    for name,mult in COSTS:
        net=[v-(FEE+SLIPPAGE)*mult*t for v,t in zip(values,turnover)]
        costs[name]=summary(net)
    base=costs["base"];stress15=costs["stress_1_5x_cost"];stress2=costs["stress_2x_cost"]; sens=summary(sensitivity)
    gates={
      "research_return_positive":base["research"]["period_return"]>0,
      "research_drawdown_lte_10pct":base["research"]["max_drawdown_percent"]<=10,
      "research_profit_factor_gte_1_10":base["research"]["profit_factor"]=="inf" or base["research"]["profit_factor"]>=1.10,
      "rolling_profit_factor_gte_1_10":base["rolling_profit_factor"]=="inf" or base["rolling_profit_factor"]>=1.10,
      "rolling_profitable_window_ratio_gte_0_50":base["rolling_profitable_window_ratio"]>=0.50,
      "rolling_average_drawdown_lte_10pct":base["rolling_average_drawdown_percent"]<=10,
      "oos_to_is_return_ratio_gte_0_25":base["oos_to_is_return_ratio"]>=0.25,
      "holdout_return_positive":base["holdout"]["period_return"]>0,
      "holdout_profit_factor_gte_1_10":base["holdout"]["profit_factor"]=="inf" or base["holdout"]["profit_factor"]>=1.10,
      "holdout_drawdown_lte_10pct":base["holdout"]["max_drawdown_percent"]<=10,
      "stress_1_5x_holdout_nonnegative":stress15["holdout"]["period_return"]>=0,
      "stress_2x_holdout_nonnegative":stress2["holdout"]["period_return"]>=0,
      "total_return_sensitivity_holdout_nonnegative":sens["holdout"]["period_return"]>=0,
    }
    return {"base":base,"stress_1_5x_cost":costs["stress_1_5x_cost"],"stress_2x_cost":costs["stress_2x_cost"],"total_return_sensitivity":sens,"gates":gates,"gates_passed":sum(gates.values()),"gates_total":13,"all_gates_passed":all(gates.values())}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",type=Path,default=Path("."));ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args();root=a.repo_root
    assets,symbols,prereg,cov,pit,inp=preflight(root); adjusted=load_adjusted(root,prereg,symbols)
    monthly=build_monthly_targets(assets,symbols)
    arms={}
    for variant in VARIANTS:
        weights=monthly[VARIANT_TARGETS[variant]]
        gross=[];turn=[];sensitivity=[];prev={s:0.0 for s in symbols}
        for i in range(N-2):
            w=weights[i];t=sum(abs(float(w[s])-prev[s]) for s in symbols);turn.append(t);prev={s:float(w[s]) for s in symbols}
            gross_ret=0.0
            sens_ret=0.0
            for s in symbols:
                o=assets[s][i+2].open/assets[s][i+1].open-1
                gross_ret+=float(w[s])*o
                cur=assets[s][i+2].timestamp;prv=assets[s][i+1].timestamp
                adj_cur=adjusted[s][cur];adj_prv=adjusted[s][prv]
                close_ret=assets[s][i+2].close/assets[s][i+1].close-1
                adj_ret=adj_cur/adj_prv-1
                sens_ret+=float(w[s])*(o+adj_ret-close_ret)
            gross.append(gross_ret)
            sensitivity.append(sens_ret-(FEE+SLIPPAGE)*t)
        result=evaluate(gross,sensitivity,turn)
        result["turnover"]={"mean":sum(turn)/len(turn),"sum":sum(turn)}
        arms[variant]=result
    out={
      "schema_version":"1.0","trial_id":TRIAL_ID,"status":"COMPLETED","code_version":prereg.get("source_contract",{}).get("performance_runner_sha256"),
      "universe":prereg["data_contract"]["universe"],"symbols":list(symbols),"requested_candles":REQUESTED,"target_common_candles":N,"research_periods":RESEARCH,"holdout_periods":HOLDOUT,
      "initial_capital_eur":INITIAL_CAPITAL_EUR,"variants":list(VARIANTS),
      "coverage_prerequisite":{"trial_id":COVERAGE_ID,"result_fingerprint":cov["result_fingerprint"],"snapshot_fingerprint":cov["snapshot_fingerprint"]},
      "pit_prerequisite":{"trial_id":PIT_ID,"result_fingerprint":pit["result_fingerprint"]},
      "input_bundle_prerequisite":{"trial_id":INPUT_ID,"bundle_fingerprint":inp["bundle_fingerprint"]},
      "performance_evaluation":True,"oos_evaluation":True,"holdout_evaluation":True,
      "selection_used":False,"holdout_used_for_selection":False,"parameter_search":False,"threshold_search":False,"asset_search":False,"horizon_search":False,"variant_search":False,"family_ranking":False,
      "governance":{"performance_trial_authorized":True,"selection":False,"holdout_used_for_selection":False,"promotion_decision":False,"automatic_promotion":False},
      "safety":SAFETY,"arms":arms,"promotion":False
    }
    out["report_fingerprint"]=fp(out)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Q095 PERFORMANCE OK")
    for v,x in arms.items(): print(v,f"{x['gates_passed']}/13",x["base"]["holdout"]["period_return"])
    print("Q095_REPORT_FINGERPRINT:",out["report_fingerprint"])
    return 0

if __name__=="__main__": raise SystemExit(main())
