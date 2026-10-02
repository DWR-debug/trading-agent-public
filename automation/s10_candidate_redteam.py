"""Bounded S10 red-team review of quarantined candidate contracts.

This lane reviews only the current hypothesis/design metadata. Its output is
operational/adversarial input, never scientific evidence, authorization,
selection, ranking, promotion or trading logic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import time
import urllib.request
from pathlib import Path
from typing import Any

from automation.research_hypothesis_compiler import compile_inventories
from automation.s10_runtime import resolve

LABELS = ("SUPPORTED", "REFUTED", "INSUFFICIENT")
INVENTORIES = (
    "research/frontier/q104_candidate_wave_2026_10_01.json",
    "research/frontier/q109_candidate_wave_2026_10_01.json",
    "research/frontier/q123_candidate_wave_2026_10_02.json",
)


def _request(endpoint: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse(payload: dict[str, Any]) -> tuple[str | None, dict[str, float]]:
    verdict = ((payload.get("answers") or {}).get("verdict") or {})
    choice = verdict.get("choice")
    probs = verdict.get("probabilities") or {}
    if choice not in LABELS or not isinstance(probs, dict) or set(probs) != set(LABELS):
        raise ValueError("S10_REDTEAM_TYPED_RESPONSE_INVALID")
    normalized = {label: float(probs[label]) for label in LABELS}
    if any(v < 0 or v > 1 for v in normalized.values()) or abs(sum(normalized.values()) - 1.0) > 0.05:
        raise ValueError("S10_REDTEAM_PROBABILITY_CONTRACT_INVALID")
    return choice, normalized


def review_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    claim = (
        "The supplied candidate entry contains a sufficiently explicit and "
        "deterministic research contract to enter only its stated next gate, "
        "without introducing hidden outcome-dependent choices."
    )
    evidence = json.dumps(candidate, ensure_ascii=False, sort_keys=True)
    return {
        "state": {
            "claim": claim,
            "evidence": evidence,
            "domain": "quarantined research-candidate contract review",
        },
        "questions": {
            "verdict": {
                "criteria": {
                    "SUPPORTED": "The candidate entry is explicit enough for the stated next feasibility gate.",
                    "REFUTED": "The candidate entry contains a material contract ambiguity or hidden degree of freedom.",
                    "INSUFFICIENT": "The entry cannot yet be judged reliably without additional source/PIT contract detail.",
                }
            }
        },
    }


def review_candidates(endpoint: str, candidates: list[dict[str, Any]], timeout: int) -> list[dict[str, Any]]:
    rows = []
    for candidate in candidates:
        started = time.monotonic()
        try:
            choice, probabilities = _parse(
                _request(endpoint.rstrip("/") + "/v1/systemone", review_payload(candidate), timeout)
            )
            error = None
        except Exception as exc:
            choice, probabilities = None, {}
            error = f"{type(exc).__name__}: {exc}"
        rows.append({
            "candidate_id": candidate["id"],
            "family": candidate.get("family"),
            "predicted_contract_status": choice,
            "probabilities": probabilities,
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
            "error": error,
        })
    return rows


def build_result(repo_root: Path, output: Path) -> dict[str, Any]:
    descriptor = resolve()
    if not descriptor.get("available"):
        return {
            "schema_version": 1,
            "task_id": "S10-CANDIDATE-REDTEAM-2026-10-02",
            "status": "SKIPPED_S10_UNAVAILABLE",
            "source_commit": os.environ.get("GITHUB_SHA"),
            "runner_name": os.environ.get("RUNNER_NAME"),
            "model": descriptor.get("model"),
            "worker_output_is_scientific_evidence": False,
            "governance": {
                "performance_evaluation": False,
                "holdout_selection": False,
                "candidate_selection": False,
                "candidate_ranking": False,
                "promotion": False,
                "live_execution": False,
            },
        }

    inventories = [repo_root / path for path in INVENTORIES]
    bundle = compile_inventories(inventories)
    candidates = bundle["candidates"]
    endpoint = str(descriptor["base_url"]).rstrip("/") + str(descriptor["protocol_path"])
    rows = review_candidates(endpoint, candidates, int(descriptor.get("timeout_seconds", 180)))
    errors = sum(row["error"] is not None for row in rows)

    result = {
        "schema_version": 1,
        "task_id": "S10-CANDIDATE-REDTEAM-2026-10-02",
        "status": "S10_CANDIDATE_REDTEAM_COMPLETED" if errors == 0 else "S10_CANDIDATE_REDTEAM_PARTIAL",
        "model": descriptor.get("model"),
        "endpoint": descriptor.get("base_url"),
        "protocol_path": descriptor.get("protocol_path"),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "runner_name": os.environ.get("RUNNER_NAME"),
        "runner_arch": platform.machine(),
        "candidate_bundle_fingerprint": bundle["bundle_fingerprint"],
        "candidate_count": len(candidates),
        "reviewed_count": len(rows),
        "error_count": errors,
        "reviews": rows,
        "review_scope": "contract ambiguity / next-gate readiness only",
        "worker_output_is_scientific_evidence": False,
        "governance": {
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_result(args.repo_root.resolve(), args.output)
    print(json.dumps({
        "status": result["status"],
        "candidate_count": result.get("candidate_count", 0),
        "reviewed_count": result.get("reviewed_count", 0),
        "error_count": result.get("error_count", 0),
        "receipt_fingerprint": result.get("receipt_fingerprint"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
