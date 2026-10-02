"""Bounded S10 throughput probe; never scientific evidence.

Compares the canonical one-thread local server with an isolated multi-thread
llama.cpp server using the same model, seed, prompt and decoding parameters.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import time
import urllib.request
from pathlib import Path


HOST = "127.0.0.1"
BASE_PORT = 8080
PROBE_PORT = 8081
SEED = 271828
CASES = 8
MODEL_FILENAME = "qwen2.5-1.5b-instruct-q4_k_m.gguf"


def post_chat(base_url: str, prompt: str, timeout: int = 120) -> dict:
    payload = {
        "model": "qwen2.5-1.5b-throughput-probe",
        "messages": [
            {"role": "system", "content": "Return only one JSON object."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "seed": SEED,
        "top_k": 1,
        "max_tokens": 48,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_health(base_url: str, timeout: int = 90) -> None:
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(base_url.rstrip("/") + "/health")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(1)
    raise RuntimeError(f"health timeout: {last}")


def one_call(base_url: str, prompt: str) -> float:
    t0 = time.monotonic()
    post_chat(base_url, prompt)
    return (time.monotonic() - t0) * 1000


def probe_mode(base_url: str, label: str) -> dict:
    latencies = []
    first = None
    second = None
    for i in range(CASES):
        prompt = (
            "Classify this bounded operational statement as SUPPORTED, REFUTED, "
            "or INSUFFICIENT. Claim: The runner returned a successful health response. "
            "Evidence: The endpoint returned HTTP 200 with a JSON status object. "
            "Return one JSON object with a choice and three probabilities."
        )
        if i == 0:
            first = post_chat(base_url, prompt)
            t0 = time.monotonic()
            # The first response above is intentionally part of timing only through a
            # second identical call below; keep payload semantics fixed.
            second = post_chat(base_url, prompt)
            latencies.append((time.monotonic() - t0) * 1000 / 1.0)
        else:
            latencies.append(one_call(base_url, prompt))
    repeatable = first == second if first is not None and second is not None else False
    return {
        "label": label,
        "n": len(latencies),
        "median_ms": round(statistics.median(latencies), 2),
        "p95_ms": round(sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)], 2),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "repeatability_same_payload": repeatable,
        "latencies_ms": [round(x, 2) for x in latencies],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--threads", type=int, default=min(8, os.cpu_count() or 1))
    ap.add_argument(
        "--model-path",
        type=Path,
        default=Path.home() / ".cache" / "trading-agent" / "s10" / "models" / MODEL_FILENAME,
    )
    args = ap.parse_args()

    binary = shutil.which("llama-server")
    if not binary:
        raise RuntimeError("LLAMA_SERVER_NOT_FOUND")
    if not args.model_path.is_file():
        raise RuntimeError(f"S10_MODEL_NOT_FOUND:{args.model_path}")
    if args.threads < 2:
        raise RuntimeError("MULTI_THREAD_PROBE_REQUIRES_AT_LEAST_2_THREADS")

    wait_health(f"http://{HOST}:{BASE_PORT}")
    baseline = probe_mode(f"http://{HOST}:{BASE_PORT}", "canonical_threads_1")

    log_dir = args.output.parent / "throughput_probe_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout = (log_dir / "llama_probe.stdout.log").open("wb")
    stderr = (log_dir / "llama_probe.stderr.log").open("wb")
    proc = subprocess.Popen(
        [
            binary,
            "--host", HOST,
            "--port", str(PROBE_PORT),
            "--model", str(args.model_path),
            "--alias", "S10-Qwen2.5-1.5B-throughput-probe",
            "--ctx-size", "2048",
            "--parallel", "1",
            "--threads", str(args.threads),
            "--threads-batch", str(args.threads),
            "--seed", str(SEED),
            "--temp", "0",
            "--top-k", "1",
        ],
        stdout=stdout,
        stderr=stderr,
    )
    try:
        wait_health(f"http://{HOST}:{PROBE_PORT}")
        optimized = probe_mode(f"http://{HOST}:{PROBE_PORT}", f"multi_threads_{args.threads}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        stdout.close()
        stderr.close()

    speedup = (
        baseline["median_ms"] / optimized["median_ms"]
        if optimized["median_ms"] > 0
        else None
    )
    result = {
        "schema_version": 1,
        "status": "S10_THROUGHPUT_PROBE_COMPLETED",
        "model": str(args.model_path),
        "seed": SEED,
        "threads_probe": args.threads,
        "baseline": baseline,
        "optimized": optimized,
        "median_speedup_x": round(speedup, 3) if speedup else None,
        "scientific_evidence": False,
        "performance_authorization": False,
        "candidate_selection": False,
        "candidate_ranking": False,
        "promotion": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "threads_probe": args.threads,
        "baseline_median_ms": baseline["median_ms"],
        "optimized_median_ms": optimized["median_ms"],
        "median_speedup_x": result["median_speedup_x"],
        "repeatable": optimized["repeatability_same_payload"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
