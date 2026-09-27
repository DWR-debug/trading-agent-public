"""Fail-closed Git scope guard for bounded agent tasks."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

PROTECTED = (".github/", "research/evidence/", "research/authorizations/", "gates/")


def _git(*args: str) -> list[str]:
    output = subprocess.check_output(["git", *args], text=True)
    return [line for line in output.splitlines() if line]


def changed_paths() -> list[str]:
    changed = set(_git("diff", "--name-only"))
    changed.update(_git("diff", "--cached", "--name-only"))
    changed.update(_git("ls-files", "--others", "--exclude-standard"))
    return sorted(changed)


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-3])
    return path == pattern


def validate(contract_path: Path) -> list[str]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    allowed = contract["allowed_paths"]
    changed = changed_paths()
    violations = [
        path
        for path in changed
        if path.startswith(PROTECTED) or not any(_matches(path, pattern) for pattern in allowed)
    ]
    if violations:
        raise SystemExit("AGENT_SCOPE_VIOLATION:" + ",".join(violations))
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    args = parser.parse_args()
    changed = validate(args.contract)
    print("AGENT_SCOPE_OK files=" + str(len(changed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
