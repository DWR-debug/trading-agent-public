"""Publish one current Q218 focus-gate receipt into the canonical index."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"research/evidence/q218_focus_gate_receipt_index_latest.json"

def blob_sha(path:str)->str:
    return subprocess.check_output(["git","rev-parse",f"HEAD:{path}"],text=True).strip()

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--gate",choices=("source","event_pair"),required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--run-id",type=int,required=True)
    args=p.parse_args()
    if not args.receipt.exists(): raise SystemExit("Q218_GATE_RECEIPT_MISSING")
    receipt=json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt.get("candidate_id")!="Q218": raise SystemExit("Q218_GATE_RECEIPT_CANDIDATE_MISMATCH")
    if receipt.get("scientific_boundary",{}).get("performance_authorized") is not False: raise SystemExit("Q218_GATE_PERFORMANCE_BOUNDARY_FAILED")
    if receipt.get("safety",{}).get("paper_only") is not True: raise SystemExit("Q218_GATE_SAFETY_BOUNDARY_FAILED")
    data=json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {"schema_version":"1.0","record_type":"q218_focus_gate_receipt_index","candidate_id":"Q218"}
    code_path="automation/q218_sec_multichannel_source_gate.py" if args.gate=="source" else "automation/q218_sec_event_pair_lineage_gate.py"
    other_path="automation/q218_sec_event_pair_lineage_gate.py" if args.gate=="source" else "automation/q218_sec_multichannel_source_gate.py"
    key="source_gate" if args.gate=="source" else "event_pair_gate"
    other_key="event_pair_gate" if args.gate=="source" else "source_gate"
    artifact_lines=subprocess.check_output(
        ["gh","api",f"/repos/{subprocess.check_output(['git','config','--get','remote.origin.url'],text=True).strip().split('github.com/')[-1].rstrip()}"+f"/actions/runs/{args.run_id}/artifacts",
         "--jq",".artifacts[] | select(.expired==false) | [.id,.digest] | @tsv"],
        text=True
    ).splitlines()
    if not artifact_lines: raise SystemExit("Q218_GATE_ARTIFACT_NOT_FOUND")
    artifact_id,artifact_digest=artifact_lines[0].split("\t",1)
    data[key]={
        "run_id":args.run_id,
        "artifact_id":int(artifact_id),
        "artifact_digest":artifact_digest,
        "receipt_fingerprint":receipt.get("receipt_fingerprint"),
        "verified_positive_complete":True,
        "gate_code_blob_sha":blob_sha(code_path),
    }
    current_source=bool(data.get("source_gate",{}).get("verified_positive_complete")) and data.get("source_gate",{}).get("gate_code_blob_sha")==blob_sha("automation/q218_sec_multichannel_source_gate.py")
    current_event=bool(data.get("event_pair_gate",{}).get("verified_positive_complete")) and data.get("event_pair_gate",{}).get("gate_code_blob_sha")==blob_sha("automation/q218_sec_event_pair_lineage_gate.py")
    data["status"]="Q218_SOURCE_AND_EVENT_PAIR_GATES_COMPLETE" if current_source and current_event else "Q218_FOCUS_GATE_PARTIAL_CURRENT_CONTEXT"
    data["verified_at_utc"]=receipt.get("generated_at_utc")
    data["next_gate"]="INDEPENDENT_ARCHITECTURE_PIT_REPRODUCTION" if current_source and current_event else ("event-pair gate" if current_source else "source gate")
    INDEX.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":data["status"],"gate":args.gate,"run_id":args.run_id,"receipt_fingerprint":receipt.get("receipt_fingerprint")},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
