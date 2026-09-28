"""Bounded local AI smoke test for the trusted Windows research runner.

This test verifies that an already authenticated local AI CLI can answer a
non-sensitive prompt without workspace writes. It records only operational
metadata and never treats the response as scientific evidence.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path


TIMEOUT_SECONDS = 90


def _find(*names: str) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def _g1_disabled() -> tuple[bool, str, object | None, str | None]:
    home = Path(os.environ.get("USERPROFILE", str(Path.home())))
    path = home / ".gemini" / "antigravity-cli" / "settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, str(path), None, type(exc).__name__
    for key in ("UseG1Credits", "useG1Credits"):
        if key in data:
            value = data[key]
            if value is False or (isinstance(value, str) and value.strip().lower() == "false"):
                return True, str(path), value, None
            return False, str(path), value, None
    return False, str(path), None, "MISSING_KEY"


def _run(cmd: list[str], timeout: int = TIMEOUT_SECONDS) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=os.environ.copy(),
    )


def main() -> int:
    agy = _find("agy")
    gemini = _find("gemini")
    result = {
        "schema_version": 1,
        "runner_name": os.environ.get("RUNNER_NAME"),
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "worker_output_is_scientific_evidence": False,
        "provider": None,
        "status": None,
        "binary": None,
        "version": None,
        "g1_fallback_disabled": False,
    }

    if not agy and not gemini:
        result["status"] = "SKIPPED_NO_GEMINI_CLI"
        print(json.dumps(result, sort_keys=True))
        return 0

    binary = agy or gemini
    result["provider"] = "antigravity_cli" if agy else "gemini_cli"
    result["binary"] = binary

    version = _run([binary, "--version"])
    if version.returncode == 0:
        result["version"] = version.stdout.strip().splitlines()[-1][:200] if version.stdout.strip() else None

    if agy:
        disabled, settings_path, g1_value, g1_error = _g1_disabled()
        result["g1_fallback_disabled"] = disabled
        result["g1_setting_value"] = g1_value
        result["g1_settings_error"] = g1_error
        result["settings_path"] = settings_path
        if not disabled:
            result["status"] = "BLOCKED_G1_FALLBACK_NOT_DISABLED"
            print(json.dumps(result, sort_keys=True))
            return 2
        command = [
            binary,
            "--print-timeout",
            "45s",
            "--output-format",
            "json",
            "-p",
            "Respond exactly with LOCAL_AI_READY and nothing else.",
        ]
    else:
        command = [
            binary,
            "--approval-mode",
            "plan",
            "--output-format",
            "json",
            "--prompt",
            "Respond exactly with LOCAL_AI_READY and nothing else.",
        ]

    started = time.monotonic()
    try:
        proc = _run(command, TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        print(json.dumps(result, sort_keys=True))
        return 0

    result["duration_seconds"] = round(time.monotonic() - started, 3)
    result["returncode"] = proc.returncode
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    result["response_marker_present"] = "LOCAL_AI_READY" in stdout
    result["error_marker_present"] = "AGY_ERROR" in stdout or "AGY_ERROR" in stderr

    if proc.returncode == 0 and result["response_marker_present"]:
        result["status"] = "SUCCESS"
    elif result["error_marker_present"]:
        result["status"] = "FAILED_PROVIDER"
    else:
        result["status"] = "FAILED_NO_EXPECTED_RESPONSE"

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
