"""Consolidate the four fresh-symbol Q218 replication receipts without changing any rules."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

TRIAL_ID="T-2026-10-08-Q218-REPLICATION-01"
SYMBOLS=("GOOGL","META","ORCL","PFE")
OUT_NAME="q218_independent_replication_latest.json"

def canonical(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)

def fp(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-root",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    recs=[]
    for sym in SYMBOLS:
        p=a.input_root/sym/f"q218_replication_{sym}.json"
        if not p.is_file() or p.stat().st_size==0:
            raise RuntimeError(f"MISSING_REPLICATION_RECEIPT:{sym}")
        r=json.loads(p.read_text(encoding="utf-8"))
        if r.get("replication_trial_id")!=TRIAL_ID or r.get("symbol")!=sym:
            raise RuntimeError(f"IDENTITY_MISMATCH:{sym}")
        if r.get("performance_output_reuse_for_rule_changes") is not False:
            raise RuntimeError(f"INDEPENDENCE_BOUNDARY:{sym}")
        if r.get("post_pass_optimization") is not False:
            raise RuntimeError(f"OPTIMIZATION_BOUNDARY:{sym}")
        if r.get("safety") != {"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}:
            raise RuntimeError(f"SAFETY_BOUNDARY:{sym}")
        recs.append(r)
    agg={
      "schema_version":"1.0",
      "record_type":"q218_independent_replication",
      "candidate_id":"Q218",
      "replication_trial_id":TRIAL_ID,
      "parent_trial_id":"T-2026-10-08-Q218-PERFORMANCE-01",
      "status":"Q218_INDEPENDENT_FRESH_SYMBOL_REPLICATION_COMPLETED",
      "fresh_symbol_disjoint":True,
      "symbols":list(SYMBOLS),
      "symbol_receipts":[
        {"symbol":r["symbol"],"event_count":r["event_count"],"receipt_fingerprint":r["receipt_fingerprint"]}
        for r in recs
      ],
      "total_event_count":sum(int(r["event_count"]) for r in recs),
      "performance_evaluation":True,
      "holdout_evaluation":False,
      "selection_used":False,
      "holdout_used_for_selection":False,
      "parameter_search":False,
      "threshold_search":False,
      "horizon_search":False,
      "asset_search":False,
      "variant_search":False,
      "post_pass_optimization":False,
      "performance_output_reuse_for_rule_changes":False,
      "candidate_ranking":False,
      "promotion_decision":False,
      "independent_replication_only":True,
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
    }
    agg["replication_fingerprint"]=fp(agg)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(agg,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":agg["status"],"total_event_count":agg["total_event_count"],"replication_fingerprint":agg["replication_fingerprint"]},sort_keys=True))

if __name__=="__main__":
    main()
