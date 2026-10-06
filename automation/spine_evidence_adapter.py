"""Conservative adapter from Research OS Evidence Bus receipts to T/I/S/R nodes.

Only explicit public-observation semantics are promoted to the temporal spine.
No outcome data, ranking, tuning or scientific authorization is produced.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN={"performance","performance_authorization","holdout_used","holdout_selection","ranking","tuning","promotion_authorization","live_execution"}

def load(p:Path):
    with p.open(encoding="utf-8") as f: return json.load(f)

def sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def assert_safe(obj):
    for k in FORBIDDEN:
        if obj.get(k) is True:
            raise ValueError(f"forbidden scientific flag: {k}=true")

def receipt_to_temporal_node(receipt:dict, *, available_at_is_public_observation:bool=False)->dict:
    assert_safe(receipt)
    required=["schema_version","source_id","source_url","retrieved_at","available_at","release_id","raw_fingerprint","normalized_fingerprint","pit_status","receipt_fingerprint"]
    missing=[k for k in required if k not in receipt]
    if missing: raise ValueError("receipt missing: "+",".join(missing))
    node={
        "node_type":"T",
        "source_id":receipt["source_id"],
        "source_record_id":receipt.get("release_id") or receipt["receipt_fingerprint"],
        "event_time":None,
        "public_observed_at":receipt["available_at"] if available_at_is_public_observation else None,
        "retrieved_at":receipt["retrieved_at"],
        "revision_time":None,
        "clock_semantics":"explicit_public_observation" if available_at_is_public_observation else "available_at_not_proven_public",
        "source_url":receipt["source_url"],
        "release_id":receipt["release_id"],
        "pit_status":receipt["pit_status"],
        "raw_fingerprint":receipt["raw_fingerprint"],
        "normalized_fingerprint":receipt["normalized_fingerprint"],
        "receipt_fingerprint":receipt["receipt_fingerprint"],
        "provenance_status":"PUBLIC_CLOCK_EXPLICIT" if available_at_is_public_observation else "PUBLIC_CLOCK_UNPROVEN",
    }
    node["node_fingerprint"]=sha(node)
    return node

def identity_record_to_node(record:dict)->dict:
    required=["source_id","source_entity_id","canonical_entity_id","mapping_version","valid_from","valid_to","mapping_status","evidence_fingerprint"]
    missing=[k for k in required if k not in record]
    if missing: raise ValueError("identity record missing: "+",".join(missing))
    node={"node_type":"I",**record}
    node["node_fingerprint"]=sha(node)
    return node

def state_transition_to_node(record:dict)->dict:
    required=["state_id","entity_id","state_before","state_after","transition_observed_at","source_component","revision_lineage","historical_prefix_fingerprint"]
    missing=[k for k in required if k not in record]
    if missing: raise ValueError("state record missing: "+",".join(missing))
    if record["state_before"]==record["state_after"]: raise ValueError("state transition is a no-op")
    node={"node_type":"S",**record}
    node["node_fingerprint"]=sha(node)
    return node

def build_bundle(receipt=None, identity=None, state=None, *, available_at_is_public_observation=False):
    bundle={"schema_version":1,"record_type":"spine_evidence_bundle","nodes":[],"scientific_evidence":False,"performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False}
    if receipt is not None: bundle["nodes"].append(receipt_to_temporal_node(receipt,available_at_is_public_observation=available_at_is_public_observation))
    if identity is not None: bundle["nodes"].append(identity_record_to_node(identity))
    if state is not None: bundle["nodes"].append(state_transition_to_node(state))
    bundle["bundle_fingerprint"]=sha(bundle)
    return bundle

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--receipt",type=Path)
    ap.add_argument("--identity",type=Path)
    ap.add_argument("--state",type=Path)
    ap.add_argument("--available-at-is-public-observation",action="store_true")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    b=build_bundle(load(args.receipt) if args.receipt else None,load(args.identity) if args.identity else None,load(args.state) if args.state else None,available_at_is_public_observation=args.available_at_is_public_observation)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(b,indent=2,ensure_ascii=False)+chr(10),encoding="utf-8")
    print(json.dumps(b,sort_keys=True))
if __name__=="__main__":
    main()
