"""Q070 point-in-time validation for the frozen Q069 candidate bank."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from automation.q069_candidate_bank import CANDIDATES, candidate_targets_at
from data.canonical_snapshot import load_frozen_snapshot

ROOT=Path(__file__).resolve().parents[1]
COVERAGE_ID="T-2026-09-28-070-COVERAGE"
PIT_ID="T-2026-09-28-070-PIT"

def _fp(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("utf-8")).hexdigest()

def _validate(root: Path):
    freeze=json.loads((ROOT/"research/evidence/q070_asset_freeze.json").read_text(encoding="utf-8"))
    if freeze.get("trial_id")!=COVERAGE_ID or freeze.get("status")!="COVERAGE_PASSED": raise ValueError("Q070 asset freeze is not a passed coverage receipt")
    symbols=tuple(freeze["symbols"])
    assets=load_frozen_snapshot(root/"snapshot_manifest.json")
    if tuple(assets)!=symbols: raise ValueError("Q070 snapshot symbol identity mismatch")
    if any(len(assets[s])!=3500 for s in symbols): raise ValueError("Q070 snapshot geometry mismatch")
    return assets,symbols,freeze

def _mutate(assets,index,mode):
    out={s:list(bars) for s,bars in assets.items()}
    for bars in out.values():
        start=index+1; stop=len(bars) if mode=="future" else index+2
        for i in range(start,stop):
            b=bars[i]
            bars[i]=type(b)(timestamp=b.timestamp,open=b.open*9.0,high=b.high*9.0,low=b.low*0.1,close=b.close*0.1,volume=b.volume*10.0)
    return {s:tuple(b) for s,b in out.items()}

def run(coverage_root: Path,result_path: Path):
    assets,symbols,freeze=_validate(coverage_root)
    checks=[]
    for index in range(757,3499,113):
        original=candidate_targets_at(assets,index,symbols=symbols)
        for mode in ("future","next"):
            mutated=_mutate(assets,index,mode)
            changed=candidate_targets_at(mutated,index,symbols=symbols)
            assert changed==original
            for name in CANDIDATES:
                weights=original[name]
                assert all(value>=0.0 for value in weights.values())
                assert sum(weights.values())<=1.0+1e-12
                assert set(s for s,w in weights.items() if w) <= set(symbols)
            checks.append({"index":index,"mode":mode,"candidate_count":len(CANDIDATES)})
    result={
        "schema_version":"1.0","trial_id":PIT_ID,"status":"PIT_PASSED",
        "coverage_trial_id":COVERAGE_ID,"symbols":list(symbols),
        "checked_decision_points":len(checks),"candidates":list(CANDIDATES),
        "future_mutation_checks_passed":True,"next_session_mutation_checks_passed":True,
        "performance_evaluation":False,"oos_evaluation":False,"holdout_evaluation":False,
        "selection_used":False,"performance_trial_authorized":False,
        "asset_freeze_fingerprint":freeze["asset_freeze_fingerprint"] if "asset_freeze_fingerprint" in freeze else _fp(freeze),
        "checks_fingerprint":_fp(checks),
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
    result["result_fingerprint"]=_fp(result)
    result_path.parent.mkdir(parents=True,exist_ok=True)
    result_path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Q070_PIT_STATUS:",result["status"])
    print("Q070_PIT_FINGERPRINT:",result["result_fingerprint"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--coverage-root",required=True); p.add_argument("--result",required=True)
    run(Path(p.parse_args().coverage_root),Path(p.parse_args().result))