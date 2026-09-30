"""RCCSM state-routing structural integrity receipt.

This is a synthetic-only gate. It replays the frozen RCCSM structural scenarios
and records a deterministic receipt. No market data, performance labels,
holdout data, optimization, ranking or authorization is involved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from automation.rccsm_synthetic import synthetic_validation


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_receipt() -> dict[str, Any]:
    validation = synthetic_validation()
    status = (
        "RCCSM_STATE_ROUTING_STRUCTURAL_INTEGRITY_PASS"
        if validation["all_structural_expectations_pass"]
        else "RCCSM_STATE_ROUTING_STRUCTURAL_INTEGRITY_FAIL"
    )
    receipt: dict[str, Any] = {
        "schema_version": "1.0",
        "diagnostic_id": "Q103-RCCSM-STATE-ROUTING-INTEGRITY-2026-09-30",
        "status": status,
        "purpose": "Synthetic structural verification of frozen RCCSM routing expectations.",
        "method": {
            "synthetic_only": True,
            "new_market_data": False,
            "new_backtest": False,
            "new_performance_trial": False,
            "uses_returns": False,
            "uses_holdout": False,
            "uses_optimizer": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "performance_authorization": False,
        },
        "validation": validation,
        "next_gate": "RCCSM state-descriptor PIT feasibility audit before any performance consideration.",
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    receipt["receipt_fingerprint"] = _fingerprint(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="research/runs/q103_rccsm_state_routing_integrity/result.json",
    )
    args = parser.parse_args()
    receipt = build_receipt()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q103_STATUS:", receipt["status"])
    print("Q103_FINGERPRINT:", receipt["receipt_fingerprint"])
    return 0 if receipt["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
