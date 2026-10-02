"""Generic operational acceptance for a Samsung/Android phone research worker."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from urllib.parse import urlparse

LABELS = {"SUPPORTED", "REFUTED", "INSUFFICIENT"}
ACCEPTANCE_CONTRACT_VERSION = "2026-10-02-R3"

def loopback(url: object) -> bool:
    if not isinstance(url, str):
        return False
    p = urlparse(url)
    return p.scheme in {"http", "https"} and p.hostname in {"127.0.0.1", "localhost", "::1"}

def evaluate(result: dict) -> tuple[str, dict[str, bool]]:
    rows = result.get("raw_predictions")
    corpus = result.get("corpus") or {}
    metrics = result.get("metrics") or {}
    sensitivity = result.get("option_order_sensitivity") or {}
    runtime = result.get("runtime_contract") or {}
    governance = result.get("governance") or {}
    row_ok = (
        isinstance(rows, list) and len(rows) == 36 and all(
            isinstance(row, dict)
            and row.get("error") is None
            and row.get("predicted_label") in LABELS
            and isinstance(row.get("probabilities"), dict)
            and set(row["probabilities"]) == LABELS
            for row in rows
        )
    )
    order_cases = sensitivity.get("cases")
    order_ok = (
        sensitivity.get("n") == 6
        and isinstance(order_cases, list)
        and len(order_cases) == 6
        and all(isinstance(x, dict) and x.get("error") is None for x in order_cases)
        and sensitivity.get("choice_changes") == 0
        and sensitivity.get("max_probability_delta") == 0
    )
    governance_ok = all(value is False for key, value in governance.items() if key in {
        "performance_evaluation","holdout_selection","candidate_selection",
        "candidate_ranking","parameter_search","promotion","live_execution"
    })
    checks = {
        "benchmark_completed": result.get("status") == "BENCHMARK_COMPLETED",
        "fixed_corpus_36_cases": corpus.get("cases") == 36 and metrics.get("n_total") == 36,
        "all_36_typed_decisions_valid": row_ok,
        "all_36_scored": metrics.get("n_scored") == 36 and metrics.get("malformed_or_no_decision") == 0,
        "option_order_checks_complete": order_ok,
        "loopback_endpoint": loopback(result.get("endpoint")),
        "model_present": isinstance(result.get("model"), str) and bool(result.get("model").strip()),
        "source_commit_present": isinstance((result.get("environment") or {}).get("source_commit"), str) and bool((result.get("environment") or {}).get("source_commit")),
        "governance_fail_closed": governance_ok,
        "not_scientific_evidence": result.get("worker_output_is_scientific_evidence") is False,
        "deterministic_runtime_contract": runtime == {"seed":271828,"threads":1,"temperature":0,"top_k":1},
    }
    return ("ANDROID_PHONE_UTILITY_ACCEPTED" if all(checks.values()) else "ANDROID_PHONE_UTILITY_NOT_ACCEPTED"), checks

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--resource-id", required=True)
    ap.add_argument("--runner-name", default="")
    args = ap.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    result["runtime_contract"] = {"seed":271828,"threads":1,"temperature":0,"top_k":1}
    status, checks = evaluate(result)
    receipt = {
        "schema_version": 1,
        "receipt_type": "android_phone_operational_utility_acceptance",
        "resource_id": args.resource_id,
        "runner_name": args.runner_name or (result.get("environment") or {}).get("runner_name"),
        "acceptance_contract_version": ACCEPTANCE_CONTRACT_VERSION,
        "status": status,
        "result_sha256": hashlib.sha256(args.result.read_bytes()).hexdigest(),
        "source_commit": (result.get("environment") or {}).get("source_commit"),
        "model": result.get("model"),
        "endpoint": result.get("endpoint"),
        "acceptance": {
            "scope": "bounded typed Evidence-Critic worker usability only",
            "checks": checks,
            "scientific_evidence": False,
            "performance_authorization": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "promotion": False
        },
        "governance": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"resource_id":args.resource_id,"status":status,"checks":checks}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
