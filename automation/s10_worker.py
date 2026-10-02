"""Optional isolated S10 Evidence-Critic benchmark runner.

Unavailable S10 is an operational skip, never a scientific failure.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from automation.evidence_critic_benchmark import main as benchmark_main
from automation.s10_runtime import resolve


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, default=Path("research/benchmarks/evidence_critic_pilot_2026_10_01.jsonl"))
    ap.add_argument("--option-order-checks", type=int, default=6)
    args = ap.parse_args()

    descriptor = resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if not descriptor.get("available"):
        result = {
            "schema_version": 1,
            "task_id": "ECL-2026-10-01-001-S10",
            "status": descriptor.get("status", "S10_UNAVAILABLE"),
            "model": descriptor.get("model"),
            "endpoint": descriptor.get("base_url"),
            "descriptor_path": descriptor.get("path"),
            "runner_name": os.environ.get("RUNNER_NAME"),
            "source_commit": os.environ.get("GITHUB_SHA"),
            "worker_output_is_scientific_evidence": False,
            "governance": {
                "performance_evaluation": False,
                "holdout_selection": False,
                "candidate_selection": False,
                "candidate_ranking": False,
                "promotion": False,
                "live_execution": False,
            },
        }
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": result["status"], "model": None}))
        return 0

    # The benchmark CLI reads its arguments from sys.argv, so invoke it through
    # the module-level parser with a controlled temporary argv.
    import sys
    old = sys.argv[:]
    try:
        sys.argv = [
            "evidence_critic_benchmark",
            "--endpoint", str(descriptor["base_url"]),
            "--model", str(descriptor["model"]),
            "--corpus", str(args.corpus),
            "--output", str(args.output),
            "--option-order-checks", str(args.option_order_checks),
        ]
        return benchmark_main()
    finally:
        sys.argv = old


if __name__ == "__main__":
    raise SystemExit(main())
