"""Isolated Evidence-Critic benchmark for Jev-style typed-decision models.

This module never feeds model output into research evidence, gates, authorization,
promotion, trading logic or candidate selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import time
import urllib.request
from pathlib import Path

LABELS = ("SUPPORTED", "REFUTED", "INSUFFICIENT")
SUBSTANTIVE = LABELS
CRITERIA = {
    "SUPPORTED": "The supplied evidence establishes the claim.",
    "REFUTED": "The supplied evidence contradicts the claim.",
    "INSUFFICIENT": "The supplied evidence is not enough to decide the claim.",
}

def load_cases(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("empty benchmark corpus")
    if {r.get("gold_label") for r in rows} != set(LABELS):
        raise ValueError("unexpected benchmark labels")
    return rows

def post_json(url: str, payload: dict, timeout: int = 90) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def wait_health(base_url: str, timeout_seconds: int = 180) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_error = None
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(base_url.rstrip("/") + "/health", headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_error = str(exc)
            time.sleep(3)
    raise RuntimeError(f"endpoint health timeout: {last_error}")

def question(order: list[str]) -> dict:
    return {
        "type": "choice",
        "instructions": "Judge the claim using only the supplied evidence. Do not use outside knowledge. Abstain when the evidence is insufficient.",
        "criteria": {label: CRITERIA[label] for label in order if label in SUBSTANTIVE},
    }

def request_for(case: dict, order: list[str] | None = None) -> dict:
    order = order or list(SUBSTANTIVE)
    return {
        "state": {
            "claim": case["claim"],
            "evidence": case["evidence"],
            "domain": case["domain"],
        },
        "questions": {"verdict": question(order)},
    }

def parse_answer(payload: dict) -> tuple[str | None, dict[str, float]]:
    answer = ((payload.get("answers") or {}).get("verdict") or {})
    choice = answer.get("choice")
    raw = answer.get("probabilities") or {}
    probs = {}
    if isinstance(raw, dict):
        for label in LABELS:
            value = raw.get(label)
            if isinstance(value, (int, float)) and math.isfinite(float(value)):
                probs[label] = max(0.0, float(value))
    total = sum(probs.values())
    if total > 0:
        probs = {k: v / total for k, v in probs.items()}
    return (choice if isinstance(choice, str) else None), probs

def brier(gold: str, probs: dict[str, float]) -> float | None:
    if any(label not in probs for label in LABELS):
        return None
    return sum((probs[label] - float(label == gold)) ** 2 for label in LABELS)

def metrics(rows: list[dict]) -> dict:
    scored = [r for r in rows if r["predicted_label"] in LABELS]
    accuracy = (
        sum(r["predicted_label"] == r["gold_label"] for r in scored) / len(scored)
        if scored else None
    )
    briers = [r["brier"] for r in scored if r["brier"] is not None]
    calibration = []
    for r in scored:
        p = r["probabilities"].get(r["predicted_label"])
        if isinstance(p, (int, float)):
            calibration.append((float(p), float(r["predicted_label"] == r["gold_label"])))
    ece = None
    if calibration:
        total = len(calibration)
        ece_sum = 0.0
        for i in range(10):
            lo, hi = i / 10, (i + 1) / 10
            bucket = [x for x in calibration if lo <= x[0] < hi or (hi == 1.0 and lo <= x[0] <= hi)]
            if bucket:
                conf = statistics.mean(x[0] for x in bucket)
                acc = statistics.mean(x[1] for x in bucket)
                ece_sum += len(bucket) * abs(conf - acc)
        ece = ece_sum / total
    return {
        "n_total": len(rows),
        "n_scored": len(scored),
        "accuracy": accuracy,
        "brier_mean": statistics.mean(briers) if briers else None,
        "ece_10bin": ece,
        "malformed_or_no_decision": len(rows) - len(scored),
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", type=Path, default=Path("research/benchmarks/evidence_critic_pilot_2026_10_01.jsonl"))
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--option-order-checks", type=int, default=6)
    args = ap.parse_args()

    cases = load_cases(args.corpus)
    health = wait_health(args.endpoint)
    started = time.monotonic()
    rows = []
    for case in cases:
        t0 = time.monotonic()
        try:
            payload = post_json(args.endpoint.rstrip("/") + "/v1/systemone", request_for(case))
            choice, probs = parse_answer(payload)
            error = None
        except Exception as exc:
            choice, probs, error = None, {}, f"{type(exc).__name__}: {exc}"
        rows.append({
            "id": case["id"],
            "gold_label": case["gold_label"],
            "predicted_label": choice,
            "probabilities": probs,
            "confidence": probs.get(choice) if choice else None,
            "brier": brier(case["gold_label"], probs),
            "latency_ms": round((time.monotonic() - t0) * 1000, 2),
            "error": error,
        })

    order_results = []
    for case in cases[:max(0, min(args.option_order_checks, len(cases)))]:
        try:
            c1, p1 = parse_answer(post_json(args.endpoint.rstrip("/") + "/v1/systemone", request_for(case)))
            c2, p2 = parse_answer(post_json(args.endpoint.rstrip("/") + "/v1/systemone", request_for(case, list(reversed(LABELS)))))
            order_results.append({
                "id": case["id"],
                "base_choice": c1,
                "reversed_choice": c2,
                "choice_changed": c1 != c2,
                "max_probability_delta": max(abs(p1.get(label, 0.0) - p2.get(label, 0.0)) for label in LABELS),
            })
        except Exception as exc:
            order_results.append({"id": case["id"], "error": f"{type(exc).__name__}: {exc}"})

    latencies = [r["latency_ms"] for r in rows if r["error"] is None]
    result = {
        "schema_version": 1,
        "task_id": "ECL-2026-10-01-001",
        "status": "BENCHMARK_COMPLETED",
        "model": args.model,
        "endpoint": args.endpoint,
        "health": health,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "runner_name": os.environ.get("RUNNER_NAME"),
            "source_commit": os.environ.get("GITHUB_SHA"),
            "upstream_ref": os.environ.get("ECL_UPSTREAM_REF"),
            "pip_freeze_sha256": (
                hashlib.sha256(Path(os.environ["ECL_PIP_FREEZE"]).read_bytes()).hexdigest()
                if os.environ.get("ECL_PIP_FREEZE") and Path(os.environ["ECL_PIP_FREEZE"]).is_file()
                else None
            ),
        },
        "corpus": {"path": str(args.corpus).replace("\\", "/"), "cases": len(cases), "labels": list(LABELS)},
        "metrics": metrics(rows),
        "latency_ms": {
            "n": len(latencies),
            "median": statistics.median(latencies) if latencies else None,
            "p95": sorted(latencies)[max(0, math.ceil(len(latencies) * 0.95) - 1)] if latencies else None,
        },
        "option_order_sensitivity": {
            "n": len(order_results),
            "choice_changes": sum(x.get("choice_changed") is True for x in order_results),
            "max_probability_delta": max((x.get("max_probability_delta", 0.0) for x in order_results), default=None),
            "cases": order_results,
        },
        "worker_output_is_scientific_evidence": False,
        "governance": {
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "raw_predictions": rows,
        "duration_seconds": round(time.monotonic() - started, 2),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "model": args.model, "metrics": result["metrics"]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
