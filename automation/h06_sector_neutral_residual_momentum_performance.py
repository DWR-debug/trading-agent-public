"""Fixed-rule H06 sector-neutral residual momentum performance trial.

One strategy only:
252-session return with 21-session skip, sector de-mean, top-2 long-only,
21-session rebalance, 1.0 gross exposure. No search or variant evaluation.
"""
from __future__ import annotations

import argparse, hashlib, json, os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from backtesting.models import Candle
from config import settings
from data.market_store import MarketDataStore
from automation.candidate_validation_50_50_vol_budget import _yahoo_adjclose

TRIAL_ID="T-2026-09-27-049-PERFORMANCE"
UNIVERSE="validation_2026_09_26_h06_mechanism_replication"
ASSETS=("MU","ADBE","CRM","ABT","BMY","BAX","PH","ROK","DOV","CPB","SJM","CAG","EXC","SRE","CMS")
SECTOR_MAP={
 "technology":("MU","ADBE","CRM"),
 "healthcare":("ABT","BMY","BAX"),
 "industrials":("PH","ROK","DOV"),
 "consumer_staples":("CPB","SJM","CAG"),
 "utilities":("EXC","SRE","CMS"),
}
TARGET=3500
RESEARCH=2798
HOLDOUT=700
LOOKBACK=252
SKIP=21
REBALANCE=21
TOP_N=2
FEE_RATE=0.001
SLIPPAGE_RATE=0.0005
ONE_WAY_COST=FEE_RATE+SLIPPAGE_RATE
ROUND_TRIP_COST=2.0*ONE_WAY_COST

EXPECTED_COVERAGE_RUN=36230165868
EXPECTED_COVERAGE_ARTIFACT=10901872543
EXPECTED_COVERAGE_FINGERPRINT="7726c5428f5c3d23e9ec009b488b8de301f65c024e518fc889928f1b99588a7b"
EXPECTED_COVERAGE_ARTIFACT_DIGEST="sha256:c08212e6a247e8cb9c8dd891c6549d35191155ed3ac04db8ae15e480bf049ce6"
EXPECTED_SNAPSHOT_FINGERPRINT="22a32d2c6785b4f04f935148d3bd3e6978af8eb49e3a32d46073ee3f0cb93522"
EXPECTED_MECHANISM_FINGERPRINT="45546b7a2b69c39f961cab85f9ab091d165f5e9a711777fb23dd717f82fc9fbd"


def _fp(value: object)->str:
    s=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)
    return hashlib.sha256(s.encode()).hexdigest()


def _load(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_assets(data_dir:Path, coverage:dict)->dict[str,list[Candle]]:
    store=MarketDataStore(data_dir)
    out={}
    expected=tuple(x["symbol"] for x in coverage["data_snapshot"]["datasets"])
    if set(expected) != set(ASSETS) or len(expected) != len(ASSETS):
        raise RuntimeError("Coverage symbol set mismatch.")
    for item in coverage["data_snapshot"]["datasets"]:
        symbol=item["symbol"]
        bars=store.load(symbol,"1d")
        if len(bars)!=TARGET:
            raise RuntimeError(f"{symbol}: expected {TARGET} candles, got {len(bars)}")
        out[symbol]=bars
    common=set(c.timestamp for c in out[ASSETS[0]])
    for symbol in ASSETS[1:]:
        common &= {c.timestamp for c in out[symbol]}
    timestamps=sorted(common)[-TARGET:]
    if len(timestamps)!=TARGET:
        raise RuntimeError("Common timestamp intersection is shorter than target.")
    for symbol in ASSETS:
        by_ts={c.timestamp:c for c in out[symbol]}
        out[symbol]=[by_ts[t] for t in timestamps]
    return out


def _weights(assets:dict[str,list[Candle]],i:int)->dict[str,float]:
    if i < LOOKBACK+SKIP:
        return {s:0.0 for s in ASSETS}
    anchor=i-SKIP
    origin=anchor-LOOKBACK
    raw={
      s:assets[s][anchor].close/assets[s][origin].close-1.0
      for s in ASSETS
    }
    residual={}
    for members in SECTOR_MAP.values():
        mean=sum(raw[s] for s in members)/len(members)
        for s in members:
            residual[s]=raw[s]-mean
    ranking=sorted(ASSETS,key=lambda s:(residual[s],s),reverse=True)
    winners=ranking[:TOP_N]
    return {s:(1.0/TOP_N if s in winners else 0.0) for s in ASSETS}


def _simulate(assets:dict[str,list[Candle]],cost_multiplier:float):
    previous={s:0.0 for s in ASSETS}
    current={s:0.0 for s in ASSETS}
    rows=[]
    weight_rows=[]
    for i in range(TARGET-2):
        if i % REBALANCE == 0:
            current=_weights(assets,i)
        gross=0.0
        turnover=0.0
        for s in ASSETS:
            w=current[s]
            bars=assets[s]
            gross += w*(bars[i+2].open/bars[i+1].open-1.0)
            turnover += abs(w-previous[s])
            previous[s]=w
        net=gross-ONE_WAY_COST*cost_multiplier*turnover
        rows.append({"timestamp":assets[ASSETS[0]][i+2].timestamp.isoformat(),"net_return":net,"gross_return":gross,"turnover":turnover})
        weight_rows.append(dict(current))
    return rows,weight_rows,{"trade_sessions":sum(r["turnover"]>0 for r in rows),"turnover":sum(r["turnover"] for r in rows)}


def _stats(rows:list[dict]) -> dict:
    equity=1.0; peak=1.0; dd=0.0; gp=0.0; gl=0.0
    vals=[r["net_return"] for r in rows]
    for v in vals:
        equity*=1+v
        peak=max(peak,equity)
        dd=max(dd,1-equity/peak)
        if v>0: gp+=v
        elif v<0: gl-=v
    return {
      "period_return":equity-1.0,
      "max_drawdown_percent":dd*100.0,
      "profit_factor":gp/gl if gl else "inf",
      "count":len(vals),
    }


def _rolling(rows:list[dict])->dict:
    width=RESEARCH//5
    windows=[]
    start=0
    for n in range(5):
        end=RESEARCH if n==4 else start+width
        windows.append(_stats(rows[start:end]))
        start=end
    return {
      "windows":windows,
      "profitable_window_ratio":sum(w["period_return"]>0 for w in windows)/5.0,
      "overall_profit_factor":_stats(rows[:RESEARCH])["profit_factor"],
      "average_drawdown_percent":sum(w["max_drawdown_percent"] for w in windows)/5.0,
    }


def _adjusted_holdout(rows,weights,assets,adjusted,cost_multiplier):
    vals=[]
    for idx,row in enumerate(rows):
        if idx<RESEARCH:
            continue
        day=assets[ASSETS[0]][idx+2].timestamp
        prev=assets[ASSETS[0]][idx+1].timestamp
        correction=0.0
        for s in ASSETS:
            adj_r=adjusted[s][day]/adjusted[s][prev]-1.0
            close_r=assets[s][idx+2].close/assets[s][idx+1].close-1.0
            correction += weights[idx][s]*(adj_r-close_r)
        vals.append(row["net_return"]+correction)
    return _stats([{"net_return":v} for v in vals])


def _gates(base, stress15, stress2, total_sens):
    r=base["research"]; h=base["holdout"]; roll=base["rolling"]
    def pf(v): return float("inf") if v=="inf" else float(v)
    oos=h["period_return"]/r["period_return"] if r["period_return"]>0 else 0.0
    checks={
      "research_return_positive":r["period_return"]>0,
      "research_max_drawdown_lte_10pct":r["max_drawdown_percent"]<=10,
      "research_profit_factor_gte_1_1":pf(r["profit_factor"])>=1.1,
      "rolling_profit_factor_gte_1_1":pf(roll["overall_profit_factor"])>=1.1,
      "rolling_profitable_window_ratio_gte_0_5":roll["profitable_window_ratio"]>=0.5,
      "rolling_average_drawdown_lte_10pct":roll["average_drawdown_percent"]<=10,
      "oos_to_is_return_ratio_gte_0_25":oos>=0.25,
      "holdout_return_positive":h["period_return"]>0,
      "holdout_profit_factor_gte_1_1":pf(h["profit_factor"])>=1.1,
      "holdout_max_drawdown_lte_10pct":h["max_drawdown_percent"]<=10,
      "stress_1_5x_holdout_nonnegative":stress15["period_return"]>=0,
      "stress_2x_holdout_nonnegative":stress2["period_return"]>=0,
      "total_return_sensitivity_holdout_nonnegative":total_sens["period_return"]>=0,
    }
    return {"absolute":checks,"all_absolute_passed":all(checks.values()),"oos_to_is_return_ratio":oos}


def run(manifest_path:Path,data_dir:Path,authorization_path:Path,mechanism_result_path:Path,output_path:Path)->dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    auth=_load(authorization_path)
    if auth.get("trial_id")!=TRIAL_ID or auth.get("performance_execution_authorized") is not True or auth.get("execution_scope")!="PERFORMANCE":
        raise RuntimeError("H06 performance authorization missing.")
    if auth.get("coverage_workflow_run_id")!=EXPECTED_COVERAGE_RUN or auth.get("coverage_artifact_id")!=EXPECTED_COVERAGE_ARTIFACT:
        raise RuntimeError("H06 authorization is not bound to exact coverage artifact.")
    if auth.get("coverage_fingerprint")!=EXPECTED_COVERAGE_FINGERPRINT or auth.get("coverage_artifact_sha256")!=EXPECTED_COVERAGE_ARTIFACT_DIGEST:
        raise RuntimeError("H06 coverage provenance mismatch.")
    if auth.get("snapshot_fingerprint")!=EXPECTED_SNAPSHOT_FINGERPRINT:
        raise RuntimeError("H06 snapshot fingerprint mismatch.")
    mech=_load(mechanism_result_path)
    if mech.get("result_fingerprint") != EXPECTED_MECHANISM_FINGERPRINT:
        # Mechanism artifact contains its fingerprint under top-level metadata in this family.
        if mech.get("fingerprint") != EXPECTED_MECHANISM_FINGERPRINT:
            raise RuntimeError("H06 mechanism-result provenance mismatch.")
    coverage=_load(manifest_path)
    if coverage.get("universe")!=UNIVERSE or coverage.get("target_common_calendar")!=TARGET:
        raise RuntimeError("H06 coverage manifest mismatch.")
    if coverage.get("fingerprint")!=EXPECTED_COVERAGE_FINGERPRINT:
        raise RuntimeError("H06 coverage fingerprint mismatch.")
    assets=_load_assets(data_dir,coverage)

    # Deterministic dataset snapshot fingerprint from the frozen coverage record.
    dataset_manifest={
      "format":coverage["data_snapshot"]["format"],
      "datasets":sorted(
        [{"symbol":x["symbol"],"interval":x["interval"],"candle_count":x["candle_count"],"fingerprint":x["fingerprint"]}
         for x in coverage["data_snapshot"]["datasets"]],key=lambda x:x["symbol"])
    }
    if _fp(dataset_manifest)!=EXPECTED_SNAPSHOT_FINGERPRINT:
        raise RuntimeError("H06 dataset snapshot fingerprint mismatch.")

    scenarios={}
    adjusted={}
    start=assets[ASSETS[0]][0].timestamp
    end=assets[ASSETS[0]][-1].timestamp
    with ThreadPoolExecutor(max_workers=len(ASSETS)) as pool:
        fs={pool.submit(_yahoo_adjclose,s,start,end):s for s in ASSETS}
        for f in as_completed(fs): adjusted[fs[f]]=f.result()

    for name,mult in (("base",1.0),("stress_1_5x",1.5),("stress_2x",2.0)):
        rows,weights,execution=_simulate(assets,mult)
        scenarios[name]={"research":_stats(rows[:RESEARCH]),"holdout":_stats(rows[RESEARCH:RESEARCH+HOLDOUT]),"rolling":_rolling(rows),"execution":execution}
        scenarios[name]["total_return_sensitivity_holdout"]=_adjusted_holdout(rows,weights,assets,adjusted,mult)

    gates=_gates(scenarios["base"],scenarios["stress_1_5x"],scenarios["stress_2x"],scenarios["base"]["total_return_sensitivity_holdout"])
    result={
      "schema_version":"1.0",
      "trial_id":TRIAL_ID,
      "status":"ALL_GATES_PASSED" if gates["all_absolute_passed"] else "NO_PROMOTION_EVIDENCE",
      "candidate_status":"VALIDATED_PASS" if gates["all_absolute_passed"] else "BLOCKED",
      "research_family":"sector_neutral_residual_momentum",
      "hypothesis":"252/21 cross-sectional momentum residualized by equal-weight sector mean supports top-2 long-only 21-day rebalancing.",
      "source":{"universe":UNIVERSE,"symbols":list(ASSETS),"sector_map":{k:list(v) for k,v in SECTOR_MAP.items()},"target_candles":TARGET,"research_periods":RESEARCH,"holdout_periods":HOLDOUT,"coverage_workflow_run_id":EXPECTED_COVERAGE_RUN,"coverage_artifact_id":EXPECTED_COVERAGE_ARTIFACT,"coverage_fingerprint":EXPECTED_COVERAGE_FINGERPRINT,"coverage_artifact_digest":EXPECTED_COVERAGE_ARTIFACT_DIGEST,"snapshot_fingerprint":EXPECTED_SNAPSHOT_FINGERPRINT,"mechanism_result_fingerprint":EXPECTED_MECHANISM_FINGERPRINT},
      "methodology":{"formation_lookback_sessions":LOOKBACK,"skip_sessions":SKIP,"rebalance_sessions":REBALANCE,"top_n":TOP_N,"residualization":"equal_weight_sector_demean","long_only":True,"gross_exposure":1.0,"leverage":1.0,"base_round_trip_cost":ROUND_TRIP_COST,"cost_multipliers":[1.0,1.5,2.0],"optimization_used":False,"asset_search":False,"threshold_search":False,"horizon_search":False,"feature_search":False,"variant_search":False,"holdout_used_for_selection":False},
      "scenarios":scenarios,
      "gates":gates,
      "selection":{"parameter_search":False,"threshold_search":False,"asset_search":False,"horizon_search":False,"feature_search":False,"variant_search":False,"holdout_used_for_selection":False},
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}
    }
    result["result_fingerprint"]=_fp(result)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\\n",encoding="utf-8")
    print("H06_STATUS:",result["status"])
    print("H06_RESEARCH_RETURN:",result["scenarios"]["base"]["research"]["period_return"])
    print("H06_RESEARCH_DD:",result["scenarios"]["base"]["research"]["max_drawdown_percent"])
    print("H06_RESEARCH_PF:",result["scenarios"]["base"]["research"]["profit_factor"])
    print("H06_HOLDOUT_RETURN:",result["scenarios"]["base"]["holdout"]["period_return"])
    print("H06_HOLDOUT_DD:",result["scenarios"]["base"]["holdout"]["max_drawdown_percent"])
    print("H06_HOLDOUT_PF:",result["scenarios"]["base"]["holdout"]["profit_factor"])
    print("H06_ROLLING_RATIO:",result["scenarios"]["base"]["rolling"]["profitable_window_ratio"])
    print("H06_RESULT_FINGERPRINT:",result["result_fingerprint"])
    return result


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--data-dir",type=Path,required=True)
    p.add_argument("--authorization",type=Path,required=True)
    p.add_argument("--mechanism-result",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    run(a.manifest,a.data_dir,a.authorization,a.mechanism_result,a.output)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
