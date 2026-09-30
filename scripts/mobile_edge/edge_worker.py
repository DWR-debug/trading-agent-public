#!/usr/bin/env python3
"""Minimal paper-only Trading Agent Android edge worker.

The worker never evaluates strategy performance and never touches live trading.
It polls a dedicated GitHub branch for whitelisted tasks and publishes heartbeat
and result JSON there. GitHub token is read from the environment only.
"""
from __future__ import annotations

import base64
import json
import os
import platform
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = os.environ.get("TRADING_AGENT_REPO", "DWR-debug/trading-agent-public")
BRANCH = os.environ.get("TRADING_AGENT_EDGE_BRANCH", "edge-control")
NODE_ID = os.environ["EDGE_NODE_ID"]
TOKEN = os.environ.get("TRADING_AGENT_GITHUB_TOKEN", "")
INTERVAL = int(os.environ.get("EDGE_POLL_SECONDS", "900"))
HEARTBEAT_INTERVAL = int(os.environ.get("EDGE_HEARTBEAT_SECONDS", "21600"))
ROOT = Path(os.environ.get("EDGE_ROOT", Path.home() / ".trading-agent-edge"))
TASK_PATH = f"ops/mobile_edge/tasks/{NODE_ID}.json"
HEARTBEAT_PATH = f"ops/mobile_edge/heartbeats/{NODE_ID}.json"
RESULT_DIR = f"ops/mobile_edge/results/{NODE_ID}"


def api(method: str, path: str, payload: dict | None = None) -> dict | None:
    url = f"https://api.github.com/repos/{REPO}{path}"
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "trading-agent-mobile-edge",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def github_get_file(path: str) -> tuple[dict, str] | None:
    result = api("GET", f"/contents/{path}?ref={BRANCH}")
    if result is None:
        return None
    content = base64.b64decode(result["content"]).decode("utf-8")
    return json.loads(content), result["sha"]


def github_put_file(path: str, obj: dict, existing_sha: str | None, message: str) -> None:
    raw = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
    payload = {
        "message": message,
        "content": base64.b64encode(raw).decode("ascii"),
        "branch": BRANCH,
    }
    if existing_sha:
        payload["sha"] = existing_sha
    for _ in range(5):
        try:
            api("PUT", f"/contents/{path}", payload)
            return
        except urllib.error.HTTPError as exc:
            if exc.code != 409:
                raise
            current = github_get_file(path)
            payload["sha"] = current[1] if current else None
            if payload["sha"] is None:
                payload.pop("sha", None)
            time.sleep(2)
    raise RuntimeError(f"GitHub update conflict did not settle: {path}")


def device_profile() -> dict:
    def prop(name: str) -> str | None:
        try:
            return subprocess.check_output(
                ["getprop", name], text=True, stderr=subprocess.DEVNULL, timeout=5
            ).strip() or None
        except Exception:
            return None

    mem_mb = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                mem_mb = int(line.split()[1]) // 1024
                break
    except Exception:
        pass

    return {
        "node_id": NODE_ID,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "android_model": prop("ro.product.model"),
        "android_release": prop("ro.build.version.release"),
        "cpu_abi": prop("ro.product.cpu.abi"),
        "ram_mb": mem_mb,
    }


def heartbeat(status: str, note: str | None = None) -> None:
    obj = {
        "schema_version": 1,
        "node_id": NODE_ID,
        "status": status,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "device": device_profile(),
    }
    if note:
        obj["note"] = note
    current = github_get_file(HEARTBEAT_PATH)
    github_put_file(
        HEARTBEAT_PATH,
        obj,
        current[1] if current else None,
        f"OPS: mobile edge heartbeat {NODE_ID}",
    )


def run_whitelisted_task(task: dict) -> dict:
    kind = task.get("kind")
    if kind == "health_probe":
        return {"status": "ok", "device": device_profile()}
    if kind == "repo_sync":
        target = ROOT / "repo"
        if not (target / ".git").exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", f"https://github.com/{REPO}.git", str(target)],
                check=True,
                timeout=300,
            )
        else:
            subprocess.run(["git", "-C", str(target), "fetch", "--depth", "1", "origin", "master"],
                           check=True, timeout=120)
        return {"status": "ok", "repo_path": str(target)}
    return {"status": "rejected", "reason": "unsupported_task_kind"}


def main() -> None:
    if not TOKEN:
        raise SystemExit("TRADING_AGENT_GITHUB_TOKEN is required for edge-control writes")
    ROOT.mkdir(parents=True, exist_ok=True)
    last_heartbeat = 0.0
    last_task_fingerprint = None

    while True:
        now = time.time()
        if now - last_heartbeat >= HEARTBEAT_INTERVAL:
            try:
                heartbeat("online")
                last_heartbeat = now
            except Exception as exc:
                print(f"HEARTBEAT_ERROR: {type(exc).__name__}: {exc}", flush=True)

        try:
            task_pair = github_get_file(TASK_PATH)
            if task_pair:
                task, _ = task_pair
                task_fp = json.dumps(task, sort_keys=True, separators=(",", ":"))
                if task_fp != last_task_fingerprint and task.get("enabled") is True:
                    result = {
                        "schema_version": 1,
                        "task_id": task.get("task_id"),
                        "node_id": NODE_ID,
                        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "safety": {
                            "paper_only": True,
                            "live_trading_enabled": False,
                            "orders_enabled": False,
                            "automatic_promotion": False,
                        },
                    }
                    try:
                        result["outcome"] = run_whitelisted_task(task)
                        result["status"] = "completed"
                    except Exception as exc:
                        result["status"] = "failed"
                        result["outcome"] = {"error": f"{type(exc).__name__}: {exc}"}
                    result_path = f"{RESULT_DIR}/{task.get('task_id','unknown')}.json"
                    current_result = github_get_file(result_path)
                    github_put_file(
                        result_path,
                        result,
                        current_result[1] if current_result else None,
                        f"OPS: mobile edge task result {NODE_ID}",
                    )
                    last_task_fingerprint = task_fp
        except Exception as exc:
            print(f"TASK_LOOP_ERROR: {type(exc).__name__}: {exc}", flush=True)

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
