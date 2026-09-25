"""Fail-closed freshness check for the durable project state.

This check compares the mutable project_state.json against the latest immutable
current_project_checkpoint.json. It never rewrites evidence and never makes a
research or promotion decision.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "research" / "evidence" / "project_state.json"
CHECKPOINT_PATH = ROOT / "research" / "evidence" / "current_project_checkpoint.json"


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"PROJECT STATE FRESHNESS FAIL: missing {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"PROJECT STATE FRESHNESS FAIL: invalid JSON in {path.relative_to(ROOT)}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise SystemExit(
            f"PROJECT STATE FRESHNESS FAIL: {path.relative_to(ROOT)} is not a JSON object"
        )
    return value


def freshness_errors(state: dict[str, Any], checkpoint: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if state.get("repository") != checkpoint.get("repository"):
        errors.append(
            "repository mismatch: "
            f"project_state={state.get('repository')!r}, "
            f"checkpoint={checkpoint.get('repository')!r}"
        )

    state_master = state.get("master_commit")
    checkpoint_master = checkpoint.get("master_commit_at_checkpoint_creation")
    if state_master != checkpoint_master:
        errors.append(
            "master provenance drift: "
            f"project_state.master_commit={state_master!r}, "
            f"checkpoint.master_commit_at_checkpoint_creation={checkpoint_master!r}"
        )

    q016_state = state.get("engineering_notes", {}).get("q016_execution_status")
    q016_scientific = state.get("engineering_notes", {}).get("q016_scientific_status")
    q016_checkpoint = checkpoint.get("q016", {})
    workflow_conclusion = q016_checkpoint.get("workflow_conclusion")
    aggregate_status = q016_checkpoint.get("aggregate_status")

    if workflow_conclusion == "success" and q016_state == "RUNNING":
        errors.append(
            "Q016 execution status is stale: project_state claims RUNNING while "
            "current_project_checkpoint records workflow_conclusion=success "
            f"(workflow_run_id={q016_checkpoint.get('workflow_run_id')})"
        )

    if aggregate_status and q016_scientific == "NO_RESULT_YET" and aggregate_status != "NO_RESULT_YET":
        errors.append(
            "Q016 scientific status is stale: project_state claims NO_RESULT_YET while "
            f"current_project_checkpoint records aggregate_status={aggregate_status!r} "
            f"(result_fingerprint={q016_checkpoint.get('result_fingerprint')})"
        )

    if checkpoint.get("safety") != {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }:
        errors.append("checkpoint safety contract is not the required paper-only invariant")

    if not checkpoint.get("generated_at_utc"):
        errors.append("checkpoint is missing generated_at_utc")

    return errors


def main() -> None:
    state = _load(STATE_PATH)
    checkpoint = _load(CHECKPOINT_PATH)
    errors = freshness_errors(state, checkpoint)
    if errors:
        print("PROJECT STATE FRESHNESS FAIL")
        for error in errors:
            print(f"- {error}")
        print(
            "reference="
            f"{CHECKPOINT_PATH.relative_to(ROOT)}"
        )
        raise SystemExit(1)

    print("PROJECT STATE FRESHNESS OK")
    print(f"checkpoint_generated_at={checkpoint['generated_at_utc']}")
    print(f"checkpoint_master={checkpoint['master_commit_at_checkpoint_creation']}")
    if checkpoint.get("q016"):
        print(
            "q016="
            f"{checkpoint['q016'].get('workflow_conclusion')}/"
            f"{checkpoint['q016'].get('aggregate_status')}"
        )


if __name__ == "__main__":
    main()
