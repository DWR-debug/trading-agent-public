"""Cross-platform local server launcher for the isolated Evidence-Critic Lab."""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path


def start(model: str, venv: Path, workdir: Path, port: int, stdout: Path, stderr: Path, pidfile: Path) -> int:
    env = os.environ.copy()
    if model == "laya-typed-decisions":
        exe = venv / ("Scripts/laya-serve.exe" if os.name == "nt" else "bin/laya-serve")
        env.update({"LAYA_DEVICE": "cpu", "LAYA_PRELOAD": "1", "LAYA_MODELS": "typed-decisions", "LAYA_PORT": str(port)})
        cmd = [str(exe)]
    elif model == "kev-0.8b":
        exe = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        cmd = [str(exe), "-m", "kev.serve", "--run", "jaredpalmer/kev-0.8b", "--port", str(port)]
    elif model == "jeff":
        exe = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        cmd = [str(exe), "-m", "scripts.jev_clf_server"]
    else:
        raise ValueError(f"unsupported model: {model}")
    stdout.parent.mkdir(parents=True, exist_ok=True)
    with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        proc = subprocess.Popen(
            cmd,
            cwd=str(workdir),
            env=env,
            stdout=out,
            stderr=err,
            creationflags=creationflags,
        )
    pidfile.write_text(str(proc.pid), encoding="utf-8")
    print(f"ECL_SERVER_STARTED model={model} pid={proc.pid} port={port}")
    return 0


def stop(pidfile: Path) -> int:
    if not pidfile.exists():
        return 0
    pid = int(pidfile.read_text(encoding="utf-8").strip())
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"ECL_SERVER_STOPPED pid={pid}")
    except ProcessLookupError:
        pass
    finally:
        pidfile.unlink(missing_ok=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--action", choices=("start", "stop"), required=True)
    ap.add_argument("--model")
    ap.add_argument("--venv", type=Path)
    ap.add_argument("--workdir", type=Path)
    ap.add_argument("--port", type=int)
    ap.add_argument("--stdout", type=Path)
    ap.add_argument("--stderr", type=Path)
    ap.add_argument("--pidfile", type=Path, required=True)
    args = ap.parse_args()
    if args.action == "stop":
        return stop(args.pidfile)
    for name, value in (("model", args.model), ("venv", args.venv), ("workdir", args.workdir), ("port", args.port), ("stdout", args.stdout), ("stderr", args.stderr)):
        if value is None:
            raise SystemExit(f"--{name} is required for start")
    return start(args.model, args.venv, args.workdir, args.port, args.stdout, args.stderr, args.pidfile)


if __name__ == "__main__":
    raise SystemExit(main())
