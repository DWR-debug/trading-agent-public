"""Bounded cross-platform worker used only when the trusted Windows pool is stale/unavailable.

This worker is a failover execution path, not a formal evidence path. It only
runs predefined QA/feasibility work and always marks formal evidence as false.
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
    "frontier_qa": [
        [
            PYTHON, "-m", "pytest", "-q",
            "tests/test_rccsm_feasibility.py",
            "tests/test_rccsm_synthetic.py",
            "tests/test_rccsm_state_topology.py",
            "tests/test_frontier_feasibility.py",
            "tests/test_q096_frontier_source_pit_audit.py",
            "tests/test_q097_public_short_flow_candidates.py",
            "tests/test_q097_public_short_flow_feasibility.py",
            "tests/test_q098_historical_archive_depth.py",
            "tests/test_q099_q081r4_failure_diagnosis.py",
            "tests/test_q100_frontier_feasibility_synthesis.py",
            "tests/test_q089_validation.py",
            "tests/test_q089_input_freeze.py",
            "tests/test_q089_performance_envelope.py",
            "tests/test_research_governance_audit.py",
        ],
        [PYTHON, "-m", "automation.q075_information_channel_contract"],
        [PYTHON, "-m", "automation.q084_candidate_feasibility"],
        [PYTHON, "-m", "automation.q096_frontier_source_pit_audit"],
        [PYTHON, "-m", "automation.q098_historical_archive_depth"],
        [
            PYTHON, "-m", "automation.q099_q081r4_failure_diagnosis",
            "--output", "research/runs/hosted_fallback/q099_failure_diagnosis.json",
        ],
        [
            PYTHON, "-m", "automation.q100_frontier_feasibility_synthesis",
            "--output", "research/runs/hosted_fallback/q100_frontier_feasibility_synthesis.json",
        ],
        [PYTHON, "-m", "automation.q095_contract_audit"],
    ],
    "governance_reproduction": [
        [
            PYTHON, "-m", "pytest", "-q",
            "tests/test_research_gates.py",
            "tests/test_c29_performance.py",
            "tests/test_research_governance_audit.py",
            "tests/test_ai_worker_fabric.py",
        ],
        [
            PYTHON, "-m", "py_compile",
            "automation/q095_contract_audit.py",
            "automation/q095_performance.py",
            "automation/q095_reconcile.py",
            "automation/autonomous_control_plane.py",
        ],
        [PYTHON, "-m", "automation.q095_contract_audit"],
    ],
}

def _run(command: list[str], out_dir: Path, index: int) -> dict[str, object]:
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    result = {
        "index": index,
        "command": command,
        "returncode": completed.returncode,
        "started_at": started,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    (out_dir / f"step-{index:02d}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", choices=sorted(LANES), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    exit_code = 0
    for index, command in enumerate(LANES[args.lane], start=1):
        result = _run(command, args.output_dir, index)
        results.append(result)
        if result["returncode"] != 0:
            exit_code = int(result["returncode"])
            break

    manifest = {
        "schema_version": 1,
        "mode": "hosted_failover",
        "lane": args.lane,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "results_count": len(results),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "runner_name": os.environ.get("RUNNER_NAME"),
        "runner_os": os.environ.get("RUNNER_OS"),
        "runner_arch": os.environ.get("RUNNER_ARCH"),
        "python_version": platform.python_version(),
        "formal_evidence_allowed": False,
        "formal_research_evidence": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "fallback_only": True,
    }
    (args.output_dir / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "summary.json").write_text(json.dumps({
        "schema_version": 1,
        "mode": "hosted_failover",
        "lane": args.lane,
        "results": results,
        "formal_evidence_allowed": False,
        "fallback_only": True,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())