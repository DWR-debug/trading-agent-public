"""Sanitized discovery for the dedicated S10 Android/Termux phone.

This script is intentionally discovery-only. It does not call remote services,
does not collect secrets, and does not modify the device.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

SECRET = ("TOKEN", "KEY", "SECRET", "PASSWORD", "PASS", "CREDENTIAL", "AUTH")
CANDIDATES = ("s10", "s10-cli", "s10-agent", "systemone", "system-one")


def run(argv: list[str], timeout: int = 4) -> tuple[int | None, str]:
    try:
        p = subprocess.run(argv, text=True, capture_output=True, timeout=timeout, check=False)
        return p.returncode, ((p.stdout or p.stderr or "").strip())[:1200]
    except Exception as exc:
        return None, type(exc).__name__


def safe_env() -> list[dict[str, str]]:
    out = []
    for key, value in sorted(os.environ.items()):
        upper = key.upper()
        if not upper.startswith("S10_"):
            continue
        if any(token in upper for token in SECRET):
            continue
        if any(token in upper for token in ("URL", "ENDPOINT", "HOST", "PORT", "MODEL", "MODE")):
            out.append({"key": key, "value": value[:300]})
    return out


def main() -> int:
    result = {
        "schema_version": 1,
        "identity": "S10",
        "device_type": "dedicated_android_phone",
        "runtime": "termux",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "prefix": os.environ.get("PREFIX"),
        "home": str(Path.home()),
        "executables": [],
        "process_matches": [],
        "listeners": [],
        "configured_interfaces": safe_env(),
        "memory": {},
        "secrets_collected": False,
    }

    for name in CANDIDATES:
        path = shutil.which(name)
        if path:
            rc, text = run([path, "--version"])
            result["executables"].append({"name": name, "path": path, "returncode": rc, "version": text})

    rc, text = run(["sh", "-lc", "ps -A 2>/dev/null | grep -Ei 's10|system.?one' | grep -v grep | head -30"])
    if rc == 0 and text:
        result["process_matches"] = text.splitlines()[:30]

    rc, text = run(["sh", "-lc", "ss -lnt 2>/dev/null | head -60"])
    if rc == 0 and text:
        result["listeners"] = text.splitlines()[:60]

    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        wanted = ("MemTotal:", "MemAvailable:", "SwapTotal:", "SwapFree:")
        for line in meminfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(wanted):
                parts = line.split()
                if len(parts) >= 2:
                    result["memory"][parts[0].rstrip(":").lower()] = parts[1] + ((" " + parts[2]) if len(parts) > 2 else "")

    result["status"] = (
        "TERMUX_RUNTIME_READY"
        if result["prefix"] and shutil.which("python")
        else "TERMUX_NOT_CONFIRMED"
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
