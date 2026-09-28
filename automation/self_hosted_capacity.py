"""Detect and safely start an already-configured secondary Windows Actions runner."""
from __future__ import annotations
import json, os, subprocess
from pathlib import Path
from typing import Any

def candidate_roots() -> list[Path]:
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    preferred = [home/"actions-runner-2", home/"actions-runner-02", home/"actions-runner-secondary", home/"actions-runner-1"]
    roots = []
    for root in preferred:
        if root not in roots: roots.append(root)
    try:
        for root in sorted(home.glob("actions-runner-*")):
            if root.is_dir() and root not in roots: roots.append(root)
    except OSError:
        pass
    return roots

def configured_secondary_roots(primary: Path | None = None) -> list[Path]:
    primary = primary or Path(os.environ.get("USERPROFILE", str(Path.home()))) / "actions-runner"
    return [root for root in candidate_roots()
            if root.resolve() != primary.resolve()
            and (root/".runner").is_file()
            and (root/"run.cmd").is_file()
            and (root/"bin"/"Runner.Listener.exe").is_file()]

def listener_processes() -> list[dict[str, Any]]:
    try:
        raw = subprocess.check_output([
            "powershell.exe","-NoProfile","-NonInteractive","-Command",
            "Get-CimInstance Win32_Process -Filter \"Name='Runner.Listener.exe'\" | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress"
        ], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return []
    if not raw: return []
    data = json.loads(raw)
    return [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])

def is_running(root: Path, processes: list[dict[str, Any]]) -> bool:
    needle = str(root.resolve()).lower().replace("\\", "/")
    return any(
        needle in " ".join(str(p.get(k, "")).lower().replace("\\", "/") for k in ("ExecutablePath","CommandLine"))
        for p in processes
    )

def launch(root: Path) -> None:
    ps = (
        "$root = [IO.Path]::GetFullPath('"
        + str(root).replace("'", "''")
        + "'); $cmd = Join-Path $root 'run.cmd'; "
        + "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c',('\"' + $cmd + '\"') "
        + "-WorkingDirectory $root -WindowStyle Hidden"
    )
    subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",ps], check=True)

def probe() -> dict[str, Any]:
    primary = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "actions-runner"
    before = listener_processes()
    configured = configured_secondary_roots(primary)
    running, launched = [], []
    for root in configured:
        if is_running(root, before):
            running.append(str(root))
        else:
            launch(root); launched.append(str(root))
    return {
        "schema_version": 1,
        "primary_root": str(primary),
        "configured_secondary_runners": [str(p) for p in configured],
        "already_running_secondary_runners": running,
        "launched_secondary_runners": launched,
        "runner_listener_process_count_before": len(before),
        "source_repository": os.environ.get("GITHUB_REPOSITORY"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
    }

if __name__ == "__main__":
    print(json.dumps(probe(), ensure_ascii=False, indent=2))
