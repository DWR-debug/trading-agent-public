"""Network-free executor for the fixed Q218 independent replication."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from automation.q218_deterministic_performance_executor import (
    _safe_child,
    construct_features,
    file_sha256,
    fp,
    validate_bundle_sources,
)

TRIAL_ID="T-2026-10-08-Q218-REPLICATION-01"
SOURCE_TRIAL_ID="T-2026-10-08-Q218-PERFORMANCE-01"
CONTRACT=ROOT/"research/governance/q218_independent_replication_contract_2026_10_08.json"


def load(path: Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(bundle_path: Path, contract_path: Path)->dict[str,Any]:
    bundle=load(bundle_path)
    contract=load(contract_path)
    if bundle.get("trial_id")!=TRIAL_ID:
        raise RuntimeError("Q218 replication bundle trial mismatch")
    if contract.get("replication_trial_id")!=TRIAL_ID or contract.get("status")!="FROZEN_INDEPENDENT_REPLICATION_CONTRACT":
        raise RuntimeError("Q218 replication contract invalid")
    primary_contract = ROOT/"research/governance/q218_performance_contract_2026_10_08.json"
    if contract.get("base_contract_sha256") != file_sha256(primary_contract):
        raise RuntimeError("Q218 replication base contract fingerprint mismatch")
    if contract.get("primary_performance_report_fingerprint") != "78c4a667b01bebe0aa23361e78856155fa3e3fe861cb6fcc1e4b79973cbddc5d":
        raise RuntimeError("Q218 replication primary provenance fingerprint drifted")
    if contract.get("replication_boundaries", {}).get("no_primary_result_reuse_for_rule_changes") is not True:
        raise RuntimeError("Q218 replication primary-result reuse boundary invalid")
    expected=bundle.get("bundle_fingerprint")
    unsigned=dict(bundle); unsigned.pop("bundle_fingerprint",None)
    if not expected or fp(unsigned)!=expected:
        raise RuntimeError("Q218 replication bundle self-fingerprint mismatch")
    if bundle.get("executor_network_access") is not False:
        raise RuntimeError("Q218 replication executor must be network-free")
    if any(bundle.get(k) is not False for k in ("selection_used","parameter_search","threshold_search","horizon_search","asset_search","variant_search","holdout_selection_used")):
        raise RuntimeError("Q218 replication bundle crosses selection boundary")
    expected_effective=str(bundle.get("contract_sha256") or "")
    effective=load(bundle_path.parent/"q218_effective_replication_contract.json")
    effective_sha=hashlib.sha256((bundle_path.parent/"q218_effective_replication_contract.json").read_bytes()).hexdigest()
    if expected_effective!=effective_sha:
        raise RuntimeError("Q218 effective replication contract fingerprint mismatch")
    if effective.get("trial_id")!=TRIAL_ID:
        raise RuntimeError("Q218 effective replication contract trial mismatch")
    validate_bundle_sources(bundle,bundle_path.parent)
    return bundle


def execute(bundle_path: Path, contract_path: Path, output_path: Path)->dict[str,Any]:
    bundle=verify(bundle_path,contract_path)
    docs={str(d["accession"]):d for d in bundle["documents"]}
    bars={(str(b["symbol"]),str(b["session"])):b for b in bundle["market_bars"]}
    rows=[]
    for event in bundle["events"]:
        mandatory=docs.get(str(event["ten_k_accession"]))
        voluntary=docs.get(str(event["item_2_02_8k_accession"]))
        if not mandatory or not voluntary:
            raise RuntimeError("Q218 replication paired documents missing")
        bar=bars.get((str(event["issuer"]),str(event["action_session"])))
        if not bar:
            raise RuntimeError(f"Q218 replication market bar missing: {event['issuer']} {event['action_session']}")
        op=float(bar["open"]); cl=float(bar["close"])
        if not math.isfinite(op) or not math.isfinite(cl) or op<=0 or cl<=0:
            raise RuntimeError("Q218 replication invalid market price")
        features=construct_features(
            _safe_child(bundle_path.parent,str(mandatory["path"])).read_bytes(),
            _safe_child(bundle_path.parent,str(voluntary["path"])).read_bytes(),
        )
        rows.append({
          "issuer":event["issuer"],
          "ten_k_accession":event["ten_k_accession"],
          "item_2_02_8k_accession":event["item_2_02_8k_accession"],
          "pair_closure_clock":event["pair_closure_clock"],
          "action_session":event["action_session"],
          "features":features,
          "outcome":cl/op-1.0,
        })
    result={
      "schema_version":"1.0",
      "record_type":"q218_independent_replication_performance_result",
      "candidate_id":"Q218",
      "source_trial_id":SOURCE_TRIAL_ID,
      "replication_trial_id":TRIAL_ID,
      "event_count":len(rows),
      "events":rows,
      "base_contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
      "effective_contract_sha256":bundle["contract_sha256"],
      "bundle_fingerprint":bundle["bundle_fingerprint"],
      "primary_performance_report_fingerprint":"78c4a667b01bebe0aa23361e78856155fa3e3fe861cb6fcc1e4b79973cbddc5d",
      "primary_performance_output_used_for_rule_changes":False,
      "performance_evaluation":True,
      "holdout_evaluation":False,
      "selection_used":False,
      "holdout_used_for_selection":False,
      "parameter_search":False,
      "threshold_search":False,
      "horizon_search":False,
      "asset_search":False,
      "variant_search":False,
      "family_ranking":False,
      "promotion_decision":False,
      "safety":{
        "paper_only":True,
        "live_trading_enabled":False,
        "orders_enabled":False,
        "automatic_promotion":False,
      }
    }
    result["report_fingerprint"]=fp(result)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"
",encoding="utf-8")
    return result


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--bundle",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=execute(args.bundle,args.contract,args.output)
    print(json.dumps({"status":"PASS","event_count":result["event_count"],"report_fingerprint":result["report_fingerprint"]},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
