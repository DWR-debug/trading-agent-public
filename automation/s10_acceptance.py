"""Deterministic operational acceptance for the isolated S10 Evidence-Critic run.

This module answers only: "Did S10 complete the fixed technical benchmark with
a stable typed interface?" It never evaluates trading performance and never
creates scientific evidence, authorization, ranking, selection or promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

LABELS = {"SUPPORTED", "REFUTED", "INSUFFICIENT"}
REQUIRED_FALSE_GOVERNANCE = (
    "performance_evaluation",
    "holdout_selection",
    "candidate_selection",
    "candidate_ranking",
    "parameter_search",
    "promotion",
    "live_execution",
)


def _loopback(url: object) -> bool:
    if not isinstance(url, str):
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {"127.0.0.1", "localhost", "::1"}


def evaluate(result: dict) -> tuple[str, dict[str, bool]]:
    rows = result.get("raw_predictions")
    corpus = result.get("corpus") or {}
    metrics = result.get("metrics") or {}
    sensitivity = result.get("option_order_sensitivity") or {}
    environment = result.get("environment") or {}
    governance = result.get("governance") or {}

    row_contract_ok = (
        isinstance(rows, list)
        and len(rows) == 36
        and all(
            isinstance(row, dict)
            and row.get("error") is None
            and row.get("predicted_label") in LABELS
            and isinstance(row.get("probabilities"), dict)
            and set(row["probabilities"]) == LABELS
            for row in rows
        )
    )
    order_cases = sensitivity.get("cases")
    order_checks_ok = (
        sensitivity.get("n") == 6
        and isinstance(order_cases, list)
        and len(order_cases) == 6
        and all(isinstance(case, dict) and case.get("error") is None for case in order_cases)
        and sensitivity.get("choice_changes") == 0
        and isinstance(sensitivity.get("max_probability_delta"), (int, float))
    )
    governance_ok = all(governance.get(key) is False for key in REQUIRED_FALSE_GOVERNANCE)
    checks = {
        "benchmark_completed": result.get("status") == "BENCHMARK_COMPLETED",
        "fixed_corpus_36_cases": corpus.get("cases") == 36 and metrics.get("n_total") == 36,
        "all_36_typed_decisions_valid": row_contract_ok,
        "all_36_scored": metrics.get("n_scored") == 36 and metrics.get("malformed_or_no_decision") == 0,
        "option_order_checks_complete": order_checks_ok,
        "loopback_endpoint": _loopback(result.get("endpoint")),
        "source_commit_present": isinstance(environment.get("source_commit"), str) and bool(environment.get("source_commit")),
        "governance_fail_closed": governance_ok,
        "not_scientific_evidence": result.get("worker_output_is_scientific_evidence") is False,
    }
    return ("S10_UTILITY_ACCEPTED" if all(checks.values()) else "S10_UTILITY_NOT_ACCEPTED"), checks


def build_receipt(result_path: Path) -> dict:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    status, checks = evaluate(result)
    digest = hashlib.sha256(result_path.read_bytes()).hexdigest()
    return {
        "schema_version": 1,
        "receipt_type": "s10_operational_utility_acceptance",
        "task_id": result.get("task_id", "ECL-2026-10-01-001-S10"),
        "status": status,
        "result_sha256": digest,
        "source_commit": (result.get("environment") or {}).get("source_commit", result.get("source_commit")),
        "runner_name": (result.get("environment") or {}).get("runner_name", result.get("runner_name")),
        "model": result.get("model"),
        "endpoint": result.get("endpoint"),
        "acceptance": {
            "scope": "bounded typed Evidence-Critic worker usability only",
            "checks": checks,
            "scientific_evidence": False,
            "performance_authorization": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "promotion": False,
        },
        "governance": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    receipt = build_receipt(args.result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "checks": receipt["acceptance"]["checks"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
