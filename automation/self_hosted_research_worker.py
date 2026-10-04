"""Bounded dispatch map for the self-hosted research worker.

The self-hosted runner is intentionally not an arbitrary shell executor.
Only predefined, non-production lanes can be selected. Formal evidence
production remains on the canonical GitHub-hosted research paths.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
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
            "tests/test_rccsm_observational_feasibility.py",
            "tests/test_frontier_feasibility.py",
            "tests/test_q096_frontier_source_pit_audit.py",
            "tests/test_q097_public_short_flow_candidates.py",
            "tests/test_q097_public_short_flow_feasibility.py",
            "tests/test_q098_historical_archive_depth.py",
            "tests/test_c29_fresh_pit.py",
            "tests/test_q100_frontier_feasibility_synthesis.py",
            "tests/test_q102_regime_negative_evidence.py",
            "tests/test_q103_rccsm_state_routing_integrity.py",
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
            "automation.q101_negative_evidence_atlas",
            "--output-dir",
            "research/runs/q101_negative_evidence_atlas",
        ],
        [
            PYTHON,
            "-m",
            "automation.q103_rccsm_state_routing_integrity",
            "--output",
            "research/runs/q103_rccsm_state_routing_integrity/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.rccsm_observational_feasibility",
            "--output",
            "research/runs/rccsm_observational/q089_rccsm_observational_feasibility.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q102_regime_negative_evidence",
            "--output-dir",
            "research/runs/q102_regime_negative_evidence",
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
        [
            PYTHON,
            "-m",
            "automation.h06_p2_readiness",
            "--output",
            "research/runs/self_hosted/h06_p2_readiness/result.json",
        ],
        [
            PYTHON,
            "-m",
            "pytest",
            "-q",
            "tests/test_q118_candidate_composition.py",
            "tests/test_q104_i19_xbrl_pit_compiler.py",
            "tests/test_q119_treasury_demand_shape.py",
            "tests/test_q119_treasury_source_feasibility.py",
            "tests/test_q120_cftc_positioning_state.py",
            "tests/test_q120_cftc_source_feasibility.py",
            "tests/test_q122_cftc_release_date_evidence.py",
            "tests/test_q104_i22_filing_arrival_compiler.py",
            "tests/test_s10_acceptance.py",
            "tests/test_research_hypothesis_compiler.py",
            "tests/test_research_clock_join.py",
        ],
        [
            PYTHON,
            "-m",
            "automation.research_hypothesis_compiler",
            "--output",
            "research/runs/self_hosted/research_discovery/hypothesis_quarantine.json",
        ],
        [
            PYTHON,
            "-c",
            (
                "from automation.research_clock_join import synthetic_contract; "
                "print('CROSS_CLOCK_SYNTHETIC', synthetic_contract())"
            ),
        ],
        [
            PYTHON,
            "-m",
            "automation.q119_treasury_source_feasibility",
            "--output",
            "research/runs/self_hosted/q119_treasury_source_feasibility/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q120_cftc_source_feasibility",
            "--output",
            "research/runs/self_hosted/q120_cftc_source_feasibility/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q122_cftc_release_date_evidence",
            "--output",
            "research/runs/self_hosted/q122_cftc_release_date_evidence/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q123_i25_sec_acceptance_clock_audit",
            "--output",
            "research/runs/self_hosted/q123_i25_sec_acceptance_clock_audit/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q125_f1_sec_publication_clock",
            "--output",
            "research/runs/self_hosted/q125_f1_sec_publication_clock/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q104_i22_filing_arrival_compiler",
            "--output",
            "research/runs/self_hosted/q104_i22_filing_arrival/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q104_xbrl_concept_freeze_audit",
            "--output",
            "research/runs/self_hosted/q104_xbrl_concept_freeze_audit/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q109_n7_common_holder_graph",
            "--output",
            "research/runs/self_hosted/q109_n7_common_holder_graph/result.json",
        ],
        [
            PYTHON,
            "-m",
            "pytest",
            "-q",
            "tests/test_q121_sec_beneficial_ownership_timing.py",
            "tests/test_q126_q132_frontier_feasibility.py",
        ],
        [
            PYTHON,
            "-m",
            "automation.q121_sec_beneficial_ownership_timing",
            "--output",
            "research/runs/self_hosted/q121_sec_beneficial_ownership_timing/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q126_q132_frontier_feasibility",
            "--output",
            "research/runs/self_hosted/q126_q132_frontier_feasibility/result.json",
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
            "tests/test_q193_q196_source_feasibility.py",
        ],
        [
            PYTHON,
            "-m",
            "automation.q179_q184_source_feasibility",
            "--output",
            "research/runs/self_hosted/q179_q184_source_feasibility/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q185_q186_source_feasibility",
            "--output",
            "research/runs/self_hosted/q185_q186_source_feasibility/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q187_q192_source_feasibility",
            "--output",
            "research/runs/self_hosted/q187_q192_source_feasibility/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q193_q196_source_feasibility",
            "--output",
            "research/runs/self_hosted/q193_q196_source_feasibility/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q188_q192_pit_census_r2",
            "--output",
            "research/runs/self_hosted/q188_q192_pit_census_r2/result.json",
        ],
    ],
    "design_qa": [[PYTHON, "-m", "automation.q022_design_guard"]],
    "local_reproduction": [
        [
            PYTHON,
            "-m",
            "automation.q121r6_sec_archive_url_smoke",
        ],
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
        [
            PYTHON,
            "-m",
            "pytest",
            "-q",
            "tests/test_q186_conservative_citation_visibility.py",
            "tests/test_q193_q196_source_feasibility.py",
        ],
        [
            PYTHON,
            "-m",
            "automation.q185_q186_source_feasibility",
            "--output",
            "research/runs/self_hosted/q185_q186_source_feasibility/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q187_q192_source_feasibility",
            "--output",
            "research/runs/self_hosted/q187_q192_source_feasibility/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q193_q196_source_feasibility",
            "--output",
            "research/runs/self_hosted/q193_q196_source_feasibility/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q186_pit_readiness_r2",
            "--output",
            "research/runs/self_hosted/q186_pit_readiness_r2/result.json",
        ],
        [
            PYTHON,
            "-m",
            "automation.q179_q184_source_feasibility",
            "--output",
            "research/runs/self_hosted/q179_q184_source_feasibility/result.json",
        ],
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


def default_max_workers(lane: str) -> int:
    """Return a conservative bounded concurrency for each lane."""
    return 3 if lane == "autonomous_frontier_qa" else 1


FRONTIER_WORKPACKS: tuple[tuple[int, ...], ...] = (
    tuple(range(1, 11)),
    tuple(range(11, 21)),
    tuple(range(21, 31)),
)


def select_workpack(lane: str, step_count: int, rotation_index: int = 0) -> tuple[str, list[int]]:
    """Select a deterministic bounded workpack for the current frontier pulse."""
    all_steps = list(range(1, step_count + 1))
    if lane != "autonomous_frontier_qa":
        return "full", all_steps
    pack_index = int(rotation_index) % len(FRONTIER_WORKPACKS)
    name = f"frontier_pack_{pack_index + 1}"
    selected = [index for index in FRONTIER_WORKPACKS[pack_index] if index <= step_count]
    return name, selected


def execution_groups(
    lane: str, step_count: int, rotation_index: int = 0
) -> list[list[int]]:
    """Return dependency-safe bounded execution groups for one capacity pulse."""
    _, selected = select_workpack(lane, step_count, rotation_index)
    if lane != "autonomous_frontier_qa":
        return [selected]
    dependency = [index for index in selected if index != 8]
    groups = [dependency] if dependency else []
    if 8 in selected:
        groups.append([8])
    return groups


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", choices=sorted(LANES), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--rotation-index",
        type=int,
        default=None,
        help="Deterministic frontier workpack selector; defaults to GITHUB_RUN_NUMBER.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Bounded concurrency override; defaults to lane-specific safe value.",
    )
    args = parser.parse_args()

    max_workers = args.max_workers if args.max_workers is not None else default_max_workers(args.lane)
    if max_workers < 1 or max_workers > 4:
        parser.error("--max-workers must be between 1 and 4")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rotation_index = (
        args.rotation_index
        if args.rotation_index is not None
        else int(os.environ.get("GITHUB_RUN_NUMBER", "0") or "0")
    )
    exit_code = 0
    failed_steps = []
    indexed_commands = list(enumerate(LANES[args.lane], start=1))
    command_map = dict(indexed_commands)
    results = []
    workpack_name, selected_steps = select_workpack(
        args.lane, len(LANES[args.lane]), rotation_index
    )

    # Execute dependency-safe groups sequentially; each group may use bounded
    # internal parallelism. This preserves wall-clock savings while preventing
    # artifact-consumer races such as Q100 reading Q096/Q098 before completion.
    for group in execution_groups(args.lane, len(indexed_commands), rotation_index):
        group_items = [(index, command_map[index]) for index in group]
        if max_workers == 1 or len(group_items) == 1:
            group_results = [run(command, args.output_dir, index) for index, command in group_items]
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(run, command, args.output_dir, index)
                    for index, command in group_items
                ]
                group_results = [future.result() for future in futures]
        results.extend(group_results)

    for result in results:
        if result["returncode"] != 0:
            # Keep executing independent bounded research/QA steps so one
            # non-critical failure cannot suppress unrelated diagnostics.
            # The lane still exits non-zero and therefore cannot be mistaken
            # for a clean heartbeat or formal evidence run.
            if exit_code == 0:
                exit_code = int(result["returncode"]) or 1
            failed_steps.append(int(result["index"]))

    results.sort(key=lambda result: int(result["index"]))

    summary = {
        "schema_version": "1.1",
        "lane": args.lane,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "max_workers": max_workers,
        "rotation_index": rotation_index,
        "workpack": workpack_name,
        "selected_steps": selected_steps,
        "results": results,
        "failed_steps": failed_steps,
        "all_bounded_steps_attempted": len(results) == len(LANES[args.lane]),
        "all_selected_bounded_steps_attempted": len(results) == len(selected_steps),
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
        "max_workers": max_workers,
        "rotation_index": rotation_index,
        "workpack": workpack_name,
        "selected_steps": selected_steps,
        "step_count": len(results),
        "step_return_codes": [result["returncode"] for result in results],
        "failed_steps": failed_steps,
        "all_bounded_steps_attempted": len(results) == len(LANES[args.lane]),
        "all_selected_bounded_steps_attempted": len(results) == len(selected_steps),
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
