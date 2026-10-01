"""Fail-closed Git scope guard for bounded agent tasks."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from automation.agent_dispatch import (
    AgentDispatchError,
    FORBIDDEN_PATH_PREFIXES,
    validate_scope_paths,
)

PROTECTED = FORBIDDEN_PATH_PREFIXES
SCOPE_VIOLATION_PREFIX = "AGENT_SCOPE_VIOLATION:"


def _git(*args: str) -> list[str]:
    output = subprocess.check_output(
        ["git", "-c", "core.quotePath=true", *args],
        text=True,
    )
    return [line for line in output.splitlines() if line]


def _git_changed_paths(*args: str) -> list[str]:
    fields = subprocess.check_output(["git", *args]).split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(fields) - 1:
        status = fields[index].decode("ascii")
        path_count = 2 if status.startswith(("R", "C")) else 1
        paths.extend(os.fsdecode(path) for path in fields[index + 1 : index + 1 + path_count])
        index += path_count + 1
    return paths


def changed_paths() -> list[str]:
    changed = set(_git("diff", "--name-only"))
    changed.update(_git("diff", "--cached", "--name-only"))
    changed.update(_git("ls-files", "--others", "--exclude-standard"))
    changed.update(_git_changed_paths("diff", "--name-status", "-z"))
    changed.update(_git_changed_paths("diff", "--cached", "--name-status", "-z"))
    return sorted(changed)


def validate(contract_path: Path) -> list[str]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    try:
        return validate_scope_paths(changed_paths(), contract)
    except AgentDispatchError as exc:
        raise SystemExit(SCOPE_VIOLATION_PREFIX + str(exc)) from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    args = parser.parse_args()
    changed = validate(args.contract)
    print("AGENT_SCOPE_OK files=" + str(len(changed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
