"""Retrospective negative-evidence atlas.

This module mines already recorded performance/diagnostic artifacts. It does not
rerun experiments, optimize parameters, select candidates/assets, use holdouts
for selection, change gates, or authorize promotion.

The purpose is to convert repeated failure signatures into explicit research
constraints and falsifiable design questions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUTS = (
    "research/evidence/q077r1_performance_result.json",
    "research/evidence/q081r4_performance_result.json",
    "research/evidence/q089_performance_result.json",
    "research/evidence/q091_performance_result.json",
    "research/evidence/q094_performance_result.json",
    "research/evidence/q095_performance_result.json",
    "research/evidence/c29_performance_result.json",
    "research/evidence/cross_trial_failure_diagnosis_2026_09_25.json",
)


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"INPUT_NOT_OBJECT:{path}")
    return data


def _gate_map(arm: dict[str, Any]) -> dict[str, bool]:
    candidates = (
        arm.get("gates"),
        arm.get("performance_evaluation", {}).get("gates")
        if isinstance(arm.get("performance_evaluation"), dict)
        else None,
    )
    for value in candidates:
        if isinstance(value, dict) and value:
            return {str(k): bool(v) for k, v in value.items() if isinstance(v, bool)}
    return {}


def _arms(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    raw = payload.get("arms", payload.get("variants", {}))
    if isinstance(raw, dict):
        return [(str(k), v) for k, v in raw.items() if isinstance(v, dict)]
    if isinstance(raw, list):
        out = []
        for idx, item in enumerate(raw):
            if isinstance(item, dict):
                name = str(item.get("arm") or item.get("variant") or item.get("name") or idx)
                out.append((name, item))
        return out
    return []


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def analyze(paths: list[Path]) -> dict[str, Any]:
    trials: list[dict[str, Any]] = []
    gate_trial_sets: defaultdict[str, set[str]] = defaultdict(set)
    gate_arm_failures: Counter[str] = Counter()
    trial_failure_counts: dict[str, int] = {}

    cross_trial = None
    for path in paths:
        payload = _load(path)
        if path.name.startswith("cross_trial_failure_diagnosis"):
            cross_trial = payload
            continue

        trial_id = str(payload.get("trial_id") or path.stem)
        arm_rows = []
        failed_any: set[str] = set()
        for name, arm in _arms(payload):
            gates = _gate_map(arm)
            failed = sorted(k for k, v in gates.items() if not v)
            failed_any.update(failed)
            for gate in failed:
                gate_trial_sets[gate].add(trial_id)
                gate_arm_failures[gate] += 1
            arm_rows.append(
                {
                    "arm": name,
                    "failed_gates": failed,
                    "gates_observed": len(gates),
                }
            )
        trial_failure_counts[trial_id] = len(failed_any)
        trials.append(
            {
                "trial_id": trial_id,
                "status": payload.get("status"),
                "arm_count": len(arm_rows),
                "arm_diagnostics": arm_rows,
                "failed_gate_union": sorted(failed_any),
            }
        )

    recurring = sorted(
        (
            {
                "gate": gate,
                "trial_count": len(trial_ids),
                "arm_failure_count": gate_arm_failures[gate],
                "trial_ids": sorted(trial_ids),
            }
            for gate, trial_ids in gate_trial_sets.items()
            if len(trial_ids) >= 2
        ),
        key=lambda row: (-row["trial_count"], -row["arm_failure_count"], row["gate"]),
    )

    risk_core = {
        "research_drawdown_lte_10pct",
        "rolling_average_drawdown_lte_10pct",
        "holdout_drawdown_lte_10pct",
    }
    risk_trials = [
        t["trial_id"]
        for t in trials
        if risk_core.issubset(set(t["failed_gate_union"]))
    ]

    lessons = [
        {
            "id": "NEG-01",
            "observation": "risk/stability gates recur across multiple otherwise distinct formal trials",
            "evidence": {
                "trials_with_all_three_core_risk_failures": len(risk_trials),
                "trial_ids": risk_trials,
            },
            "research_implication": (
                "Treat additional portfolio-risk-control variants as a secondary "
                "research branch; prioritize orthogonal information mechanisms and "
                "state-aware designs before reserving another formal trial."
            ),
            "status": "DESIGN_CONSTRAINT_HYPOTHESIS",
        },
        {
            "id": "NEG-02",
            "observation": "candidate/variant migrations can be diagnosed from existing rolling controls without rerunning experiments",
            "research_implication": (
                "Prefer fixed-rule mechanisms with provenance-complete state definitions "
                "over adaptive retuning. Any migration pattern is retrospective evidence "
                "only and cannot justify parameter changes by itself."
            ),
            "status": "DESIGN_CONSTRAINT_HYPOTHESIS",
        },
        {
            "id": "NEG-03",
            "observation": "positive holdout fragments have not been sufficient for formal success when fixed risk/stability gates fail",
            "research_implication": (
                "Use holdout only as the predeclared final test; do not treat a positive "
                "holdout component as an override for fixed risk/stability failures."
            ),
            "status": "GOVERNANCE_LESSON",
        },
        {
            "id": "NEG-04",
            "observation": "public source accessibility is not equivalent to historical PIT completeness",
            "research_implication": (
                "Make publication time, archive depth, identifier mapping, amendments "
                "and revision handling first-class signal inputs before formalization."
            ),
            "status": "DATA_CONTRACT_LESSON",
        },
    ]

    if cross_trial:
        patterns = cross_trial.get("cross_trial_patterns_by_id", {})
        lessons.append(
            {
                "id": "NEG-05",
                "observation": "the archived cross-trial diagnosis explicitly records recurring control-relative and OOS stability failures",
                "evidence": {
                    "pattern_keys": sorted(patterns),
                    "source_fingerprint": cross_trial.get("source", {}).get("diagnosis_fingerprint"),
                },
                "research_implication": (
                    "New candidate generation should target independent information "
                    "content rather than another cosmetic variant of the same control family."
                ),
                "status": "ARCHIVED_DIAGNOSTIC_LESSON",
            }
        )

    result = {
        "schema_version": "1.0",
        "diagnostic_id": "Q101-NEGATIVE-EVIDENCE-ATLAS-2026-09-30",
        "status": "RETROSPECTIVE_DIAGNOSTIC_ONLY",
        "source_inputs": [str(p).replace("\\", "/") for p in paths],
        "trial_count": len(trials),
        "gate_recurrence": recurring,
        "trial_failure_counts": trial_failure_counts,
        "trials": trials,
        "lessons": lessons,
        "governance": {
            "new_backtest": False,
            "parameter_search": False,
            "threshold_search": False,
            "asset_search": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "gate_changes": False,
            "performance_authorization": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["analysis_fingerprint"] = _fingerprint(result)
    return result


def markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Q101 Negative Evidence Atlas",
        "",
        f"Diagnostic fingerprint: {result['analysis_fingerprint']}",
        "",
        "This is retrospective evidence mining only. No new backtest, optimization, "
        "candidate selection, holdout selection, gate change or authorization occurred.",
        "",
        "## Recurrent gate failures",
        "",
        "| Gate | Trials | Arm failures |",
        "| --- | ---: | ---: |",
    ]
    for row in result["gate_recurrence"]:
        lines.append(
            f"| {row['gate']} | {row['trial_count']} | {row['arm_failure_count']} |"
        )
    lines.extend(["", "## Lessons", ""])
    for lesson in result["lessons"]:
        lines.extend(
            [
                f"### {lesson['id']}",
                f"Observation: {lesson['observation']}",
                f"Implication: {lesson['research_implication']}",
                f"Status: {lesson['status']}",
                "",
            ]
        )
    lines.extend(
        [
            "Paper-Only: True; Live-Trading: False; Orders: False; Automatic-Promotion: False.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="research/runs/q101_negative_evidence_atlas")
    parser.add_argument("inputs", nargs="*", default=None)
    args = parser.parse_args()
    raw_inputs = args.inputs or list(DEFAULT_INPUTS)
    paths = [Path(x) for x in raw_inputs]
    result = analyze(paths)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "result.md").write_text(markdown(result), encoding="utf-8")
    print("Q101_STATUS:", result["status"])
    print("Q101_TRIAL_COUNT:", result["trial_count"])
    print("Q101_RECURRING_GATES:", len(result["gate_recurrence"]))
    print("Q101_FINGERPRINT:", result["analysis_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
