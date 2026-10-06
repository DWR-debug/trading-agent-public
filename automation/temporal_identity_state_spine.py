"""Deterministic Temporal/Identity/State Spine compiler.

Metadata/control-plane only. It does not read market outcomes, rank candidates,
select holdouts, tune parameters or authorize performance.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN_TRUE={"performance","performance_authorization","holdout_selection","ranking","tuning","promotion_authorization","promotion","live_execution"}

def load(path:Path)->dict:
    if not path.is_file():
        raise SystemExit(f"missing input: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def sha256_json(obj:object)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def assert_safe(obj:dict,label:str)->None:
    for k in FORBIDDEN_TRUE:
        if obj.get(k) is True:
            raise SystemExit(f"{label}: forbidden flag {k}=true")

def _required(record:dict, fields:list[str], label:str)->None:
    missing=[f for f in fields if f not in record]
    if missing:
        raise ValueError(f"{label}: missing fields: {','.join(missing)}")

def validate_temporal_record(record:dict, *, label:str="temporal_record")->dict:
    required=["source_id","source_record_id","event_time","public_observed_at","retrieved_at","revision_time","clock_semantics"]
    _required(record,required,label)
    event_time=parse_iso(record["event_time"])
    public_time=parse_iso(record["public_observed_at"])
    retrieved_time=parse_iso(record["retrieved_at"])
    revision_time=parse_iso(record["revision_time"])
    if public_time > retrieved_time:
        raise ValueError(f"{label}: public_observed_at after retrieved_at")
    if revision_time is not None and revision_time < public_time:
        raise ValueError(f"{label}: revision_time before public_observed_at")
    return {"event_time":event_time.isoformat() if event_time else None,
            "public_observed_at":public_time.isoformat(),
            "retrieved_at":retrieved_time.isoformat(),
            "revision_time":revision_time.isoformat() if revision_time else None}

def validate_identity_record(record:dict, *, label:str="identity_record")->dict:
    required=["source_id","source_entity_id","canonical_entity_id","mapping_version","valid_from","valid_to","mapping_status","evidence_fingerprint"]
    _required(record,required,label)
    start=parse_iso(record["valid_from"])
    end=parse_iso(record["valid_to"])
    if end is not None and end < start:
        raise ValueError(f"{label}: valid_to before valid_from")
    if not str(record["evidence_fingerprint"]):
        raise ValueError(f"{label}: evidence_fingerprint empty")
    return {"mapping_version":record["mapping_version"],
            "valid_from":start.isoformat(),
            "valid_to":end.isoformat() if end else None,
            "mapping_status":record["mapping_status"]}

def validate_state_transition(record:dict, *, label:str="state_transition")->dict:
    required=["state_id","entity_id","state_before","state_after","transition_observed_at","source_component","revision_lineage","historical_prefix_fingerprint"]
    _required(record,required,label)
    observed=parse_iso(record["transition_observed_at"])
    if record["state_before"] == record["state_after"]:
        raise ValueError(f"{label}: no-op transition")
    if not record["historical_prefix_fingerprint"]:
        raise ValueError(f"{label}: historical prefix fingerprint empty")
    if not isinstance(record["revision_lineage"], list):
        raise ValueError(f"{label}: revision_lineage must be a list")
    return {"state_id":record["state_id"],
            "entity_id":record["entity_id"],
            "transition_observed_at":observed.isoformat(),
            "state_before":record["state_before"],
            "state_after":record["state_after"]}

def parse_iso(v):
    if not v: return None
    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    if d.tzinfo is None:
        raise SystemExit("timestamp must be timezone-aware")
    return d

def compile_spine(contract:dict, relation:dict, specs:dict, registry:dict)->dict:
    if contract.get("status")!="ACTIVE_METADATA_ONLY":
        raise SystemExit("spine contract is not active metadata-only")
    assert_safe(contract,"contract")
    assert_safe(relation,"relation")
    candidates=[str(x["id"]) for x in specs.get("candidates",[]) if x.get("id")]
    if len(candidates)!=len(set(candidates)):
        raise SystemExit("duplicate candidate ids")
    components={x.get("id"):x for x in relation.get("reusable_components",[]) if x.get("id")}
    links=relation.get("candidate_component_links",[])
    relations=relation.get("candidate_relations",[])
    missing_components=sorted({x.get("component") for x in links if x.get("component") not in components})
    candidate_ids=set(candidates)
    unresolved_candidates=sorted({x.get("candidate") for x in links if x.get("candidate") not in candidate_ids})
    shared={}
    for x in links:
        shared.setdefault(x.get("component"),set()).add(x.get("candidate"))
    shared_component_groups=[]
    for comp,cids in sorted(shared.items()):
        cids=sorted(cids)
        shared_component_groups.append({
            "component":comp,
            "status":components.get(comp,{}).get("status"),
            "candidate_count":len(cids),
            "candidates":cids,
            "routing_priority":len(cids),
            "route":"shared_prerequisite_then_candidate_specific_gate" if len(cids)>1 else "candidate_specific_gate"
        })
    shared_component_groups.sort(key=lambda x:(-x["routing_priority"],x["component"]))
    edge_issues=[]
    for e in relations:
        if e.get("from") not in candidate_ids or e.get("to") not in candidate_ids:
            edge_issues.append(e)
    out={
        "schema_version":1,
        "record_type":"temporal_identity_state_spine_index",
        "status":"READY_FOR_CANDIDATE_SPECIFIC_PIT_WORK",
        "generated_at_utc":datetime.now().astimezone().isoformat(),
        "source_contract":"research/governance/temporal_identity_state_spine_contract_2026_10_06.json",
        "relation_contract":"research/governance/knowledge_relation_graph_contract_2026_10_06.json",
        "candidate_spec_count":len(candidates),
        "source_registry":"research/governance/research_os_source_registry_2026_09_30.json",
        "spine_layers":["T","I","S","R"],
        "shared_component_groups":shared_component_groups,
        "highest_unblocking_components":shared_component_groups[:5],
        "graph_integrity":{
            "missing_component_refs":missing_components,
            "unresolved_historical_candidate_links":unresolved_candidates,
            "candidate_edge_issues":edge_issues,
            "component_ref_integrity_ok":not missing_components,
            "candidate_reference_integrity_ok":not unresolved_candidates,
            "relation_endpoint_integrity_ok":not edge_issues
        },
        "temporal_contract":contract["temporal_contract"],
        "identity_contract":contract["identity_contract"],
        "state_contract":contract["state_contract"],
        "composition_rules":contract["composition_rules"],
        "discovery_patterns":contract["high_value_patterns"],
        "safety":{
            "PAPER_ONLY":True,"LIVE_TRADING_ENABLED":False,"ORDERS_ENABLED":False,"AUTOMATIC_PROMOTION":False,
            "performance":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False
        },
        "registry_source_count":len(registry.get("source_lattice",[])),
    }
    out["content_fingerprint"]=sha256_json(out)
    return out

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=ROOT/"research/governance/temporal_identity_state_spine_contract_2026_10_06.json")
    ap.add_argument("--relation",type=Path,default=ROOT/"research/governance/knowledge_relation_graph_contract_2026_10_06.json")
    ap.add_argument("--specs",type=Path,default=ROOT/"research/candidates/orthogonal_candidate_specs_2026-10-05.json")
    ap.add_argument("--registry",type=Path,default=ROOT/"research/governance/research_os_source_registry_2026_09_30.json")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    result=compile_spine(load(args.contract),load(args.relation),load(args.specs),load(args.registry))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
