"""Fast-path dispatch for executable dashboard capacity plans.

This is orchestration only: it dispatches already-defined workflows from the
current bounded dashboard plan, never creates new research hypotheses and never
authorizes performance, ranking, tuning, promotion or live execution.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PLATFORM_NAMES = {
    "Resource Dashboard Update",
    "Current Operational Status Synchronizer",
    "Current Status Drift Guard",
    "Spine Next-Gate Autonomous Router",
    "Workflow Lint",
    "CI",
    "Full Suite Verification",
    "T052 Exact Master CI Gate",
    "Unified Research Orchestrator",
    "Planned Capacity Fast Dispatch",
}

FOCUS_CANDIDATES = {"Q104:I19", "Q218"}
TOP4_CANDIDATES = {"Q218", "Q219", "Q220", "Q221"}
TOP4_PRIORITY = ("Q218", "Q219", "Q220", "Q221")
SLOT_SCOPED_WORKFLOW = ".github/workflows/top4-candidate-slot-research.yml"


Q218_GATE_INDEX_PATH = Path("research/evidence/q218_focus_gate_receipt_index_latest.json")
Q218_INDEPENDENT_WORKFLOW = ".github/workflows/q218-independent-architecture-pit-reproduction.yml"


def q218_positive_gate_index_current() -> set[str]:
    """Return positive Q218 gates only when the immutable index matches current code."""
    try:
        index = json.loads(Q218_GATE_INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    if index.get("status") != "Q218_SOURCE_AND_EVENT_PAIR_GATES_COMPLETE":
        return set()
    out: set[str] = set()
    checks = {
        "source": (
            bool(index.get("source_gate", {}).get("verified_positive_complete")),
            "automation/q218_sec_multichannel_source_gate.py",
            str(index.get("source_gate", {}).get("gate_code_blob_sha") or ""),
        ),
        "event_pair": (
            bool(index.get("event_pair_gate", {}).get("verified_positive_complete")),
            "automation/q218_sec_event_pair_lineage_gate.py",
            str(index.get("event_pair_gate", {}).get("gate_code_blob_sha") or ""),
        ),
    }
    for gate, (positive, path, expected_sha) in checks.items():
        if not positive or not expected_sha:
            continue
        try:
            actual_sha = subprocess.check_output(
                ["git", "hash-object", path], text=True
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            continue
        if actual_sha == expected_sha:
            out.add(gate)
    return out


def q218_independent_reproduction_current() -> bool:
    try:
        receipt = json.loads(
            Path("research/evidence/q218_independent_architecture_pit_reproduction_latest.json")
            .read_text(encoding="utf-8")
        )
        index = json.loads(Q218_GATE_INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        receipt.get("status") == "Q218_INDEPENDENT_ARCHITECTURE_PIT_REPRODUCED"
        and receipt.get("upstream_receipts", {}).get("source_receipt_fingerprint")
        == index.get("source_gate", {}).get("receipt_fingerprint")
        and receipt.get("upstream_receipts", {}).get("event_pair_receipt_fingerprint")
        == index.get("event_pair_gate", {}).get("receipt_fingerprint")
    )


Q218_INDEPENDENT_WORKFLOW = ".github/workflows/q218-independent-architecture-pit-reproduction.yml"
Q218_GATE_NAMES = {"source", "event_pair"}


def gate_files_unchanged_since_run(run: dict[str, Any], gate: str) -> bool:
    """Fail closed unless the relevant Q218 gate implementation is unchanged."""
    head_sha = str(run.get("head_sha") or "")
    if not head_sha:
        return False
    if gate == "source":
        paths = ["automation/q218_sec_multichannel_source_gate.py"]
    elif gate == "event_pair":
        paths = ["automation/q218_sec_event_pair_lineage_gate.py"]
    else:
        return False
    try:
        proc = subprocess.run(
            ["git", "diff", "--quiet", head_sha, "HEAD", "--", *paths],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return proc.returncode == 0


def completed_q218_gates_for_current_context(runs: list[dict[str, Any]]) -> set[str]:
    # The immutable positive receipt index is the authoritative current-context
    # completion signal. This avoids shallow-clone/git-diff ambiguity and stops
    # phase-successful Q218 source/event gates from being dispatched again.
    indexed = q218_positive_gate_index_current()
    if indexed:
        return indexed
    out: set[str] = set()
    for run in runs:
        if not isinstance(run, dict) or run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        title = " ".join(str(run.get(key) or "") for key in ("name", "display_title", "run_name"))
        if "Top-4 Slot " not in title or "Q218" not in title:
            continue
        parts = title.split("Top-4 Slot ", 1)[1].strip().split()
        if len(parts) < 3 or parts[2] not in Q218_GATE_NAMES:
            continue
        if gate_files_unchanged_since_run(run, parts[2]):
            out.add(parts[2])
    return out
