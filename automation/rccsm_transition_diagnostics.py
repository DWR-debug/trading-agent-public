"""RCCSM state-velocity and mechanism-conflict diagnostics.

Diagnostic-only: no future labels, P&L, holdout outcomes, optimization, or
performance ranking. The module compares two adjacent lagged state observations
and the frozen-Q069 mechanism disagreement at the later decision point.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any, Mapping, Sequence

from automation.q069_candidate_bank import CANDIDATES
from automation.rccsm_disagreement import disagreement_at
from automation.rccsm_state import state_at
from data.canonical_snapshot import load_frozen_snapshot

ROOT=Path(__file__).resolve().parents[1]
STATE_COMPONENTS=("trend_coherence","breadth","dispersion_percentile","shock_density")


def _fp(value: object)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def state_velocity(previous: Mapping[str,Any], current: Mapping[str,Any])->float:
    """Mean absolute movement across the four frozen state descriptors."""
    values=[]
    for key in STATE_COMPONENTS:
        if key not in previous or key not in current:
            raise ValueError(f"missing state component: {key}")
        values.append(abs(float(current[key])-float(previous[key])))
    return sum(values)/len(values)


def conflict_transition_diagnostic(
    assets: Mapping[str,Sequence[Any]], index: int, *, symbols: Sequence[str],
    lag: int = 21,
)->dict[str,Any]:
    if lag < 1 or index <= lag:
        raise ValueError("index must be greater than lag")
    previous=state_at(assets,index-lag,symbols=symbols)
    current=state_at(assets,index,symbols=symbols)
    disagreement=disagreement_at(assets,index,symbols=symbols)
    velocity=state_velocity(previous,current)
    payload={
        "schema_version":1,
        "index":index,
        "lag":lag,
        "symbols":list(symbols),
        "candidate_ids":list(CANDIDATES),
        "state_velocity":velocity,
        "mechanism_disagreement":disagreement["mechanism_disagreement"],
        "previous_state_fingerprint":previous["provenance_fingerprint"],
        "current_state_fingerprint":current["provenance_fingerprint"],
        "disagreement_fingerprint":disagreement["provenance_fingerprint"],
        "uses_future_bars":False,
        "uses_performance_labels":False,
        "uses_holdout":False,
        "uses_optimizer":False,
        "performance_evaluation":False,
    }
    payload["fingerprint"]=_fp(payload)
    return payload


def run(manifest:Path, output:Path)->dict[str,Any]:
    assets=load_frozen_snapshot(manifest)
    parsed=json.loads(manifest.read_text(encoding="utf-8"))
    symbols=tuple(parsed["symbols"])
    length=len(next(iter(assets.values())))
    indices=(400,631,862,1093,1324,1555,1786,2017,2248,2479,2710,2941,3172,3403)
    observations=[conflict_transition_diagnostic(assets,i,symbols=symbols) for i in indices if i < length]
    result={
        "schema_version":1,
        "component":"RCCSM-CONFLICT-TRANSITION-DIAGNOSTIC",
        "source_snapshot_fingerprint":parsed["snapshot_fingerprint"],
        "source_trial_id":"T-2026-09-28-089-COVERAGE",
        "symbols":list(symbols),
        "sample_count":len(observations),
        "candidate_ids":list(CANDIDATES),
        "observations":observations,
        "governance":{
            "performance_evaluation":False,"holdout_used":False,"selection_used":False,
            "parameter_search":False,"asset_search":False,"threshold_search":False,
            "performance_trial_authorized":False,"automatic_promotion":False,
        },
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
        "status":"DIAGNOSTIC_FEASIBILITY_PASSED",
    }
    result["fingerprint"]=_fp(result)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"sample_count":len(observations),"fingerprint":result["fingerprint"]},sort_keys=True))
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    raise SystemExit(0 if run(Path(a.manifest),Path(a.output))["status"]=="DIAGNOSTIC_FEASIBILITY_PASSED" else 1)
