"""Update the Q218 focus-gate receipt index from a successful gate artifact."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "research/evidence/q218_focus_gate_receipt_index_latest.json"
CODE_PATHS = {"source": "automation/q218_sec_multichannel_source_gate.py", "event_pair": "automation/q218_sec_event_pair_lineage_gate.py"}

def blob_sha(path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True).strip()

def fingerprint(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()

def load() -> dict[str, Any]:
    if INDEX.exists():
        return json.loads(INDEX.read_text(encoding="utf-8"))
    return {"schema_version":"1.0","record_type":"q218_focus_gate_receipt_index","candidate_id":"Q218","source_gate":{},"event_pair_gate":{},
            "scientific_boundary":{"performance_authorized":False,"holdout_selection_allowed":False,"ranking_allowed":False,"parameter_search_allowed":False,"threshold_search_allowed":False,"horizon_search_allowed":False,"promotion_allowed":False,"live_execution_allowed":False},
            "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", choices=["source","event_pair"], required=True)
    ap.add_argument("--run-id", type=int, required=True)
    ap.add_argument("--artifact-id", type=int, required=True)
    ap.add_argument("--artifact-digest", required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt.get("candidate_id") != "Q218": raise RuntimeError("Q218_RECEIPT_CANDIDATE_MISMATCH")
    positive = bool(receipt.get("all_required_issuer_channels_observed")) if args.gate == "source" else (bool(receipt.get("all_pairing_valid")) and all(bool(x.get("all_lineage_valid")) for x in (receipt.get("issuer_results") or {}).values()))
    if not positive: raise RuntimeError("Q218_GATE_RECEIPT_NOT_POSITIVE:"+args.gate)
    index = load()
    code_sha = blob_sha(CODE_PATHS[args.gate])
    index[args.gate + "_gate"] = {"run_id":args.run_id,"artifact_id":args.artifact_id,"artifact_digest":args.artifact_digest,"receipt_fingerprint":receipt.get("receipt_fingerprint"),"verified_positive_complete":True,"gate_code_blob_sha":code_sha,"verified_at_utc":datetime.now(timezone.utc).isoformat()}
    source = index.get("source_gate", {}); event = index.get("event_pair_gate", {})
    source_current = bool(source.get("verified_positive_complete")) and str(source.get("gate_code_blob_sha") or "") == blob_sha(CODE_PATHS["source"])
    event_current = bool(event.get("verified_positive_complete")) and str(event.get("gate_code_blob_sha") or "") == blob_sha(CODE_PATHS["event_pair"])
    both = source_current and event_current
    index["status"] = "Q218_SOURCE_AND_EVENT_PAIR_GATES_COMPLETE" if both else "Q218_SOURCE_OR_EVENT_GATE_PARTIAL"
    index["verified_at_utc"] = datetime.now(timezone.utc).isoformat()
    index["next_gate"] = "INDEPENDENT_ARCHITECTURE_PIT_REPRODUCTION" if both else ("DETERMINISTIC_10K_8K_EVENT_PAIR_AND_AMENDMENT_LINEAGE" if not event_current else "SEC_MULTICHANNEL_SOURCE_GATE")
    index["routing_trigger"] = "POSITIVE_COMPLETE_GATE_INDEX"
    index["record_fingerprint"] = fingerprint(index)
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate":args.gate,"status":index["status"],"gate_code_blob_sha":code_sha,"receipt_fingerprint":receipt.get("receipt_fingerprint")}, sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())