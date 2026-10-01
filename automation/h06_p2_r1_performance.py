"""H06-P2-R1 corrective one-shot performance evaluation.\n\nThis correction preserves the frozen H06-P2 scientific scope and changes only execution-boundary normalization: the canonical coverage receipt status schema and ISO timestamp representation are normalized deterministically before evaluation. No data, PIT, signal, cost, portfolio, horizon, threshold, or selection rule changes.
No network data acquisition occurs inside the runner. Market OHLCV inputs are supplied
from the already frozen H06 coverage artifact; adjusted-close inputs come from the
immutable H06-P2 input bundle committed to the repository.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os
from datetime import datetime
from pathlib import Path

from automation.h06_p2_signal import (
    LOOKBACK, SKIP, TOP_K, WEIGHT, SYMBOLS, build_arms, gross_exposure, net_exposure,
)
from config import settings
from execution.cost_contract import validate_research_cost_compatibility
from research.protocol import dataset_fingerprint
from automation.literature_strategy_lab import load_bars

TRIAL_ID = "T-2026-10-01-H06P2R1-PERFORMANCE-01"
PIT_TRIAL_ID = "H06-REPAIR-2026-09-25"
INPUT_ID = "T-2026-10-01-H06P2-INPUT-FREEZE"
N = 3500
RESEARCH = 2798
HOLDOUT = 700
EVALUATION_PERIODS = 3498
FEE = 0.001
SLIPPAGE = 0.0005
COSTS = (("base", 1.0), ("stress_1_5x_cost", 1.5), ("stress_2x_cost", 2.0))
SAFETY = {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False}
ARM_IDS = ("H06-P2-RESIDUAL-GLOBAL-T5/B5", "H06-P2-RAW-GLOBAL-T5/B5")
GATES = (
    "research_return_positive", "research_drawdown_lte_10pct",
    "research_profit_factor_gte_1_10", "rolling_profit_factor_gte_1_10",
    "rolling_profitable_window_ratio_gte_0_50", "rolling_average_drawdown_lte_10pct",
    "oos_to_is_return_ratio_gte_0_25", "holdout_return_positive",
    "holdout_profit_factor_gte_1_10", "holdout_drawdown_lte_10pct",
    "stress_1_5x_holdout_nonnegative", "stress_2x_holdout_nonnegative",
    "total_return_sensitivity_holdout_nonnegative",
)

def _fp(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()

def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _load_market_snapshot(root: Path, coverage: dict) -> dict[str, list[dict]]:
    data_dir = root / "h06_repair_datasets"
    manifest = coverage
    coverage_status = manifest.get("status") or manifest.get("coverage", {}).get("status")
    if coverage_status not in {"COVERAGE_PASSED", "COVERAGE_READY"}:
        raise RuntimeError("H06-P2-R1 market coverage is not ready")
    if manifest.get("fingerprint") != "cd130e0cccf264680bf306ec58d162ddbd09f4b00b96613039f056b80c609936":
        raise RuntimeError("H06 coverage fingerprint mismatch")
    if manifest.get("snapshot_fingerprint") != "e80e63eebbc94a32043dcf9c38aa86d2f7dc88eb7c2a172de24dfd9b269e55c6":
        raise RuntimeError("H06 snapshot fingerprint mismatch")
    expected = {x["symbol"]: x for x in manifest["data_snapshot"]["datasets"]}
    if tuple(manifest["symbols"]) != tuple(SYMBOLS) or set(expected) != set(SYMBOLS):
        raise RuntimeError("H06 universe mismatch")
    assets = {}
    for symbol in SYMBOLS:
        path = data_dir / symbol / "1d.csv"
        if not path.is_file():
            raise RuntimeError(f"missing market dataset: {symbol}")
        bars = load_bars(path, expected_count=N)
        if dataset_fingerprint(bars) != expected[symbol]["fingerprint"]:
            raise RuntimeError(f"{symbol}: market dataset fingerprint mismatch")
        assets[symbol] = bars
    timestamps = [bar.timestamp for bar in assets[SYMBOLS[0]]]
    if any([bar.timestamp for bar in assets[s]] != timestamps for s in SYMBOLS[1:]):
        raise RuntimeError("H06 market timestamps are not aligned")
    return assets

def _timestamp_key(value):
    """Canonical ISO timestamp key for datetime and frozen CSV representations."""
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    return value.isoformat()

def _load_adjusted_bundle(root: Path, prereg: dict):
    bundle_root = root / "research/runs/h06_p2_input_bundle" / INPUT_ID
    manifest = _load(bundle_root / "input_bundle_manifest.json")
    if manifest.get("trial_id") != INPUT_ID:
        raise RuntimeError("H06 input bundle identity mismatch")
    if manifest.get("bundle_fingerprint") != prereg["input_contract"]["input_bundle_fingerprint"]:
        raise RuntimeError("H06 input bundle fingerprint mismatch")
    canonical = dict(manifest); actual = canonical.pop("bundle_fingerprint", None)
    if _fp(canonical) != actual:
        raise RuntimeError("H06 input bundle self-fingerprint mismatch")
    adjusted={}
    for item in manifest["datasets"]:
        symbol=item["symbol"]
        rows=[]
        with (bundle_root / item["path"]).open(newline="",encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows.append((str(row["timestamp"]), float(row["adjusted_close"])))
        if len(rows) != int(item["row_count"]):
            raise RuntimeError(f"{symbol}: adjusted-close row count mismatch")
        if _fp(rows) != item["fingerprint"]:
            raise RuntimeError(f"{symbol}: adjusted-close fingerprint mismatch")
        adjusted[symbol] = {_timestamp_key(ts): val for ts, val in rows}
    if set(adjusted) != set(SYMBOLS):
        raise RuntimeError("H06 adjusted-close symbol set mismatch")
    return adjusted

def _preflight(root: Path):
    prereg=_load(root/"research/preregistrations/h06_p2_r1_performance_2026_10_01.json")
    pit=_load(root/"research/evidence/h06_pit_independent_reproduction_2026_10_01.json")
    freeze=_load(root/"research/evidence/h06_p2_input_freeze_result.json")
    auth=_load(root/"research/authorizations/h06_p2_r1_performance_2026_10_01.json")
    registry=_load(root/"research/governance/active_research_registry.json")
    if prereg.get("trial_id") != TRIAL_ID or prereg.get("status") != "PREREGISTERED_PERFORMANCE":
        raise RuntimeError("H06-P2 preregistration is not authorized")
    if prereg.get("input_contract",{}).get("input_bundle_fingerprint") != freeze.get("bundle_fingerprint"):
        raise RuntimeError("H06-P2 frozen bundle fingerprint mismatch")
    if pit.get("trial_id") != PIT_TRIAL_ID or pit.get("status") != "PIT_REPRODUCED_RECONCILED":
        raise RuntimeError("H06 PIT prerequisite invalid")
    if pit.get("reconciliation",{}).get("check_fingerprint") != prereg["input_contract"]["pit_check_fingerprint"]:
        raise RuntimeError("H06 PIT semantic-check fingerprint mismatch")
    if pit.get("data_contract",{}).get("coverage_fingerprint") != prereg["input_contract"]["coverage_fingerprint"]:
        raise RuntimeError("H06 PIT coverage fingerprint mismatch")
    if pit.get("data_contract",{}).get("snapshot_fingerprint") != prereg["input_contract"]["snapshot_fingerprint"]:
        raise RuntimeError("H06 PIT snapshot fingerprint mismatch")
    if auth.get("authorized") is not True or auth.get("performance_execution_authorized") is not True or auth.get("one_shot") is not True:
        raise RuntimeError("H06 one-shot authorization invalid")
    if auth.get("trial_id") != TRIAL_ID or auth.get("preregistration_fingerprint") != _fp(prereg):
        raise RuntimeError("H06 authorization/preregistration fingerprint mismatch")
    if auth.get("input_bundle_fingerprint") != prereg["input_contract"]["input_bundle_fingerprint"]:
        raise RuntimeError("H06 authorization/input bundle mismatch")
    active=next((x for x in registry.get("active_trials",[]) if x.get("code")=="H06-P2-R1"),None)
    if not active or active.get("trial_id") != TRIAL_ID or active.get("state") != "PERFORMANCE_AUTHORIZED" or active.get("performance_authorization_allowed") is not True:
        raise RuntimeError("H06 active registry does not authorize exact trial")
    for key in ("selection","holdout_used_for_selection","parameter_search","threshold_search","asset_search","horizon_search","variant_search","family_ranking","promotion_decision","automatic_promotion"):
        if prereg.get("governance",{}).get(key) is not False:
            raise RuntimeError(f"H06 forbidden governance state: {key}")
    if prereg.get("governance",{}).get("performance_trial_authorized") is not True:
        raise RuntimeError("H06 performance authorization flag missing")
    if prereg.get("safety") != SAFETY:
        raise RuntimeError("H06 prereg safety mismatch")
    if auth.get("safety") != SAFETY:
        raise RuntimeError("H06 authorization safety mismatch")
    return prereg, pit, freeze, auth, registry

def _weights(assets):
    closes={s:[bar.close for bar in assets[s]] for s in SYMBOLS}
    out={arm_id:[] for arm_id in ARM_IDS}
    for i in range(N):
        if i < LOOKBACK:
            for arm_id in ARM_IDS: out[arm_id].append({s:0.0 for s in SYMBOLS})
            continue
        arms=build_arms(closes,i)
        for arm_id in ARM_IDS:
            w=dict(arms[arm_id]["weights"])
            if gross_exposure(w) != 1.0 or net_exposure(w) != 0.0:
                raise RuntimeError(f"H06 exposure invariant failed: {arm_id} at {i}")
            if sum(v == WEIGHT for v in w.values()) != TOP_K or sum(v == -WEIGHT for v in w.values()) != TOP_K:
                raise RuntimeError(f"H06 position-count invariant failed: {arm_id} at {i}")
            out[arm_id].append(w)
    return out

def _rows(assets, weights):
    previous={s:0.0 for s in SYMBOLS}; rows=[]
    for i in range(EVALUATION_PERIODS):
        gross=0.0; turnover=0.0
        for s in SYMBOLS:
            bars=assets[s]
            gross += float(weights[i].get(s,0.0)) * (bars[i+2].open / bars[i+1].open - 1.0)
            turnover += abs(float(weights[i].get(s,0.0)) - previous[s])
            previous[s]=float(weights[i].get(s,0.0))
        rows.append({"timestamp":assets[SYMBOLS[0]][i+2].timestamp,"gross":gross,"turnover":turnover})
    return rows

def _stats(values,start,end):
    segment=values[start:end]; equity=1.0; peak=1.0; gain=0.0; loss=0.0; positive=0; dd=0.0
    for value in segment:
        equity *= 1.0 + value
        peak=max(peak,equity)
        dd=max(dd,1.0-equity/peak if equity>0 else 1.0)
        if value>0: gain+=value; positive+=1
        elif value<0: loss-=value
    return {"period_return":equity-1.0,"max_drawdown_percent":dd*100.0,"profit_factor":gain/loss if loss else ("inf" if gain else 0.0),"positive_period_ratio":positive/len(segment) if segment else 0.0,"day_count":len(segment)}

def _summary(values):
    research=_stats(values,0,RESEARCH); holdout=_stats(values,RESEARCH,RESEARCH+HOLDOUT); width=RESEARCH//5
    rolling=[_stats(values,i*width,RESEARCH if i==4 else (i+1)*width) for i in range(5)]
    pos=sum(max(x["period_return"],0.0) for x in rolling); neg=-sum(min(x["period_return"],0.0) for x in rolling)
    rpf=pos/neg if neg else ("inf" if pos else 0.0)
    return {"research":research,"holdout":holdout,"rolling_windows":[{"window_index":i+1,**x} for i,x in enumerate(rolling)],"rolling_profit_factor":rpf,"rolling_profitable_window_ratio":sum(x["period_return"]>0 for x in rolling)/5.0,"rolling_average_drawdown_percent":sum(x["max_drawdown_percent"] for x in rolling)/5.0,"oos_to_is_return_ratio":holdout["period_return"]/research["period_return"] if research["period_return"]>0 else 0.0}

def _evaluate(assets,weights,adjusted,arm_id):
    rows=_rows(assets,weights[arm_id]); gross=[x["gross"] for x in rows]; turnover=[x["turnover"] for x in rows]
    scenarios={}
    for name,mult in COSTS:
        scenarios[name]=_summary([v-(FEE+SLIPPAGE)*mult*t for v,t in zip(gross,turnover)])
    sensitivity=[]
    for i,row in enumerate(rows):
        current=row["timestamp"]; previous=assets[SYMBOLS[0]][i+1].timestamp; value=0.0
        for s in SYMBOLS:
            ca=adjusted[s].get(_timestamp_key(current)); pa=adjusted[s].get(_timestamp_key(previous))
            if ca is None or pa is None: raise RuntimeError(f"{s}: adjusted close missing at {current}")
            b=assets[s]
            open_ret=b[i+2].open/b[i+1].open-1.0
            close_ret=b[i+2].close/b[i+1].close-1.0
            adj_ret=ca/pa-1.0
            value += float(weights[arm_id][i].get(s,0.0))*(open_ret+adj_ret-close_ret)
        sensitivity.append(value-(FEE+SLIPPAGE)*turnover[i])
    sens=_summary(sensitivity); base=scenarios["base"]; s15=scenarios["stress_1_5x_cost"]; s2=scenarios["stress_2x_cost"]
    rp=base["research"]["profit_factor"]; hp=base["holdout"]["profit_factor"]; rpf=base["rolling_profit_factor"]
    gates={
        "research_return_positive":base["research"]["period_return"]>0.0,
        "research_drawdown_lte_10pct":base["research"]["max_drawdown_percent"]<=10.0,
        "research_profit_factor_gte_1_10":rp=="inf" or rp>=1.10,
        "rolling_profit_factor_gte_1_10":rpf=="inf" or rpf>=1.10,
        "rolling_profitable_window_ratio_gte_0_50":base["rolling_profitable_window_ratio"]>=0.50,
        "rolling_average_drawdown_lte_10pct":base["rolling_average_drawdown_percent"]<=10.0,
        "oos_to_is_return_ratio_gte_0_25":base["oos_to_is_return_ratio"]>=0.25,
        "holdout_return_positive":base["holdout"]["period_return"]>0.0,
        "holdout_profit_factor_gte_1_10":hp=="inf" or hp>=1.10,
        "holdout_drawdown_lte_10pct":base["holdout"]["max_drawdown_percent"]<=10.0,
        "stress_1_5x_holdout_nonnegative":s15["holdout"]["period_return"]>=0.0,
        "stress_2x_holdout_nonnegative":s2["holdout"]["period_return"]>=0.0,
        "total_return_sensitivity_holdout_nonnegative":sens["holdout"]["period_return"]>=0.0,
    }
    if tuple(gates)!=GATES: raise RuntimeError("H06 gate definition drift")
    return {"base":base,"stress_1_5x_cost":s15,"stress_2x_cost":s2,"total_return_sensitivity":sens,"gates":gates,"gates_passed":sum(bool(v) for v in gates.values()),"gates_total":13,"all_gates_passed":all(gates.values()),"turnover":{"mean":sum(turnover)/len(turnover),"sum":sum(turnover)}}

def _control_relative(treatment,control):
    def delta(path):
        a=treatment; b=control
        for key in path: a=a[key]; b=b[key]
        return a-b
    return {
        "research_return_delta_percentage_points":100.0*delta(("base","research","period_return")),
        "research_drawdown_delta_percentage_points":delta(("base","research","max_drawdown_percent")),
        "research_profit_factor_delta":delta(("base","research","profit_factor")),
        "holdout_return_delta_percentage_points":100.0*delta(("base","holdout","period_return")),
        "holdout_drawdown_delta_percentage_points":delta(("base","holdout","max_drawdown_percent")),
        "holdout_profit_factor_delta":delta(("base","holdout","profit_factor")),
    }

def run(root:Path, market_root:Path, output:Path)->dict:
    prereg,pit,freeze,auth,registry=_preflight(root)
    validate_research_cost_compatibility(fee_rate=FEE,slippage_rate=SLIPPAGE)
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("H06 runtime safety invariants invalid")
    coverage_path=market_root/"h06_sector_neutral_residual_momentum_repair_coverage.json"
    coverage=_load(coverage_path)
    assets=_load_market_snapshot(market_root,coverage)
    adjusted=_load_adjusted_bundle(root,prereg)
    weights=_weights(assets)
    arms={arm_id:_evaluate(assets,weights,adjusted,arm_id) for arm_id in ARM_IDS}
    treatment=arms["H06-P2-RESIDUAL-GLOBAL-T5/B5"]; control=arms["H06-P2-RAW-GLOBAL-T5/B5"]
    result={
        "schema_version":"1.0","trial_id":TRIAL_ID,"status":"COMPLETED","code_version":os.getenv("GITHUB_SHA","UNVERIFIED"),
        "research_family":"h06_p2_sector_residual_global_rank","universe":freeze["universe"],"symbols":list(SYMBOLS),
        "requested_candles":4000,"target_common_candles":N,"evaluation_return_periods":EVALUATION_PERIODS,
        "research_periods":RESEARCH,"holdout_periods":HOLDOUT,"initial_capital_eur":2000.0,
        "corrective_basis":{"prior_trial_id":"T-2026-10-01-H06P2-PERFORMANCE-01","execution_incident_path":"research/evidence/h06_p2_performance_execution_incident.json","correction_type":"execution_boundary_normalization_only","coverage_status_schema_normalization":true,"timestamp_representation_normalization":true,"scientific_scope_changed":false},
        "coverage_prerequisite":{"trial_id":PIT_TRIAL_ID,"coverage_result_fingerprint":prereg["input_contract"]["coverage_fingerprint"],"snapshot_fingerprint":prereg["input_contract"]["snapshot_fingerprint"]},
        "pit_prerequisite":{"trial_id":PIT_TRIAL_ID,"check_fingerprint":prereg["input_contract"]["pit_check_fingerprint"]},
        "input_bundle_prerequisite":{"trial_id":INPUT_ID,"bundle_fingerprint":freeze["bundle_fingerprint"]},
        "upstream_market_artifact":prereg["input_contract"]["upstream_market_artifact"],
        "arms":arms,
        "control_relative_diagnostics":_control_relative(treatment,control),
        "performance_evaluation":True,"oos_evaluation":True,"holdout_evaluation":True,
        "selection_used":False,"holdout_used_for_selection":False,"parameter_search":False,"threshold_search":False,
        "asset_search":False,"horizon_search":False,"variant_search":False,"sector_map_search":False,"family_ranking":False,
        "governance":{"performance_trial_authorized":True,"selection":False,"holdout_used_for_selection":False,"promotion_decision":False,"automatic_promotion":False},
        "safety":SAFETY
    }
    result["report_fingerprint"]=_fp(result)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    for arm_id,report in arms.items(): print(f"{arm_id} {report['gates_passed']}/{report['gates_total']}")
    print("H06P2_REPORT_FINGERPRINT="+result["report_fingerprint"])
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo-root",type=Path,default=Path(".")); p.add_argument("--market-root",type=Path,required=True); p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(); run(a.repo_root.resolve(),a.market_root.resolve(),a.output if a.output.is_absolute() else a.repo_root.resolve()/a.output)

if __name__=="__main__": raise SystemExit(main())
