"""Bounded Top-4 research workpack.

Only source/PIT/structure work is performed. No market outcomes, ranking,
parameter/horizon search, holdout selection, tuning, promotion or live execution.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PYTHON=sys.executable
COMMON_TESTS=[
    "tests/test_candidate_robustness_gate.py",
    "tests/test_canonical_snapshot.py",
    "tests/test_github_free_resource_policy.py",
]
LANES={
    "Q218":[
        [PYTHON,"-m","automation.q218_q221_historical_source_census","--output","{OUT}/q218_q221_historical_source_census.json"],
        [PYTHON,"-m","pytest","-q",*COMMON_TESTS],
        [PYTHON,"-m","pytest","-q","tests/test_q218_q221_historical_source_census.py","tests/test_q218_q221_candidate_gate_compiler.py"],
    ],
    "Q219":[
        [PYTHON,"-m","pytest","-q","tests/test_q129_options_source_feasibility.py","tests/test_q129_options_pit_reproduction.py"],
        [PYTHON,"-m","pytest","-q","tests/test_q218_q221_candidate_gate_compiler.py"],
    ],
    "Q220":[
        [PYTHON,"-m","automation.q218_q221_historical_source_census","--output","{OUT}/q220_source_census.json"],
        [PYTHON,"-m","pytest","-q","tests/test_q218_q221_historical_source_census.py"],
        [PYTHON,"-m","pytest","-q","tests/test_q104_xbrl_concept_freeze_audit.py","tests/test_q104_i19_xbrl_pit_compiler.py"],
    ],
    "Q221":[
        [PYTHON,"-m","automation.top_candidate_source_preflight","--output","{OUT}/top_candidate_source_preflight.json"],
        [PYTHON,"-m","pytest","-q","tests/test_q218_q221_candidate_gate_compiler.py"],
    ],
}

def run_cmd(cmd:list[str], out:Path, idx:int)->dict:
    cmd=[x.replace("{OUT}",str(out)) for x in cmd]
    started=datetime.now(timezone.utc).isoformat()
    p=subprocess.run(cmd,text=True,capture_output=True,check=False)
    row={"index":idx,"command":cmd,"returncode":p.returncode,"started_at":started,
         "completed_at":datetime.now(timezone.utc).isoformat(),"stdout":p.stdout,"stderr":p.stderr}
    (out/f"step-{idx:02d}.json").write_text(json.dumps(row,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return row

def main()->int:
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",choices=sorted(LANES),required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    out=args.output_dir
    out.mkdir(parents=True,exist_ok=True)
    results=[run_cmd(c,out,i) for i,c in enumerate(LANES[args.candidate],1)]
    failed=[r["index"] for r in results if r["returncode"]!=0]
    manifest={
        "schema_version":1,"candidate":args.candidate,
        "source_commit":os.environ.get("GITHUB_SHA"),
        "runner_name":os.environ.get("RUNNER_NAME"),
        "python_version":platform.python_version(),
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "results":results,"failed_steps":failed,
        "scientific_evidence":False,"performance_authorization":False,
        "holdout_selection":False,"ranking":False,"tuning":False,
        "promotion":False,"live_execution":False,"paper_only":True,
    }
    canonical=json.dumps(manifest,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    manifest["receipt_fingerprint"]=hashlib.sha256(canonical).hexdigest()
    (out/"run_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,sort_keys=True))
    return 0 if not failed else 1

if __name__=="__main__":
    raise SystemExit(main())