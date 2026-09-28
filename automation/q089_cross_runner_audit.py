"""Cross-run audit for independent Q089 coverage executions.

This module compares immutable coverage receipts from different runners.
Different snapshot fingerprints are not treated as a failure by themselves:
the audit distinguishes selection/geometry agreement from source-data
fingerprint variance. No performance data is consumed.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

def _load(path: Path) -> dict[str, Any]:
    data=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data,dict): raise ValueError(f"not an object: {path}")
    return data

def _fp(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def compare(left_path: Path,right_path: Path)->dict[str,Any]:
    left,right=_load(left_path),_load(right_path)
    required=("trial_id","status","symbols","universe","common_calendar_count","snapshot_fingerprint")
    for name,data in (("left",left),("right",right)):
        missing=[k for k in required if k not in data]
        if missing: raise ValueError(f"{name}: missing keys {missing}")
    if left["trial_id"]!=right["trial_id"]: raise ValueError("trial identity mismatch")
    if left["status"]!="COVERAGE_PASSED" or right["status"]!="COVERAGE_PASSED": raise ValueError("both receipts must be passed")
    same_symbols=tuple(left["symbols"])==tuple(right["symbols"])
    same_universe=left["universe"]==right["universe"]
    same_calendar_count=left["common_calendar_count"]==right["common_calendar_count"]
    same_snapshot_fingerprint=left["snapshot_fingerprint"]==right["snapshot_fingerprint"]
    result={
        "schema_version":1,
        "trial_id":left["trial_id"],
        "selection_agreement":same_symbols,
        "universe_agreement":same_universe,
        "calendar_geometry_agreement":same_calendar_count,
        "snapshot_fingerprint_agreement":same_snapshot_fingerprint,
        "snapshot_fingerprint_variance":not same_snapshot_fingerprint,
        "left_snapshot_fingerprint":left["snapshot_fingerprint"],
        "right_snapshot_fingerprint":right["snapshot_fingerprint"],
        "left_symbols":left["symbols"],
        "right_symbols":right["symbols"],
        "governance":{"performance_evaluation":False,"holdout_used":False,"selection_used":False,"performance_trial_authorized":False},
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
    }
    result["structural_cross_runner_agreement"]=all((same_symbols,same_universe,same_calendar_count))
    result["fingerprint"]=_fp(result)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--left",required=True)
    p.add_argument("--right",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=compare(Path(a.left),Path(a.right))
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
