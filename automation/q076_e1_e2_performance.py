"""Q076 fixed-rule performance on a fully frozen input bundle."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

from automation.q067_alpha_mechanisms import (
    Q067_SLEEVES,
    RETURN_COUNT,
    apply_common_mode_throttle,
    apply_turnover_hysteresis,
    build_alpha_sleeves,
    equal_weight_ensemble,
    sleeve_period_returns,
    validate_gross_exposure_cap,
)
from config import settings
from data.canonical_snapshot import load_frozen_snapshot
from execution.cost_contract import validate_research_cost_compatibility

TRIAL_ID="T-2026-09-28-076-PERFORMANCE"
COVERAGE_ID="T-2026-09-28-076-COVERAGE"
PIT_ID="T-2026-09-28-076-PIT"
BUNDLE_ID="T-2026-09-28-076-INPUT-FREEZE"
SYMBOLS=("SPG","CCI","EQIX","ESS","ARE","WY","PLD","KIM")
RESEARCH=2798
HOLDOUT=700
FEE=0.001
SLIPPAGE=0.0005
COSTS=(("base",1.0),("stress_1_5x_cost",1.5),("stress_2x_cost",2.0))
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}


def fp(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def load_json(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_adjusted(bundle_root:Path):
    manifest=load_json(bundle_root/"input_bundle_manifest.json")
    adjusted={}
    for row in manifest["adjusted_close_datasets"]:
        values={}
        path=bundle_root/Path(row["path"]).relative_to(bundle_root) if Path(row["path"]).is_absolute() else bundle_root/Path(row["path"])
        if not path.exists():
            # The published manifest stores paths relative to repo root.
            path=Path(row["path"])
        with path.open("r",encoding="utf-8",newline="") as fh:
            reader=csv.DictReader(fh)
            if tuple(reader.fieldnames or ()) != ("timestamp","adjusted_close"):
                raise RuntimeError(f"{row['symbol']}: invalid adjusted-close schema")
            for item in reader:
                values[datetime.fromisoformat(item["timestamp"])] = float(item["adjusted_close"])
        if len(values) != int(row["row_count"]):
            raise RuntimeError(f"{row['symbol']}: adjusted-close row count mismatch")
        digest=fp([[ts.isoformat(),val] for ts,val in sorted(values.items())])
        if digest != row["fingerprint"]:
            raise RuntimeError(f"{row['symbol']}: adjusted-close fingerprint mismatch")
        adjusted[row["symbol"]]=values
    return manifest,adjusted


def stats(values,start,end):
    segment=values[start:end]
    equity=1.0
    peak=1.0
    gain=0.0
    loss=0.0
    positive=0
    max_dd=0.0
    for value in segment:
        equity*=1.0+value
        peak=max(peak,equity)
        max_dd=max(max_dd,1.0-equity/peak if equity>0 else 1.0)
        if value>0:
            gain+=value
            positive+=1
        elif value<0:
            loss-=value
    return {"period_return":equity-1.0,"max_drawdown_percent":max_dd*100.0,"profit_factor":gain/loss if loss else ("inf" if gain else 0.0),"positive_day_ratio":positive/len(segment) if segment else 0.0,"day_count":len(segment)}


def summary(values):
    research=stats(values,0,RESEARCH)
    holdout=stats(values,RESEARCH,RETURN_COUNT)
    width=RESEARCH//5
    rolling=[stats(values,i*width,RESEARCH if i==4 else (i+1)*width) for i in range(5)]
    pos=sum(max(x["period_return"],0.0) for x in rolling)
    neg=-sum(min(x["period_return"],0.0) for x in rolling)
    return {
        "research":research,
        "holdout":holdout,
        "rolling_windows":[{"window_index":i+1,**x} for i,x in enumerate(rolling)],
        "rolling_profit_factor":pos/neg if neg else ("inf" if pos else 0.0),
        "rolling_profitable_window_ratio":sum(x["period_return"]>0 for x in rolling)/5.0,
        "rolling_average_drawdown_percent":sum(x["max_drawdown_percent"] for x in rolling)/5.0,
        "oos_to_is_return_ratio":holdout["period_return"]/research["period_return"] if research["period_return"]>0 else 0.0,
    }


def rows(assets,weights):
    previous={symbol:0.0 for symbol in SYMBOLS}
    out=[]
    for i in range(RETURN_COUNT):
        gross=0.0
        turnover=0.0
        for symbol in SYMBOLS:
            bars=assets[symbol]
            holding_return=bars[i+2].open/bars[i+1].open-1.0
            weight=float(weights[i].get(symbol,0.0))
            gross+=weight*holding_return
            turnover+=abs(weight-previous[symbol])
            previous[symbol]=weight
        out.append({"timestamp":assets[SYMBOLS[0]][i+2].timestamp,"gross":gross,"turnover":turnover})
    return out


def evaluate(assets,weights,adjusted):
    base_rows=rows(assets,weights)
    gross=[r["gross"] for r in base_rows]
    turnover=[r["turnover"] for r in base_rows]
    stressed={}
    for name,multiplier in COSTS:
        stressed[name]=summary([v-(FEE+SLIPPAGE)*multiplier*t for v,t in zip(gross,turnover)])

    sensitivity=[]
    for i,r in enumerate(base_rows):
        current_ts=r["timestamp"]
        previous_ts=assets[SYMBOLS[0]][i+1].timestamp
        value=0.0
        for symbol in SYMBOLS:
            current_adj=adjusted[symbol].get(current_ts)
            previous_adj=adjusted[symbol].get(previous_ts)
            if current_adj is None or previous_adj is None:
                raise RuntimeError(f"{symbol}: frozen adjusted close missing at {current_ts}")
            bars=assets[symbol]
            open_return=bars[i+2].open/bars[i+1].open-1.0
            close_return=bars[i+2].close/bars[i+1].close-1.0
            adjusted_return=current_adj/previous_adj-1.0
            value+=float(weights[i].get(symbol,0.0))*(open_return+adjusted_return-close_return)
        sensitivity.append(value-(FEE+SLIPPAGE)*turnover[i])

    base=stressed["base"]
    sens=summary(sensitivity)
    pf=base["research"]["profit_factor"]
    rolling_pf=base["rolling_profit_factor"]
    holdout_pf=base["holdout"]["profit_factor"]
    gates={
      "research_return_positive":base["research"]["period_return"]>0.0,
      "research_drawdown_lte_10pct":base["research"]["max_drawdown_percent"]<=10.0,
      "research_profit_factor_gte_1_10":pf=="inf" or pf>=1.10,
      "rolling_profit_factor_gte_1_10":rolling_pf=="inf" or rolling_pf>=1.10,
      "rolling_profitable_window_ratio_gte_0_50":base["rolling_profitable_window_ratio"]>=0.50,
      "rolling_average_drawdown_lte_10pct":base["rolling_average_drawdown_percent"]<=10.0,
      "oos_to_is_return_ratio_gte_0_25":base["oos_to_is_return_ratio"]>=0.25,
      "holdout_return_positive":base["holdout"]["period_return"]>0.0,
      "holdout_profit_factor_gte_1_10":holdout_pf=="inf" or holdout_pf>=1.10,
      "holdout_drawdown_lte_10pct":base["holdout"]["max_drawdown_percent"]<=10.0,
      "stress_1_5x_holdout_nonnegative":stressed["stress_1_5x_cost"]["holdout"]["period_return"]>=0.0,
      "stress_2x_holdout_nonnegative":stressed["stress_2x_cost"]["holdout"]["period_return"]>=0.0,
      "total_return_sensitivity_holdout_nonnegative":sens["holdout"]["period_return"]>=0.0,
    }
    return {
      "base":base,
      "stress_1_5x_cost":stressed["stress_1_5x_cost"],
      "stress_2x_cost":stressed["stress_2x_cost"],
      "total_return_sensitivity":sens,
      "gates":gates,
      "gates_passed":sum(bool(x) for x in gates.values()),
      "gates_total":13,
      "all_gates_passed":all(gates.values()),
      "turnover":{"mean":sum(turnover)/len(turnover),"sum":sum(turnover)}
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",default=".")
    ap.add_argument("--preregistration",required=True)
    ap.add_argument("--authorization",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    root=Path(args.repo_root)
    prereg=load_json(Path(args.preregistration))
    auth=load_json(Path(args.authorization))
    if prereg["trial_id"]!=TRIAL_ID or prereg["status"]!="PREREGISTERED_PERFORMANCE":
        raise RuntimeError("Q076 preregistration mismatch")
    if auth["authorized"] is not True or auth["performance_execution_authorized"] is not True or auth["execution_scope"]!="Q076_FIXED_RULE_PERFORMANCE_ONLY":
        raise RuntimeError("Q076 authorization invalid")
    if auth["safety"]!=SAFETY:
        raise RuntimeError("Q076 authorization safety mismatch")
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("runtime safety invalid")
    validate_research_cost_compatibility(fee_rate=FEE,slippage_rate=SLIPPAGE)

    coverage=load_json(root/"research/evidence/q076_coverage_result.json")
    pit=load_json(root/"research/evidence/q076_pit_result.json")
    if coverage["trial_id"]!=COVERAGE_ID or coverage["status"]!="COVERAGE_PASSED" or coverage["performance_trial_authorized"] is not False or coverage["selection_used"] is not False:
        raise RuntimeError("Q076 coverage prerequisite invalid")
    if pit["trial_id"]!=PIT_ID or pit["status"]!="PIT_PASSED" or pit["performance_trial_authorized"] is not False or pit["selection_used"] is not False:
        raise RuntimeError("Q076 PIT prerequisite invalid")

    snap_manifest=root/"research/runs/q076_coverage"/COVERAGE_ID/"snapshot_manifest.json"
    assets=load_frozen_snapshot(snap_manifest)
    if tuple(assets)!=SYMBOLS or any(len(assets[s])!=3500 for s in SYMBOLS):
        raise RuntimeError("Q076 OHLCV snapshot geometry mismatch")
    bundle_root=root/"research/runs/q076_input_bundle"/BUNDLE_ID
    bundle,adjusted=load_adjusted(bundle_root)
    if bundle["trial_id"]!=BUNDLE_ID or bundle["performance_network_access"] is not False:
        raise RuntimeError("Q076 input bundle contract invalid")
    if auth["source_receipts"]["input_bundle_fingerprint"]!=bundle["bundle_fingerprint"]:
        raise RuntimeError("Q076 input bundle fingerprint mismatch")

    sleeves=build_alpha_sleeves(assets,symbols=SYMBOLS)
    aggregate=equal_weight_ensemble(sleeves,symbols=SYMBOLS)
    sleeve_returns=sleeve_period_returns(assets,sleeves,symbols=SYMBOLS)
    e1=apply_common_mode_throttle(aggregate,sleeve_returns,symbols=SYMBOLS)
    e2=apply_turnover_hysteresis(aggregate,symbols=SYMBOLS)
    arms={"CONTROL_6SLEEVE_ENSEMBLE":aggregate,"E1_ALPHA_COMMON_MODE_THROTTLE":e1,"E2_TURNOVER_HYSTERESIS":e2}
    for weights in arms.values():
        validate_gross_exposure_cap(weights,symbols=SYMBOLS)
    reports={name:evaluate(assets,weights,adjusted) for name,weights in arms.items()}
    result={
      "schema_version":"1.0","trial_id":TRIAL_ID,"status":"COMPLETED","universe":prereg["universe"],"symbols":list(SYMBOLS),
      "requested_candles":4000,"target_common_candles":3500,"research_periods":RESEARCH,"holdout_periods":HOLDOUT,"initial_capital_eur":2000.0,
      "coverage_prerequisite":{"trial_id":COVERAGE_ID,"result_fingerprint":coverage["result_fingerprint"],"snapshot_fingerprint":coverage["snapshot_fingerprint"]},
      "pit_prerequisite":{"trial_id":PIT_ID,"result_fingerprint":pit["result_fingerprint"]},
      "input_bundle_prerequisite":{"trial_id":BUNDLE_ID,"bundle_fingerprint":bundle["bundle_fingerprint"]},
      "arms":reports,"performance_evaluation":True,"oos_evaluation":True,"holdout_evaluation":True,
      "selection_used":False,"holdout_used_for_selection":False,"parameter_search":False,"threshold_search":False,"asset_search":False,"horizon_search":False,
      "variant_search":False,"family_ranking":False,
      "governance":{"performance_trial_authorized":True,"selection":False,"holdout_used_for_selection":False,"promotion_decision":False,"automatic_promotion":False},
      "safety":SAFETY,
    }
    result["report_fingerprint"]=fp(result)
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Q076_STATUS: COMPLETED")
    for name,report in reports.items(): print(name,f"{report['gates_passed']}/{report['gates_total']}")
    print("Q076_REPORT_FINGERPRINT:",result["report_fingerprint"])


if __name__=="__main__":
    main()
