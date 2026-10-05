"""Deterministic public-source preflight for the current top-candidate wave.

Discovery/source feasibility only. No performance, ranking, tuning, promotion or
live execution is performed by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

TARGETS = {
    "Q218_sec_submissions": "https://data.sec.gov/submissions/CIK0000320193.json",
    "Q218_sec_edgar_entity": "https://www.sec.gov/edgar/browse/?CIK=320193",
    "Q220_fsn_dataset_landing": "https://www.sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets",
    "Q220_fsn_smallest_archive": "https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets/2009q1_notes.zip",
    "Q221_usaspending_home": "https://www.usaspending.gov/",
    "Q221_usaspending_award_example": "https://www.usaspending.gov/award/CONT_AWD_1332KP23FNEEB0050_1330_1305M421ANAAA0093_1330",
}

def run(output: Path) -> dict:
    headers = {"User-Agent": "TradingAgent-Public-Research/1.0 research@example.invalid"}
    result = {
        "schema_version": 1,
        "record_type": "top_candidate_source_preflight",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidates": ["Q218", "Q219", "Q220", "Q221"],
        "checks": [],
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    }
    for name, url in TARGETS.items():
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=25) as response:
                body = response.read() if url.endswith(".zip") else response.read(8192)
                row = {
                    "name": name,
                    "url": url,
                    "status": getattr(response, "status", 200),
                    "content_type": response.headers.get("Content-Type"),
                    "sample_bytes": len(body),
                }
                if url.endswith(".zip"):
                    try:
                        with zipfile.ZipFile(io.BytesIO(body)) as archive:
                            row["zip_parse_ok"] = True
                            row["zip_members_sample"] = archive.namelist()[:12]
                    except Exception as exc:
                        row["zip_parse_ok"] = False
                        row["zip_parse_error"] = type(exc).__name__ + ":" + str(exc)
                result["checks"].append(row)
        except Exception as exc:
            result["checks"].append(
                {"name": name, "url": url, "error": type(exc).__name__ + ":" + str(exc)}
            )
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    result["bundle_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args.output)
    print(json.dumps(payload, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
