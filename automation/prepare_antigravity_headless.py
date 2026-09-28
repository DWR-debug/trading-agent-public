"""Prepare Antigravity CLI settings for bounded headless research workers.

Runs after the Windows bootstrap so it can normalize the PowerShell-5.1 BOM
and add only read-only Git command permissions needed for workspace inspection.
It never overwrites an unreadable settings file.
"""
from __future__ import annotations
import json
from pathlib import Path

READONLY_GIT_RULES = [
    "command(git status)",
    "command(git log)",
    "command(git show)",
    "command(git diff)",
    "command(git ls-files)",
    "command(git grep)",
    "command(git rev-parse)",
    "command(git branch --show-current)",
]

def main() -> int:
    path = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
    if not path.exists():
        print(f"ANTIGRAVITY_SETTINGS_MISSING={path}")
        return 1
    raw = path.read_bytes()
    bom_present = raw.startswith(b"\xef\xbb\xbf")
    if bom_present:
        raw = raw[3:]
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"ANTIGRAVITY_SETTINGS_INVALID={type(exc).__name__}")
        return 1
    if not isinstance(data, dict):
        print("ANTIGRAVITY_SETTINGS_INVALID=not_object")
        return 1
    permissions = data.get("permissions")
    if not isinstance(permissions, dict):
        permissions = {}
        data["permissions"] = permissions
    allow = permissions.get("allow")
    if not isinstance(allow, list):
        allow = []
        permissions["allow"] = allow
    changed = False
    for rule in READONLY_GIT_RULES:
        if rule not in allow:
            allow.append(rule)
            changed = True
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print("ANTIGRAVITY_SETTINGS_NORMALIZED=True")
    print(f"ANTIGRAVITY_SETTINGS_BOM_REMOVED={bom_present}")
    print(f"ANTIGRAVITY_SETTINGS_READONLY_GIT_RULES={len([r for r in READONLY_GIT_RULES if r in allow])}")
    print(f"ANTIGRAVITY_SETTINGS_CHANGED={changed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
