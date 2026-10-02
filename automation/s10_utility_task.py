"""Bounded S10 utility review of immutable OS/governance facts.

This worker uses the local S10 model as an independent QA reader. Its output is
operational review only: it can never be scientific evidence, performance
authorization, candidate selection/ranking, promotion, or live execution.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from automation.s10_runtime import resolve

LABELS = {"SUPPORTED", "REFUTED", "INSUFFICIENT"}
SEED = 271828
CASES = 6


def _loopback(url: object) -> bool:
    if not isinstance(url, str):
        return False
    return urlparse(url).hostname in {"127.0.0.1", "localhost", "::1"} and urlparse(url).scheme in {"http", "https"}


def _request(base_url: str, protocol_path: str, claim: str, evidence: str) -> dict:
    payload = {
        "mode": "utility_review",
        "state": {"claim": claim, "evidence": evidence, "domain": "Trading Agent OS bounded governance QA"},
        "questions": {
            "verdict": {
                "criteria": {
                    "SUPPORTED": "The supplied evidence establishes the claim.",
                    "REFUTED": "The supplied evidence contradicts the claim.",
                    "INSUFFICIENT": "The supplied evidence is not enough to decide the claim.",
                }
            }
        },
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + protocol_path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        body = json.loads(response.read().decode("utf-8"))
    verdict = ((body.get("answers") or {}).get("verdict") or {})
    choice = verdict.get("choice")
    probabilities = verdict.get("probabilities")
    if choice not in LABELS or not isinstance(probabilities, dict) or set(probabilities) != LABELS:
        raise ValueError("INVALID_TYPED_VERDICT")
    return {"choice": choice, "probabilities": probabilities}


def _load(repo_root: Path) -> tuple[dict, dict]:
    os_state = json.loads((repo_root / "ops/trading_agent_os_state.json").read_text(encoding="utf-8"))
    decision = json.loads((repo_root / "research/evidence/decision_basis_latest.json").read_text(encoding="utf-8"))
    return os_state, decision


def build_cases(os_state: dict, decision: dict) -> list[dict]:
    safety = os_state.get("permanent_safety", {})
    s10 = os_state.get("resource_routing", {}).get("s10", {})
    fleet = os_state.get("resource_routing", {}).get("android_phone_fleet", {})
    return [
        {
            "id": "G1",
            "claim": "Live trading is enabled in the Trading Agent OS.",
            "expected": "REFUTED",
            "evidence": f"permanent_safety={json.dumps(safety, sort_keys=True)}",
        },
        {
            "id": "G2",
            "claim": "The S10 worker is allowed to create scientific trading evidence by itself.",
            "expected": "REFUTED",
            "evidence": f"s10_scientific_role={s10.get('scientific_role')}; performance_authorization={s10.get('performance_authorization_allowed', False)}",
        },
        {
            "id": "G3",
            "claim": "The S10 resource is routed only when a valid utility acceptance is present.",
            "expected": "SUPPORTED",
            "evidence": f"routing_contract={s10.get('routing_contract')}; acceptance_status={s10.get('capability_claim')}",
        },
        {
            "id": "G4",
            "claim": "An additional Samsung phone can be used for bounded support after it is online and receipt-gated.",
            "expected": "SUPPORTED",
            "evidence": f"fleet_activation_rule={fleet.get('activation_rule')}; scientific_role={fleet.get('scientific_role')}",
        },
        {
            "id": "G5",
            "claim": "The latest formal performance result already passed the project's full gate set.",
            "expected": "REFUTED",
            "evidence": f"latest_formal_trial={decision.get('scientific_status', {}).get('latest_formal_trial')}; latest_formal_status={decision.get('scientific_status', {}).get('latest_formal_status')}",
        },
        {
            "id": "G6",
            "claim": "The next performance run will pass all scientific gates.",
            "expected": "INSUFFICIENT",
            "evidence": "The decision basis records no authorization for performance and does not contain future outcome information.",
        },
    ]


def run(repo_root: Path) -> dict:
    descriptor = resolve()
    base_url = descriptor.get("base_url")
    protocol_path = descriptor.get("protocol_path")
    result = {
        "schema_version": 1,
        "status": "S10_UTILITY_TASK_UNAVAILABLE",
        "task_id": "S10-UTILITY-GOVERNANCE-2026-10-02",
        "source_commit": os.environ.get("GITHUB_SHA"),
        "runner_name": os.environ.get("RUNNER_NAME"),
        "model": descriptor.get("model"),
        "endpoint": base_url,
        "runtime_contract": {"seed": SEED, "threads": 1, "temperature": 0, "top_k": 1},
        "scientific_evidence": False,
        "performance_authorization": False,
        "candidate_selection": False,
        "candidate_ranking": False,
        "promotion": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "cases": [],
    }
    if not descriptor.get("available") or not _loopback(base_url) or not isinstance(protocol_path, str):
        result["reason"] = str(descriptor.get("status", "S10_UNAVAILABLE"))
        return result

    os_state, decision = _load(repo_root)
    cases = build_cases(os_state, decision)
    outputs = []
    for case in cases:
        try:
            answer = _request(str(base_url), protocol_path, case["claim"], case["evidence"])
            outputs.append({**case, "actual": answer["choice"], "probabilities": answer["probabilities"], "error": None})
        except Exception as exc:
            outputs.append({**case, "actual": None, "probabilities": None, "error": f"{type(exc).__name__}: {exc}"})

    valid = len(outputs) == CASES and all(item["error"] is None for item in outputs)
    result["cases"] = outputs
    result["status"] = "S10_UTILITY_REVIEW_COMPLETED" if valid else "S10_UTILITY_REVIEW_PARTIAL"
    result["summary"] = {
        "n": len(outputs),
        "typed_successes": sum(item["error"] is None for item in outputs),
        "agreement_with_fixed_expectation": sum(item["error"] is None and item["actual"] == item["expected"] for item in outputs),
        "expected_outcomes": {"supported": sum(x["expected"] == "SUPPORTED" for x in outputs), "refuted": sum(x["expected"] == "REFUTED" for x in outputs), "insufficient": sum(x["expected"] == "INSUFFICIENT" for x in outputs)},
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    payload = run(args.repo_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "n": len(payload["cases"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
