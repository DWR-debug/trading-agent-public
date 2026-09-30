"""Bounded dispatch map for the self-hosted research worker.

The self-hosted runner is intentionally not an arbitrary shell executor.
Only predefined, non-production lanes can be selected. Formal evidence
production remains on the canonical GitHub-hosted research paths.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PYTHON = sys.executable

LANES: dict[str, list[list[str]]] = {
    "autonomous_frontier_qa": [
        [
            PYTHON,
            "-m",
            "pytest",
            "-q",
            "tests/test_rccsm_feasibility.py",
            "tests/test_rccsm_synthetic.py",
            "tests/test_rccsm_state_topology.py",
            "tests/test_frontier_feasibility.py",
            "tests/test_q096_frontier_source_pit_audit.py",
            "tests/test_q097_public_short_flow_candidates.py",
            "tests/test_q097_public_short_flow_feasibility.py",
            "tests/test_q098_historical_archive_depth.py",
            "tests/test_q100_frontier_feasibility_synthesis.py",
            "tests/test_q089_validation.py",
            "tests/test_q089_input_freeze.py",
            "tests/test_q089_performance_envelope.py",
            "tests/test_research_governance_audit.py",
        ],
        [
            PYTHON,
            "-m",
            "py_compile",
            "automation/q095_contract_audit.py",
            "automation/q095_performance.py",
            "automation/q095_reconcile.py",
        ],
        [
            PYTHON,
            "-m",
            "automation.q075_information_channel_contract",
        ],
        [
            PYTHON,
            "-m",
            "automation.q084_candidate_feasibility",
        ],
        [
            PYTHON,
            "-m",
            "automation.q096_frontier_source_pit_audit",
        ],
        [
            PYTHON,
            "-m",
            "automation.q098_historical_archive_depth",
        ],
        [
            PYTHON,
            "-m",
            "automation.q099_q081r4_failure_diagnosis",
            "--output",
            "research/runs/q099_q081r4_failure_diagnosis/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q100_frontier_feasibility_synthesis",
            "--output",
            "research/runs/q100_frontier_feasibility_synthesis/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q095_contract_audit",
        ],
        [
            PYTHON,
            "-c",
            (
                "from automation.rccsm_feasibility import feasibility_manifest, route_mesh; "
                "state={'trend_coherence':0.8,'breadth':0.7,'dispersion':0.3,'event_density':0.1}; "
                "print('RCCSM_AUTONOMOUS_FEASIBILITY', feasibility_manifest()['fingerprint'], "
                "route_mesh('RCCSM-AUTO', state))"
            ),
        ],
        [
            PYTHON,
            "-m",
            "automation.q092_q091_failure_diagnosis",
            "--repo-root",
            ".",
            "--output",
            "research/runs/self_hosted/q092_q091_failure_diagnosis.json",
            "--markdown",
            "research/runs/self_hosted/q092_q091_failure_diagnosis.md",
        ],
    ],
    "repo_qa": [
        [
            PYTHON,
            "-c",
            (
                "import ast, pathlib; "
                "files=sorted(p for root in ('automation','data','research') "
                "for p in pathlib.Path(root).rglob('*.py')); "
                "[ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in files]; "
                "print(f'AST_SYNTAX_OK files={len(files)}')"
            ),
        ],
        [PYTHON, "-m", "pytest", "-q"],
    ],
    "data_qa": [
        [
            PYTHON,
            "-m",
            "pytest",
            "-q",
            "tests/test_canonical_snapshot.py",
            "tests/test_github_free_resource_policy.py",
        ],
    ],
    "design_qa": [[PYTHON, "-m", "automation.q022_design_guard"]],
    "local_reproduction": [
        [
            PYTHON,
            "-c",
            (
                "import ast, pathlib; "
                "files=sorted(p for root in ('automation','data','research') "
                "for p in pathlib.Path(root).rglob('*.py')); "
                "[ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in files]; "
                "print(f'AST_LOCAL_REPRODUCTION_OK files={len(files)}')"
            ),
        ],
        [PYTHON, "-m", "pytest", "-q", "tests/test_research_gates.py"],
        [PYTHON, "-m", "automation.q095_contract_audit"],
    ],
}


def run(command: list[str], out_dir: Path, index: int) -> dict[str, object]:
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    payload = {
        "index": index,
        "command": command,
        "returncode": completed.returncode,
        "started_at": started,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    (out_dir / f"step-{index:02d}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[self_hosted {index}] returncode={completed.returncode}", flush=True)
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n", flush=True)
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", flush=True)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", choices=sorted(LANES), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    exit_code = 0
    for index, command in enumerate(LANES[args.lane], start=1):
        result = run(command, args.output_dir, index)
        results.append(result)
        if result["returncode"] != 0:
            exit_code = int(result["returncode"])
            break

    summary = {
        "schema_version": "1.0",
        "lane": args.lane,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "formal_evidence_allowed": False,
        "paper_only": True,
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    run_manifest = {
        "schema_version": 1,
        "lane": args.lane,
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "runner_name": os.environ.get("RUNNER_NAME"),
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "formal_research_evidence": False,
        "step_count": len(results),
        "step_return_codes": [result["returncode"] for result in results],
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
