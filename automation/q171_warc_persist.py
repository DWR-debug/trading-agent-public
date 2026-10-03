"""Persist a stable, material Q171 WARC reconstruction receipt.

Volatile workflow paths and run IDs are removed so repeated scheduled runs
only create a repository commit when material reconstruction evidence changes.
"""
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
    ap.add_argument("--source-commit",required=True)
    args=ap.parse_args()
    data=json.loads(args.input.read_text(encoding="utf-8"))
    material={
      "schema_version":data.get("schema_version"),
      "task_id":data.get("task_id"),
      "source_commit":args.source_commit,
      "coverage_receipt_fingerprint":data.get("coverage_receipt_fingerprint"),
      "results":data.get("results",{}),
      "summary":data.get("summary",{}),
      "scientific_boundary":data.get("scientific_boundary",{}),
      "safety":data.get("safety",{}),
    }
    material["receipt_fingerprint"]=sha(material)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(material,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PERSISTENCE_READY","receipt_fingerprint":material["receipt_fingerprint"]},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())