"""Create the universal pre-formal robustness receipt for Q218.

This delegates to the repository's canonical candidate_robustness_gate and
records only structural, non-performance evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from automation.candidate_robustness_gate import validate_candidate

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/governance/q218_performance_contract_2026_10_08.json"
OUT_DEFAULT = ROOT / "research/evidence/q218_candidate_robustness_latest.json"


def fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def build() -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("candidate_id") != "Q218":
        raise RuntimeError("Q218 contract identity mismatch")
    candidate = {
        "id": "Q218",
        "name": contract["candidate_id"] + " " + contract.get("record_type", ""),
        "hypothesis": contract["universe"]["selection_rule"] + " " + contract["outcome_contract"]["direction"],
        "construction": json.dumps({
            "feature_construction": contract["feature_construction"],
            "event_pair_rules": contract["event_pair_rules"],
        }, sort_keys=True),
        "sources": [
            "https://data.sec.gov/submissions/",
            "https://www.sec.gov/Archives/edgar/data/",
            "https://query1.finance.yahoo.com/v8/finance/chart/",
        ],
        "next_gate": "Q218 frozen performance preparation",
    }
    result = validate_candidate(
        candidate,
        "research/governance/q218_performance_contract_2026_10_08.json",
        "ACTION_ARTIFACT_PENDING",
    )
    if result.get("status") != "PRE_FORMAL_ROBUSTNESS_COMPLETED":
        raise RuntimeError("Q218 universal candidate robustness gate failed")
    result.update({
        "trial_id": contract["trial_id"],
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "performance_evaluation": False,
        "holdout_evaluation": False,
    })
    result["receipt_fingerprint"] = fp(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    receipt = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_id": receipt["candidate_id"],
        "status": receipt["status"],
        "receipt_fingerprint": receipt["receipt_fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
