"""Q094 coverage, PIT and adjusted-close input freeze.

This module is upstream of performance and performs no performance evaluation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
import urllib.error
from pathlib import Path

from automation.fixed_window_candidate_discovery import run_discovery
from automation.q079_input_freeze import fetch_adjusted_close
from data.canonical_snapshot import load_frozen_snapshot, snapshot_from_preregistration
from data.yahoo_loader import load_yahoo_history
from portfolio.q094_monthly_rebalance import VARIANTS, monthly_rebalance_indices, monthly_targets_at

ROOT = Path(__file__).resolve().parents[1]
TRIAL_ID="T-2026-09-29-094"
COVERAGE_ID="T-2026-09-29-094-COVERAGE"
PIT_ID="T-2026-09-29-094-PIT"
INPUT_ID="T-2026-09-29-094-INPUT-FREEZE"
REQUESTED=5000
TARGET=3500
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}


def _fp(v:object)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def _load(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _loader(symbol, interval, requested_candles, **kwargs):
    last=None
    for attempt in range(3):
        try:
            return load_yahoo_history(symbol, interval, requested_candles, **kwargs)
        except Exception as exc:
            last=exc
            if attempt<2:
                time.sleep(2**attempt)
    raise RuntimeError(f"{symbol}: source acquisition failed after 3 attempts: {last}")


def coverage(prereg:dict)->dict:
    pool=tuple(prereg["data_contract"]["candidate_pool"])
    discovery_path=ROOT/"research/runs/q094_coverage"/COVERAGE_ID/"discovery.json"
    discovery=run_discovery(output=discovery_path,symbol_limit=len(pool),workers=8,candidate_pool=pool)
    selected=tuple(discovery["selected_coverage_batch"][:8])
    if len(selected)!=8:
        raise RuntimeError("Q094 did not obtain eight coverage-valid fresh symbols")
    spec={
      "trial_id":COVERAGE_ID,
      "universe":"validation_2026_09_29_q094_monthly_rebalance",
      "symbols":list(selected),
      "interval":"1d",
      "requested_candles":REQUESTED,
      "raw_fetch_candles":REQUESTED,
      "target_common_candles":TARGET,
      "study_window":{"start":"2011-01-01","end":"2025-09-24"}
    }
    snap=snapshot_from_preregistration(spec,output_root=ROOT/"research/runs/q094_coverage",loader=_loader)
    if snap["status"]!="COVERAGE_PASSED":
        raise RuntimeError("Q094 coverage failed")
    receipt={
      "schema_version":"1.0","trial_id":COVERAGE_ID,
      "research_family":"low_turnover_monthly_rebalance_after_q093_cost_diagnosis",
      "status":"COVERAGE_PASSED","symbols":list(selected),
      "universe":spec["universe"],
      "common_calendar_count":snap["coverage"]["common_calendar_count"],
      "snapshot_fingerprint":snap["snapshot_fingerprint"],
      "source_discovery_fingerprint":discovery["fingerprint"],
      "selection_used":False,"asset_selection_by_performance":False,
      "performance_evaluation":False,"holdout_evaluation":False,"safety":SAFETY
    }
    receipt["result_fingerprint"]=_fp(receipt)
    ev=ROOT/"research/evidence";ev.mkdir(parents=True,exist_ok=True)
    (ev/"q094_coverage_result.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"
",encoding="utf-8")
    freeze={**receipt}
    freeze["asset_freeze_fingerprint"]=freeze.pop("result_fingerprint")
    (ev/"q094_asset_freeze.json").write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+"
",encoding="utf-8")
    return receipt


def pit(prereg:dict)->dict:
    coverage=_load(ROOT/"research/evidence/q094_coverage_result.json")
    freeze=_load(ROOT/"research/evidence/q094_asset_freeze.json")
    manifest=ROOT/"research/runs/q094_coverage"/COVERAGE_ID/"snapshot_manifest.json"
    assets=load_frozen_snapshot(manifest)
    symbols=tuple(freeze["symbols"])
    if any(len(assets[s])!=TARGET for s in symbols): raise RuntimeError("Q094 snapshot geometry invalid")
    indices=monthly_rebalance_indices(assets,symbols)
    checks=0
    for idx in (0,1,21,63,146,273,756,1200,1800,2400,3000,3496):
        if idx>=TARGET-1: continue
        original=monthly_targets_at(assets,idx,symbols)
        mutated={s:list(v) for s,v in assets.items()}
        for s,bars in mutated.items():
            for j in range(idx+1,min(len(bars),idx+8)):
                b=bars[j]
                bars[j]=type(b)(timestamp=b.timestamp,open=b.open*13,high=b.high*13,low=b.low*0.04,close=b.close*0.04,volume=b.volume*17)
        mutated={s:tuple(v) for s,v in mutated.items()}
        if monthly_targets_at(mutated,idx,symbols)!=original:
            raise AssertionError(f"Q094 PIT future mutation changed targets at {idx}")
        checks+=1
        for variant,weights in original.items():
            gross=sum(abs(float(x)) for x in weights.values())
            if gross>1+1e-12: raise AssertionError(f"{variant} gross > 1")
    if not indices:
        raise RuntimeError("Q094 no monthly rebalance sessions")
    receipt={
      "schema_version":"1.0","trial_id":PIT_ID,"status":"PIT_PASSED",
      "coverage_trial_id":COVERAGE_ID,"symbols":list(symbols),
      "variants":list(VARIANTS),"rebalance_contract":prereg["rebalance_contract"],
      "rebalance_session_count":len(indices),"checked_decision_points":checks,
      "future_mutation_checks_passed":True,"performance_evaluation":False,
      "selection_used":False,"holdout_used_for_selection":False,
      "performance_trial_authorized":False,
      "asset_freeze_fingerprint":freeze["asset_freeze_fingerprint"],"safety":SAFETY
    }
    receipt["result_fingerprint"]=_fp(receipt)
    (ROOT/"research/evidence/q094_pit_result.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"
",encoding="utf-8")
    return receipt


def input_freeze(prereg:dict)->dict:
    coverage=_load(ROOT/"research/evidence/q094_coverage_result.json")
    manifest_path=ROOT/"research/runs/q094_coverage"/COVERAGE_ID/"snapshot_manifest.json"
    manifest=_load(manifest_path)
    symbols=list(coverage["symbols"])
    outroot=ROOT/"research/runs/q094_input_bundle"/INPUT_ID
    outroot.mkdir(parents=True,exist_ok=True)
    datasets=[]
    for symbol in symbols:
        rows=[]
        csvpath=ROOT/manifest["data_snapshot"]["datasets"][symbols.index(symbol)]["path"]
        with csvpath.open("r",encoding="utf-8",newline="") as f:
            rows=list(csv.DictReader(f))
        timestamps=[row["timestamp"] for row in rows]
        values=fetch_adjusted_close(symbol,timestamps)
        dest=outroot/symbol/"adjusted_close.csv";dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("w",encoding="utf-8",newline="") as f:
            w=csv.writer(f,lineterminator="\n");w.writerow(("timestamp","adjusted_close"));w.writerows(values)
        datasets.append({"symbol":symbol,"path":(Path(symbol)/"adjusted_close.csv").as_posix(),"row_count":len(values),"first_timestamp":values[0][0],"last_timestamp":values[-1][0],"fingerprint":_fp(values)})
    bundle={
      "schema_version":"1.0","trial_id":INPUT_ID,"source_snapshot_fingerprint":manifest["snapshot_fingerprint"],
      "symbols":symbols,"datasets":datasets,"performance_network_access":False,"selection_used":False,
      "performance_evaluation":False,"holdout_used_for_selection":False,"safety":SAFETY
    }
    bundle["bundle_fingerprint"]=_fp(bundle)
    (outroot/"input_bundle_manifest.json").write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+"
",encoding="utf-8")
    result={
      "schema_version":"1.0","trial_id":INPUT_ID,"status":"INPUT_BUNDLE_FROZEN",
      "coverage_trial_id":COVERAGE_ID,"source_snapshot_fingerprint":manifest["snapshot_fingerprint"],
      "bundle_fingerprint":bundle["bundle_fingerprint"],"symbols":symbols,"datasets":datasets,
      "performance_network_access":False,"selection_used":False,"performance_evaluation":False,
      "holdout_used_for_selection":False,"safety":SAFETY
    }
    (ROOT/"research/evidence/q094_input_freeze_result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"
",encoding="utf-8")
    return result


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=("coverage","pit","input-freeze","all"),default="all")
    a=ap.parse_args(); prereg=_load(ROOT/"research/preregistrations/q094_monthly_rebalance_q091_low_turnover_2026_09_29.json")
    if a.mode in ("coverage","all"): coverage(prereg)
    if a.mode in ("pit","all"): pit(prereg)
    if a.mode in ("input-freeze","all"): input_freeze(prereg)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
