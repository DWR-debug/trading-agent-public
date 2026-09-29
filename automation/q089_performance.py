"""Q089 fixed-rule performance evaluation for the unchanged Q069 candidate bank using immutable inputs."""
from __future__ import annotations
import argparse, hashlib, json, os, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from automation.q069_candidate_bank import CANDIDATES, candidate_targets_at
from config import settings
from data.canonical_snapshot import load_frozen_snapshot
from execution.cost_contract import validate_research_cost_compatibility

TRIAL_ID="T-2026-09-28-089-PERFORMANCE"
COVERAGE_ID="T-2026-09-28-089-COVERAGE"
PIT_ID="T-2026-09-28-089-PIT"
REQUESTED_CANDLES=5000
N=3500; RESEARCH=2798; HOLDOUT=700
FEE=0.001; SLIPPAGE=0.0005
COSTS=(("base",1.0),("stress_1_5x_cost",1.5),("stress_2x_cost",2.0))
YAHOO="https://query1.finance.yahoo.com/v8/finance/chart"
Safety={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}

def _fp(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("utf-8")).hexdigest()

def _load(path): return json.loads(path.read_text(encoding="utf-8"))

def _preflight(root):
    coverage=_load(root/"research/evidence/q089_coverage_result.json")
    pit=_load(root/"research/evidence/q089_pit_result.json")
    freeze=_load(root/"research/evidence/q089_asset_freeze.json")
    prereg=_load(root/"research/preregistrations/q089_performance_2026_09_28.json")
    for obj,trial,status in ((coverage,COVERAGE_ID,"COVERAGE_PASSED"),(pit,PIT_ID,"PIT_PASSED")):
        if obj.get("trial_id")!=trial or obj.get("status")!=status: raise RuntimeError("Q089 preflight receipt invalid")
        if obj.get("performance_trial_authorized", False) is not False or obj.get("selection_used") is not False: raise RuntimeError("Q089 preflight receipt has forbidden state")
    if prereg.get("trial_id")!=TRIAL_ID or prereg.get("status")!="PREREGISTERED_PERFORMANCE": raise RuntimeError("Q089 performance preregistration invalid")
    if prereg.get("requested_candles") != REQUESTED_CANDLES or prereg.get("target_common_candles") != N or prereg.get("research_periods") != RESEARCH or prereg.get("holdout_periods") != HOLDOUT: raise RuntimeError("Q089 performance geometry metadata mismatch")
    if prereg.get("selection_used") is not False or prereg.get("holdout_used_for_selection") is not False: raise RuntimeError("Q089 preregistration records selection")
    if prereg.get("safety")!=Safety: raise RuntimeError("Q089 performance safety mismatch")
    symbols=tuple(freeze["symbols"])
    if tuple(prereg["symbols"])!=symbols: raise RuntimeError("Q089 asset freeze/prereg symbols mismatch")
    snap=root/"research/runs/q089_coverage"/COVERAGE_ID/"snapshot_manifest.json"
    assets=load_frozen_snapshot(snap)
    if tuple(assets)!=symbols or any(len(assets[s])!=N for s in symbols): raise RuntimeError("Q089 snapshot geometry mismatch")
    if freeze.get("snapshot_fingerprint")!=coverage.get("snapshot_fingerprint"): raise RuntimeError("Q089 snapshot fingerprint mismatch")
    if prereg.get("source_discovery_fingerprint")!=freeze.get("source_discovery_fingerprint"): raise RuntimeError("Q089 discovery fingerprint mismatch")
    if prereg.get("asset_freeze_fingerprint")!=_fp(freeze): raise RuntimeError("Q089 asset-freeze fingerprint mismatch")
    return assets,symbols,coverage,pit,freeze,prereg

def _load_adjusted_bundle(root, prereg, symbols):
    bundle_root = root / "research/runs/q089_input_bundle/T-2026-09-28-089-INPUT-FREEZE"
    manifest_path = bundle_root / "input_bundle_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("Q089 immutable adjusted-close input bundle missing")
    bundle = _load(manifest_path)
    if bundle.get("trial_id") != "T-2026-09-28-089-INPUT-FREEZE":
        raise RuntimeError("Q089 input bundle identity mismatch")
    expected_fp = prereg["data_contract"]["input_bundle_fingerprint"]
    actual_fp = bundle.get("bundle_fingerprint")
    if actual_fp != expected_fp:
        raise RuntimeError("Q089 input bundle fingerprint mismatch")
    if tuple(bundle.get("symbols", ())) != tuple(symbols):
        raise RuntimeError("Q089 input bundle symbols mismatch")

    canonical = dict(bundle)
    canonical.pop("bundle_fingerprint", None)
    if _fp(canonical) != actual_fp:
        raise RuntimeError("Q089 input bundle self-fingerprint mismatch")

    adjusted = {}
    for item in bundle["datasets"]:
        symbol = item["symbol"]
        path = bundle_root / item["path"]
        rows = []
        with path.open(encoding="utf-8", newline="") as handle:
            reader = __import__("csv").DictReader(handle)
            for row in reader:
                rows.append((str(row["timestamp"]), float(row["adjusted_close"])))
        if len(rows) != int(item["row_count"]):
            raise RuntimeError(f"{symbol}: adjusted-close row count mismatch")
        if _fp(rows) != item["fingerprint"]:
            raise RuntimeError(f"{symbol}: adjusted-close dataset fingerprint mismatch")
        adjusted[symbol] = {
            datetime.fromisoformat(timestamp): value
            for timestamp, value in rows
        }
    if set(adjusted) != set(symbols):
        raise RuntimeError("Q089 adjusted-close symbol set mismatch")
    return adjusted


def _assert_authorization(root, prereg):
    if prereg.get("governance", {}).get("performance_trial_authorized") is not True:
        raise RuntimeError("Q089 performance preregistration is not authorized")
    registry = _load(root / "research/governance/active_research_registry.json")
    entry = next((x for x in registry.get("active_trials", []) if x.get("code") == "089"), None)
    if entry is None or entry.get("trial_id") != TRIAL_ID or entry.get("performance_authorization_allowed") is not True:
        raise RuntimeError("Q089 active research registry does not authorize performance")
    auth_path = root / "research/authorizations/q089_performance_2026_09_28.json"
    if not auth_path.exists():
        raise RuntimeError("Q089 one-shot performance authorization is missing")
    authorization = _load(auth_path)
    if authorization.get("trial_id") != TRIAL_ID:
        raise RuntimeError("Q089 authorization trial identity mismatch")
    if authorization.get("preregistration_fingerprint") != _fp(prereg):
        raise RuntimeError("Q089 authorization is not bound to the exact preregistration")
    if authorization.get("input_bundle_fingerprint") != prereg["data_contract"]["input_bundle_fingerprint"]:
        raise RuntimeError("Q089 authorization input-bundle fingerprint mismatch")


def _assert_source_contract(root, prereg):
    contract = prereg.get("source_contract", {})
    expected = {
        "performance_runner_sha256": root.joinpath("automation/q089_performance.py").read_bytes(),
        "candidate_bank_sha256": root.joinpath("automation/q069_candidate_bank.py").read_bytes(),
        "cost_contract_sha256": root.joinpath("execution/cost_contract.py").read_bytes(),
        "settings_sha256": root.joinpath("config/settings.py").read_bytes(),
    }
    for key, raw in expected.items():
        digest = __import__("hashlib").sha256(raw).hexdigest()
        if contract.get(key) != digest:
            raise RuntimeError(f"Q089 source contract mismatch: {key}")

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
    _assert_authorization(root, prereg)
    _assert_source_contract(root, prereg)
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False: raise RuntimeError("runtime safety invalid")
    validate_research_cost_compatibility(fee_rate=FEE,slippage_rate=SLIPPAGE)
    weights={name:tuple(candidate_targets_at(assets,i,symbols=symbols)[name] for i in range(N)) for name in CANDIDATES}
    adjusted=_load_adjusted_bundle(root, prereg, symbols)
    arms={name:_evaluate(assets,weights[name],adjusted,symbols) for name in CANDIDATES}
    result={"schema_version":"1.0","trial_id":TRIAL_ID,"status":"COMPLETED","code_version":os.getenv("GITHUB_SHA","UNVERIFIED"),"universe":freeze["universe"],"symbols":list(symbols),"requested_candles":REQUESTED_CANDLES,"target_common_candles":N,"research_periods":RESEARCH,"holdout_periods":HOLDOUT,"initial_capital_eur":2000.0,"coverage_prerequisite":{"trial_id":COVERAGE_ID,"coverage_result_fingerprint":coverage["result_fingerprint"],"snapshot_fingerprint":coverage["snapshot_fingerprint"]},"pit_prerequisite":{"trial_id":PIT_ID,"result_fingerprint":pit["result_fingerprint"]},
        "input_bundle_prerequisite":{"trial_id":"T-2026-09-28-089-INPUT-FREEZE","bundle_fingerprint":prereg["data_contract"]["input_bundle_fingerprint"]},"asset_freeze_fingerprint":_fp(freeze),"arms":arms,"performance_evaluation":True,"oos_evaluation":True,"holdout_evaluation":True,"selection_used":False,"holdout_used_for_selection":False,"parameter_search":False,"threshold_search":False,"asset_search":False,"horizon_search":False,"variant_search":False,"family_ranking":False,"governance":{"performance_trial_authorized":True,"selection":False,"holdout_used_for_selection":False,"promotion_decision":False,"automatic_promotion":False},"safety":Safety}
    result["report_fingerprint"]=_fp(result); output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    for name,report in arms.items(): print(name,report["gates_passed"],"/13")
    print("Q089_REPORT_FINGERPRINT:",result["report_fingerprint"]); return result

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--repo-root",required=True); p.add_argument("--output",required=True); a=p.parse_args(); run(Path(a.repo_root),Path(a.output))