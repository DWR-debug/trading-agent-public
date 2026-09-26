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
    "repo_qa": [
        [
            PYTHON,
            "-c",
            (
                "import ast, pathlib; "
                "files=sorted(p for root in ('automation','data','research') "
                "for p in pathlib.Path(root).rglob('*.py')); "
                "[(ast.parse(p.read_text(encoding='utf-8'), filename=str(p)), None)[1] "
                "for p in files]; "
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
    "local_reproduction": [
        [PYTHON, "-m", "compileall", "-q", "automation", "data", "research"],
        [PYTHON, "-m", "pytest", "-q", "tests/test_research_governance.py"],
    ],
}


def run(command: list[str], out_dir: Path, index: int) -> dict[str, object]:
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )
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
    print(f"[repo_qa step {index}] returncode={completed.returncode}", flush=True)
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
