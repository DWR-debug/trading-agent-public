"""Fail-closed freshness check for the durable project state.

This check compares the mutable project_state.json against the latest immutable
current_project_checkpoint.json. It never rewrites evidence and never makes a
research or promotion decision.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "research" / "evidence" / "project_state.json"
CHECKPOINT_PATH = ROOT / "research" / "evidence" / "current_project_checkpoint.json"
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _verified_master_revision() -> tuple[str, str]:
    event_name = os.environ.get("GITHUB_EVENT_NAME")
    event_path = os.environ.get("GITHUB_EVENT_PATH")

    if event_name == "pull_request":
        if not event_path:
            raise SystemExit("PROJECT STATE FRESHNESS FAIL: GITHUB_EVENT_PATH is missing")
        try:
            event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(
                f"PROJECT STATE FRESHNESS FAIL: cannot read pull request event {event_path}: {exc}"
            ) from exc
        if not isinstance(event, dict):
            raise SystemExit(
                f"PROJECT STATE FRESHNESS FAIL: pull request event {event_path} is not a JSON object"
            )
        pull_request = event.get("pull_request")
        base = pull_request.get("base") if isinstance(pull_request, dict) else None
        revision = base.get("sha") if isinstance(base, dict) else None
        source = "pull_request.base.sha"
    elif os.environ.get("GITHUB_REF") == "refs/heads/master":
        revision = os.environ.get("GITHUB_SHA")
        source = "GITHUB_SHA (master push)"
    else:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "refs/heads/master"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            try:
                result = subprocess.run(
                    ["git", "ls-remote", "origin", "refs/heads/master"],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except (OSError, subprocess.CalledProcessError) as remote_exc:
                raise SystemExit(
                    "PROJECT STATE FRESHNESS FAIL: cannot verify current master revision "
                    "from refs/heads/master or origin/refs/heads/master"
                ) from remote_exc
            remote_refs = []
            for line in result.stdout.splitlines():
                fields = line.split()
                if len(fields) == 2 and fields[1] == "refs/heads/master":
                    remote_refs.append(fields[0])
            revision = remote_refs[0] if len(remote_refs) == 1 else None
            source = "origin/refs/heads/master"
        else:
            revision = result.stdout.strip()
            source = "git refs/heads/master"

    if not isinstance(revision, str) or not GIT_SHA_PATTERN.fullmatch(revision):
        raise SystemExit(
            f"PROJECT STATE FRESHNESS FAIL: invalid current master revision from {source}: "
            f"{revision!r}"
        )
    return revision, source


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


def freshness_errors(
    state: dict[str, Any],
    checkpoint: dict[str, Any],
    verified_master_revision: str | None = None,
    verified_master_source: str = "verified current master",
) -> list[str]:
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

    if verified_master_revision is not None and checkpoint_master != verified_master_revision:
        errors.append(
            "checkpoint repository revision is stale: "
            f"{CHECKPOINT_PATH.relative_to(ROOT)} records "
            f"master_commit_at_checkpoint_creation={checkpoint_master!r}, while "
            f"{verified_master_source} is {verified_master_revision!r}"
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

    q020_state = state.get("q020_performance", {})
    q020_checkpoint = checkpoint.get("q020_performance", {})
    for field in ("status", "workflow_run_id", "artifact_id", "result_fingerprint"):
        checkpoint_value = q020_checkpoint.get(field)
        if checkpoint_value is not None and q020_state.get(field) != checkpoint_value:
            errors.append(
                f"Q020 performance {field} is stale: project_state.q020_performance."
                f"{field}={q020_state.get(field)!r}, while "
                f"current_project_checkpoint.q020_performance.{field}="
                f"{checkpoint_value!r}"
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
    verified_master_revision, verified_master_source = _verified_master_revision()
    errors = freshness_errors(
        state,
        checkpoint,
        verified_master_revision,
        verified_master_source,
    )
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
    print(f"verified_master={verified_master_revision} ({verified_master_source})")
    if checkpoint.get("q016"):
        print(
            "q016="
            f"{checkpoint['q016'].get('workflow_conclusion')}/"
            f"{checkpoint['q016'].get('aggregate_status')}"
        )


if __name__ == "__main__":
    main()
