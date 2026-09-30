"""Bounded provenance primitives for the Research OS Evidence Bus."""
from __future__ import annotations
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Mapping

ROOT=Path(__file__).resolve().parents[1]
REGISTRY_PATH=ROOT/"research/governance/research_os_source_registry_2026_09_30.json"
REQUIRED=("schema_version","receipt_type","source_id","source_url","retrieved_at","available_at","release_id","parser_version","raw_fingerprint","normalized_fingerprint","pit_status","access_status","scientific_evidence","performance_authorization","holdout_used")

def canonical_json(value:Any)->str:
    return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(",",":"),allow_nan=False)
def fingerprint(value:Any)->str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()
def utc_now()->str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def load_registry(path:Path=REGISTRY_PATH)->dict[str,Any]:
    payload=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload,dict) or payload.get("research_os_version")!="ROS-0.1": raise ValueError("Unsupported Research OS registry.")
    return payload
def source_index(registry:Mapping[str,Any])->dict[str,dict[str,Any]]:
    out={}
    for item in registry.get("source_lattice",[]):
        if not isinstance(item,dict) or not item.get("id") or not str(item.get("source_url","")).startswith("https://"): raise ValueError("Invalid Research OS source entry.")
        if item["id"] in out: raise ValueError(f"Duplicate source_id: {item['id']}")
        out[item["id"]]=item
    if not out: raise ValueError("Empty Research OS source lattice.")
    return out
def _ts(value:str|None)->datetime|None:
    if value is None:return None
    try:d=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:raise ValueError(f"Invalid timestamp: {value}") from exc
    if d.tzinfo is None:raise ValueError("Timestamp must include timezone.")
    return d.astimezone(timezone.utc)
def build_receipt(*,source_id:str,raw_payload:Any,normalized_payload:Any|None=None,retrieved_at:str|None=None,available_at:str|None=None,release_id:str|None=None,parser_version:str="unparsed",pit_status:str="DISCOVERY_ONLY",access_status:str="SUCCESS",receipt_type:str="source_fetch",registry:Mapping[str,Any]|None=None)->dict[str,Any]:
    registry=registry or load_registry(); source=source_index(registry).get(source_id)
    if source is None: raise ValueError(f"Unregistered source_id: {source_id}")
    retrieved_at=retrieved_at or utc_now(); normalized_payload=raw_payload if normalized_payload is None else normalized_payload
    receipt={"schema_version":1,"receipt_type":receipt_type,"source_id":source_id,"source_url":source["source_url"],"retrieved_at":retrieved_at,"available_at":available_at,"release_id":release_id,"parser_version":parser_version,"raw_fingerprint":fingerprint(raw_payload),"normalized_fingerprint":fingerprint(normalized_payload),"pit_status":pit_status,"access_status":access_status,"scientific_evidence":False,"performance_authorization":False,"holdout_used":False,"registry_research_os_version":registry["research_os_version"],"registry_source_pit_fit":source.get("pit_fit")}
    receipt["receipt_fingerprint"]=fingerprint(receipt); validate_receipt(receipt,registry=registry); return receipt
def validate_receipt(receipt:Mapping[str,Any],*,registry:Mapping[str,Any]|None=None)->None:
    registry=registry or load_registry(); missing=[x for x in REQUIRED if x not in receipt]
    if missing: raise ValueError("Missing receipt fields: "+",".join(missing))
    source=source_index(registry).get(receipt["source_id"])
    if source is None: raise ValueError("Receipt uses unregistered source.")
    if receipt["source_url"]!=source["source_url"]: raise ValueError(f"Source URL drift for {receipt['source_id']}.")
    r,a=_ts(receipt["retrieved_at"]),_ts(receipt["available_at"])
    if a and r and a>r: raise ValueError("available_at cannot be later than retrieved_at.")
    if receipt["scientific_evidence"] is not False or receipt["performance_authorization"] is not False or receipt["holdout_used"] is not False: raise ValueError("Operational receipt cannot become scientific evidence, authorization, or holdout input.")
    for key in ("raw_fingerprint","normalized_fingerprint","receipt_fingerprint"):
        if not isinstance(receipt.get(key),str) or len(receipt[key])!=64: raise ValueError(f"{key} must be SHA-256.")
def write_receipt(receipt:Mapping[str,Any],output:str|Path)->Path:
    validate_receipt(receipt); path=Path(output); path=path if path.is_absolute() else ROOT/path; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8"); return path
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--validate",type=Path); a=p.parse_args()
    if not a.validate:p.error("pass --validate RECEIPT.json")
    validate_receipt(json.loads(a.validate.read_text(encoding="utf-8"))); print("RESEARCH OS EVIDENCE RECEIPT OK"); return 0
if __name__=="__main__": raise SystemExit(main())
