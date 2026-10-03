"""Persist a stable, material Q133-Q170 PIT-readiness receipt."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha(value: object) -> str:
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--source-code-sha256",required=True)
    args=ap.parse_args()
    data=json.loads(args.input.read_text(encoding="utf-8"))
    material={
      "schema_version":data.get("schema_version"),
      "receipt_type":data.get("receipt_type"),
      "wave_id":data.get("wave_id"),
      "source_receipt":data.get("source_receipt"),
      "source_results":data.get("source_results",{}),
      "candidate_results":data.get("candidate_results",[]),
      "synthetic_mutation_checks":data.get("synthetic_mutation_checks",{}),
      "scientific_boundary":data.get("scientific_boundary",{}),
      "safety":data.get("safety",{}),
      "source_code_sha256":args.source_code_sha256,
    }
    material["receipt_fingerprint"]=sha(material)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(material,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PERSISTENCE_READY","receipt_fingerprint":material["receipt_fingerprint"]},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())