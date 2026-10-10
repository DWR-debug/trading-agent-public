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
WORKPACK_PURPOSES={
    "Q104:I19":"13F acceptance-time closure and deterministic XBRL PIT compiler contract diagnostics",
    "Q221":"USAspending historical public-clock, agency-exception and recipient-to-issuer mapping gate",
    "Q220":"as-filed XBRL narrative/structured mapping and concept-freeze diagnostics",
}

WORKPACK_GATE_PATHS={
    "Q104:I19":["automation/q104_i19_13f_historical_identity_census.py","automation/q104_i19_xbrl_pit_compiler.py","automation/q104_xbrl_concept_freeze_audit.py"],
    "Q221":["automation/q221_usaspending_public_clock_gate.py","automation/q221_historical_source_vintage_gate.py","tests/test_q221_usaspending_public_clock_gate.py","tests/test_q221_historical_source_vintage_gate.py"],
    "Q220":["tests/test_q220_as_filed_xbrl_population_gate.py","automation/q104_xbrl_concept_freeze_audit.py","automation/q104_i19_xbrl_pit_compiler.py"],
}

LANES={
    "Q104:I19":[
        [PYTHON,"-m","automation.q104_i19_xbrl_pit_compiler","--output","{OUT}/q104_i19_xbrl_pit_compiler.json"],
        [PYTHON,"-m","pytest","-q","tests/test_q104_i19_xbrl_concept_freeze.py","tests/test_q104_i19_xbrl_pit_compiler.py","tests/test_q104_candidate_wave_contract.py"],
        [PYTHON,"-m","pytest","-q","tests/test_q104_i19_13f_historical_identity_census.py","tests/test_q104_i19_historical_identity_census.py"],
    ],
    "Q220":[
        [PYTHON,"-m","pytest","-q","tests/test_q220_as_filed_xbrl_population_gate.py"],
        [PYTHON,"-m","pytest","-q","tests/test_q104_xbrl_concept_freeze_audit.py","tests/test_q104_i19_xbrl_pit_compiler.py"],
    ],
    "Q221":[
        [PYTHON,"-m","automation.q221_usaspending_public_clock_gate","--output","{OUT}/q221_usaspending_public_clock_gate.json"],
        [PYTHON,"-m","automation.q221_historical_source_vintage_gate","--output","{OUT}/q221_historical_source_vintages.json"],
        [PYTHON,"-m","pytest","-q","tests/test_q221_usaspending_public_clock_gate.py","tests/test_q221_historical_source_vintage_gate.py"],
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
        "workpack_contract_version":"focused-2026-10-10-v1",
        "workpack_purpose":WORKPACK_PURPOSES[args.candidate],
        "workpack_gate_paths":WORKPACK_GATE_PATHS[args.candidate],
        "source_commit":os.environ.get("GITHUB_SHA"),
        "runner_name":os.environ.get("RUNNER_NAME"),
        "execution_mode":os.environ.get("TOP4_EXECUTION_MODE","STANDARD_BOUNDED_RESEARCH"),
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