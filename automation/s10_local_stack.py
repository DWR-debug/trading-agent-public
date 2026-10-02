"""Bounded local S10 inference-stack bootstrap.

This helper only touches loopback services and operator-local cache paths.
It may reuse an existing llama.cpp server/bridge, or install the official
llama.cpp Ubuntu ARM64 CPU binary and the fixed Qwen2.5-1.5B-Instruct Q4_K_M
GGUF model when they are absent. No credentials, remote trading endpoints or
research evidence are touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

HOST = "127.0.0.1"
LLAMA_PORT = 8080
BRIDGE_PORT = 8765
LLAMA_RELEASE_API = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
HF_MODEL_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/"
    "resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
)
MODEL_FILENAME = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODEL_ID_FALLBACK = "S10-Qwen2.5-1.5B-Instruct-Q4_K_M"
BRIDGE_MODULE = "automation.s10_systemone_bridge"
S10_SEED = int(os.environ.get("S10_SEED", "271828"))
USER_AGENT = "trading-agent-public/S10-local-stack-bootstrap/1"
START_TIMEOUT_SECONDS = 150
MIN_FREE_BYTES_FOR_MODEL = 1_500_000_000


def _urlopen(url: str, *, timeout: int = 30, headers: dict[str, str] | None = None):
    merged = {"User-Agent": USER_AGENT}
    if headers:
        merged.update(headers)
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=merged), timeout=timeout
    )


def _http_get(url: str, timeout: int = 4) -> tuple[int | None, bytes, str | None]:
    try:
        with _urlopen(url, timeout=timeout) as response:
            return response.status, response.read(20000), response.geturl()
    except Exception as exc:
        return None, b"", type(exc).__name__


def _json_get(url: str, timeout: int = 6) -> dict:
    status, body, detail = _http_get(url, timeout)
    if status != 200:
        raise RuntimeError(f"HTTP_GET_FAILED:{status}:{detail}")
    value = json.loads(body.decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("HTTP_JSON_OBJECT_REQUIRED")
    return value


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((HOST, port)) == 0


def _model_ids(base_url: str) -> list[str]:
    try:
        data = _json_get(base_url.rstrip("/") + "/v1/models")
    except Exception:
        return []
    rows = data.get("data")
    if not isinstance(rows, list):
        return []
    return [
        str(row["id"])
        for row in rows
        if isinstance(row, dict) and row.get("id")
    ][:20]


def _safe_extract(tf: tarfile.TarFile, destination: Path) -> None:
    destination = destination.resolve()
    for member in tf.getmembers():
        target = (destination / member.name).resolve()
        if target != destination and destination not in target.parents:
            raise RuntimeError("UNSAFE_TAR_MEMBER")
        if member.issym() or member.islnk():
            raise RuntimeError("UNSAFE_TAR_LINK")
    tf.extractall(destination)


def _arch_suffix() -> str:
    machine = platform.machine().lower()
    if machine in {"aarch64", "arm64"}:
        return "arm64"
    if machine in {"x86_64", "amd64"}:
        return "x64"
    raise RuntimeError(f"UNSUPPORTED_S10_ARCH:{machine}")


def _download(url: str, destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    started = time.monotonic()
    with _urlopen(url, timeout=60, headers={"Accept": "*/*"}) as response:
        with temporary.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
    temporary.replace(destination)
    digest = hashlib.sha256()
    with destination.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "url": url,
        "path": str(destination),
        "bytes": destination.stat().st_size,
        "sha256": digest.hexdigest(),
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def _ensure_model(cache_dir: Path) -> tuple[Path, dict]:
    model = cache_dir / "models" / MODEL_FILENAME
    usage = shutil.disk_usage(cache_dir)
    if model.exists() and model.stat().st_size > 100_000_000:
        return model, {"source": "cache", "path": str(model), "bytes": model.stat().st_size}
    if usage.free < MIN_FREE_BYTES_FOR_MODEL:
        raise RuntimeError(
            f"S10_INSUFFICIENT_DISK_FOR_MODEL:{usage.free}<{MIN_FREE_BYTES_FOR_MODEL}"
        )
    info = _download(HF_MODEL_URL, model)
    info["source"] = "qwen_hf_official_model_repository"
    return model, info


def _ensure_llama_server(cache_dir: Path) -> tuple[Path, dict]:
    found = shutil.which("llama-server")
    if found:
        return Path(found), {"source": "PATH", "path": found}

    bin_dir = cache_dir / "bin"
    candidates = list(bin_dir.rglob("llama-server"))
    if candidates:
        candidates.sort()
        return candidates[0], {"source": "cache", "path": str(candidates[0])}

    release = _json_get(LLAMA_RELEASE_API, timeout=10)
    tag = str(release.get("tag_name", "")).strip()
    assets = release.get("assets")
    if not tag or not isinstance(assets, list):
        raise RuntimeError("S10_LLAMA_RELEASE_METADATA_INVALID")

    suffix = _arch_suffix()
    marker = f"-bin-ubuntu-{suffix}.tar.gz"
    asset = next(
        (
            item
            for item in assets
            if isinstance(item, dict)
            and str(item.get("name", "")).endswith(marker)
            and item.get("browser_download_url")
        ),
        None,
    )
    if not asset:
        raise RuntimeError(f"S10_LLAMA_RELEASE_ASSET_MISSING:{marker}")

    archive = cache_dir / "downloads" / str(asset["name"])
    if not archive.exists():
        _download(str(asset["browser_download_url"]), archive)

    extract_root = cache_dir / "llama_cpp" / tag
    extract_root.mkdir(parents=True, exist_ok=True)
    marker_file = extract_root / ".extracted"
    if not marker_file.exists():
        with tarfile.open(archive, "r:gz") as tf:
            _safe_extract(tf, extract_root)
        marker_file.write_text(tag + "\n", encoding="utf-8")
    candidates = list(extract_root.rglob("llama-server"))
    if not candidates:
        raise RuntimeError("S10_LLAMA_SERVER_BINARY_NOT_FOUND_AFTER_EXTRACT")
    candidates.sort()
    return candidates[0], {
        "source": "official_llama_cpp_release",
        "tag": tag,
        "asset": str(asset["name"]),
        "path": str(candidates[0]),
    }


def _wait_for_models(timeout: int = START_TIMEOUT_SECONDS) -> list[str]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ids = _model_ids(f"http://{HOST}:{LLAMA_PORT}")
        if ids:
            return ids
        time.sleep(2)
    return []


def _start_llama(binary: Path, model: Path, log_dir: Path) -> dict:
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout = (log_dir / "llama-server.stdout.log").open("ab")
    stderr = (log_dir / "llama-server.stderr.log").open("ab")
    command = [
        str(binary),
        "--host", HOST,
        "--port", str(LLAMA_PORT),
        "--model", str(model),
        "--ctx-size", "2048",
        "--parallel", "1",
        "--batch-size", "256",
        "--ubatch-size", "128",
        "--threads", str(min(4, os.cpu_count() or 4)),
        "--seed", str(S10_SEED),
    ]
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        start_new_session=True,
        close_fds=True,
    )
    return {"pid": process.pid, "command": command}


def _start_bridge(repo_root: Path, log_dir: Path, model_id: str) -> dict:
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout = (log_dir / "s10-bridge.stdout.log").open("ab")
    stderr = (log_dir / "s10-bridge.stderr.log").open("ab")
    env = dict(os.environ)
    env.update(
        {
            "S10_BRIDGE_PORT": str(BRIDGE_PORT),
            "S10_LLAMA_BASE_URL": f"http://{HOST}:{LLAMA_PORT}",
            "S10_MODEL": model_id,
            "S10_SEED": str(S10_SEED),
        }
    )
    process = subprocess.Popen(
        [shutil.which("python3") or "python3", "-m", BRIDGE_MODULE],
        cwd=str(repo_root),
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        env=env,
        start_new_session=True,
        close_fds=True,
    )
    return {"pid": process.pid, "model_id": model_id}


def _wait_bridge(timeout: int = 20) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status, _, _ = _http_get(f"http://{HOST}:{BRIDGE_PORT}/health", timeout=2)
        if status == 200:
            return True
        time.sleep(1)
    return False


def _write_descriptor(path: Path, model_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "enabled": True,
        "mode": "systemone_http",
        "base_url": f"http://{HOST}:{BRIDGE_PORT}",
        "model": model_id,
        "protocol_path": "/v1/systemone",
        "timeout_seconds": 90,
        "source": "automation.s10_local_stack",
    }
    # Descriptor is intentionally rejected by s10_runtime if credential-bearing keys exist.
    # Keep the marker explicit in a non-secret field instead.
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bootstrap(repo_root: Path, descriptor: Path, work_root: Path) -> dict:
    cache_dir = Path.home() / ".cache" / "trading-agent" / "s10"
    log_dir = work_root / "logs"
    result = {
        "schema_version": 1,
        "identity": "S10",
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "formal_evidence_allowed": False,
        "credentials_touched": False,
        "llama": {},
        "bridge": {},
        "model_ids": [],
    }

    llama_base = f"http://{HOST}:{LLAMA_PORT}"
    model_ids = _model_ids(llama_base)
    if not model_ids:
        binary, binary_info = _ensure_llama_server(cache_dir)
        model, model_info = _ensure_model(cache_dir)
        start_info = _start_llama(binary, model, log_dir)
        model_ids = _wait_for_models()
        result["llama"] = {
            "started": True,
            **binary_info,
            "model": model_info,
            "process": start_info,
        }
    else:
        result["llama"] = {"started": False, "source": "existing", "model_ids": model_ids}

    if not model_ids:
        raise RuntimeError("S10_LLAMA_SERVER_DID_NOT_EXPOSE_MODELS")

    result["model_ids"] = model_ids
    model_id = next((x for x in model_ids if "qwen" in x.lower()), model_ids[0])

    bridge_status, _, _ = _http_get(f"http://{HOST}:{BRIDGE_PORT}/health", timeout=2)
    if bridge_status != 200:
        result["bridge"] = {
            "started": True,
            **_start_bridge(repo_root, log_dir, model_id),
        }
        if not _wait_bridge():
            raise RuntimeError("S10_BRIDGE_DID_NOT_START")
    else:
        result["bridge"] = {"started": False, "source": "existing"}

    _write_descriptor(descriptor, model_id)
    result["descriptor"] = str(descriptor)
    result["status"] = "S10_LOCAL_STACK_READY"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--descriptor",
        type=Path,
        default=Path.home() / ".trading-agent" / "s10_interface.json",
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path.home() / ".cache" / "trading-agent" / "s10" / "runs",
    )
    args = parser.parse_args()
    args.work_root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_root = args.work_root / stamp
    run_root.mkdir(parents=True, exist_ok=True)
    try:
        result = bootstrap(args.repo_root.resolve(), args.descriptor.expanduser(), run_root)
    except Exception as exc:
        result = {
            "schema_version": 1,
            "identity": "S10",
            "status": "S10_LOCAL_STACK_BOOTSTRAP_FAILED",
            "error": f"{type(exc).__name__}: {exc}",
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "formal_evidence_allowed": False,
            "credentials_touched": False,
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    receipt = run_root / "bootstrap_receipt.json"
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
