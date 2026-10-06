"""Inspect the SEC Financial Statement Notes archive schema for Q220.

Source/PIT structure only. No market outcomes or authorization.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

URL = "https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets/2009q1_notes.zip"

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent":"TradingAgent-Public-Q220-FSN-Schema/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def run(output: Path) -> dict:
    body = fetch(URL)
    out = {
        "schema_version": 1,
        "record_type": "q220_fsn_schema_gate",
        "candidate_id": "Q220",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_sha256": hashlib.sha256(body).hexdigest(),
        "archive_bytes": len(body),
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    }
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        names = z.namelist()
        lower = {n.lower(): n for n in names}
        required = {
            "sub": {"sub.txt","sub.tsv"},
            "tag": {"tag.txt","tag.tsv"},
            "dim": {"dim.txt","dim.tsv"},
            "num": {"num.txt","num.tsv"},
            "txt": {"txt.txt","txt.tsv"},
            "pre": {"pre.txt","pre.tsv"},
        }
        out["members"] = names
        out["required_member_presence"] = {k:any(v in lower for v in vals) for k, vals in required.items()}
        out["tables"] = {}
        for key, variants in required.items():
            member = next((lower[v] for v in variants if v in lower), None)
            if not member:
                continue
            raw = z.read(member)[:262144].decode("utf-8-sig", errors="replace")
            rows = list(csv.reader(io.StringIO(raw), delimiter="\t"))
            header = rows[0] if rows else []
            out["tables"][key] = {
                "member": member,
                "header": header[:60],
                "header_count": len(header),
                "sample_rows": rows[1:3] if len(rows) > 1 else [],
            }
        sub = out["tables"].get("sub",{}).get("header",[])
        tag = out["tables"].get("tag",{}).get("header",[])
        num = out["tables"].get("num",{}).get("header",[])
        txt = out["tables"].get("txt",{}).get("header",[])
        pre = out["tables"].get("pre",{}).get("header",[])
        lower_sets = {
            "sub": {x.lower() for x in sub},
            "tag": {x.lower() for x in tag},
            "num": {x.lower() for x in num},
            "txt": {x.lower() for x in txt},
            "pre": {x.lower() for x in pre},
        }
        out["key_fields_observed"] = {
            "sub_adsh": "adsh" in lower_sets["sub"],
            "tag_tag": "tag" in lower_sets["tag"],
            "num_adsh": "adsh" in lower_sets["num"],
            "txt_adsh": "adsh" in lower_sets["txt"],
            "pre_adsh": "adsh" in lower_sets["pre"],
        }
        out["schema_minimum_pass"] = (
            all(out["required_member_presence"].values())
            and out["key_fields_observed"]["sub_adsh"]
            and out["key_fields_observed"]["tag_tag"]
        )
    out["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(out, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(run(args.output), sort_keys=True))