"""Q077-R1 PIT mutation validation for frozen E1/E2 mechanisms."""
from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path
from automation.q067_alpha_mechanisms import (
    E1_CORRELATION_LOOKBACK, Q067_SLEEVES, TARGET_CANDLES,
    alpha_sleeve_targets_at, apply_turnover_hysteresis, build_alpha_sleeves,
    equal_weight_ensemble, mean_pairwise_correlation, sleeve_period_returns,
    sleeve_return_history_at,
)
from data.canonical_snapshot import load_frozen_snapshot
STEP=113
MIN_HISTORY=E1_CORRELATION_LOOKBACK+210

def _fp(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def _mutate(assets,index,mode):
    out={s:list(b) for s,b in assets.items()}
    for s,bars in out.items():
        start=index+1
        stop=len(bars) if mode=="future" else index+2
        for i in range(start,stop):
            bars[i]=type(bars[i])(
                timestamp=bars[i].timestamp,open=bars[i].open*9.0,high=bars[i].high*9.0,
                low=bars[i].low*0.1,close=bars[i].close*0.1,volume=bars[i].volume)
    return {s:tuple(b) for s,b in out.items()}

def _aggregate_at(assets,index,symbols):
    sleeves=alpha_sleeve_targets_at(assets,index,symbols=symbols)
    return {s:sum(float(sleeves[name].get(s,0.0)) for name in Q067_SLEEVES)/len(Q067_SLEEVES) for s in symbols}

def run(snapshot_root:Path,symbols:list[str],result_path:Path):
    assets=load_frozen_snapshot(snapshot_root/"snapshot_manifest.json")
    expected=tuple(symbols)
    if tuple(assets)!=expected: raise ValueError("Q077R1 symbol order mismatch")
    if any(len(assets[s])!=TARGET_CANDLES for s in expected): raise ValueError("Q077R1 snapshot geometry mismatch")
    sleeves=build_alpha_sleeves(assets,symbols=expected)
    aggregate=equal_weight_ensemble(sleeves,symbols=expected)
    returns=sleeve_period_returns(assets,sleeves,symbols=expected)
    from automation.q067_alpha_mechanisms import common_mode_multipliers
    multipliers=common_mode_multipliers(returns)
    e2_path=apply_turnover_hysteresis(aggregate,symbols=expected)
    checks=[]
    for index in range(MIN_HISTORY,TARGET_CANDLES-1,STEP):
        original_target=aggregate[index]
        original_prev=aggregate[index-1]
        original_e2=e2_path[index]
        for mode in ("future","next"):
            mutated=_mutate(assets,index,mode)
            mutated_target=_aggregate_at(mutated,index,expected)
            mutated_prev=_aggregate_at(mutated,index-1,expected)
            mutated_e2=apply_turnover_hysteresis((e2_path[index-1],mutated_target),symbols=expected)[1]
            assert original_target==mutated_target
            assert original_prev==mutated_prev
            assert original_e2==mutated_e2
            assert sleeve_return_history_at(assets,index,symbols=expected)==sleeve_return_history_at(mutated,index,symbols=expected)
            assert abs(mean_pairwise_correlation(sleeve_return_history_at(assets,index,symbols=expected))-mean_pairwise_correlation(sleeve_return_history_at(mutated,index,symbols=expected)))<1e-15
            assert multipliers[index] in (1.0,0.5)
            checks.append({"index":index,"mode":mode,"e1_multiplier":multipliers[index]})
    result={"schema_version":"1.0","trial_id":"T-2026-09-28-077R1-PIT","status":"PIT_PASSED",
            "coverage_trial_id":"Q-2026-09-28-077R1-DISCOVERY","symbols":symbols,
            "checked_decision_points":len(checks),"mechanisms":["E1_ALPHA_COMMON_MODE_THROTTLE","E2_TURNOVER_HYSTERESIS"],
            "future_mutation_checks_passed":True,"next_session_mutation_checks_passed":True,
            "performance_evaluation":False,"oos_evaluation":False,"holdout_evaluation":False,
            "selection_used":False,"performance_trial_authorized":False,
            "checks_fingerprint":_fp(checks),
            "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
    result["result_fingerprint"]=_fp(result)
    result_path.parent.mkdir(parents=True,exist_ok=True)
    result_path.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print("Q077R1_PIT_STATUS",result["status"])
    print("Q077R1_PIT_FP",result["result_fingerprint"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--snapshot-root",required=True); p.add_argument("--symbols-json",required=True); p.add_argument("--result",required=True)
    a=p.parse_args(); run(Path(a.snapshot_root),json.loads(Path(a.symbols_json).read_text(encoding="utf-8")),Path(a.result))
