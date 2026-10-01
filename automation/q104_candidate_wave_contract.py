"""Validate the Q104 candidate wave as a design-only research contract.

No market data are fetched and no performance or candidate selection occurs.
The validator exists to keep the frontier inventory machine-checkable before
any later source/PIT work is authorized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_WAVE = "Q104-2026-10-01"
REQUIRED_COUNT = 6
FORBIDDEN_TRUE = {
    "performance_authorized",
    "holdout_selection_allowed",
    "parameter_search_allowed",
    "asset_search_allowed",
    "threshold_search_allowed",
    "horizon_search_allowed",
    "family_ranking_allowed",
    "automatic_promotion",
    "paid_data_required",
}


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Q104_NOT_OBJECT")
    return data


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("wave_id") != EXPECTED_WAVE:
        raise ValueError("Q104_WAVE_ID_MISMATCH")
    if data.get("status") != "DESIGN_INVENTORY_ONLY":
        raise ValueError("Q104_STATUS_NOT_DESIGN_ONLY")
    policy = data.get("policy")
    if not isinstance(policy, dict):
        raise ValueError("Q104_POLICY_MISSING")
    violations = [key for key in FORBIDDEN_TRUE if policy.get(key) is True]
    if violations:
        raise ValueError("Q104_FORBIDDEN_POLICY_TRUE:" + ",".join(sorted(violations)))
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != REQUIRED_COUNT:
        raise ValueError("Q104_CANDIDATE_COUNT_MISMATCH")
    ids = []
    rows = []
    for row in candidates:
        if not isinstance(row, dict):
            raise ValueError("Q104_CANDIDATE_NOT_OBJECT")
        cid = row.get("id")
        for field in ("id", "name", "family", "hypothesis", "construction", "sources", "pit_requirements", "next_gate"):
            if not row.get(field):
                raise ValueError(f"Q104_REQUIRED_FIELD_MISSING:{field}")
        if not isinstance(cid, str) or not cid.startswith("Q104:"):
            raise ValueError("Q104_CANDIDATE_ID_INVALID")
        if row.get("status") != "DESIGN_ONLY_UNRANKED":
            raise ValueError(f"Q104_CANDIDATE_STATUS_INVALID:{cid}")
        if row.get("performance_authorized") is not False:
            raise ValueError(f"Q104_CANDIDATE_AUTHORIZATION_INVALID:{cid}")
        ids.append(cid)
        rows.append({"id": cid, "name": row["name"], "next_gate": row["next_gate"]})
    if len(set(ids)) != len(ids):
        raise ValueError("Q104_DUPLICATE_CANDIDATE_ID")
    result = {
        "schema_version": "1.0",
        "wave_id": EXPECTED_WAVE,
        "status": "DESIGN_CONTRACT_VALIDATED",
        "candidate_count": len(rows),
        "candidates": rows,
        "governance": {
            "new_market_data": False,
            "new_backtest": False,
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "gate_change": False,
            "performance_authorization": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["contract_fingerprint"] = _fingerprint(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("research/frontier/q104_candidate_wave_2026_10_01.json"))
    parser.add_argument("--output", type=Path, default=Path("research/runs/q104_candidate_wave_contract/result.json"))
    args = parser.parse_args()
    result = validate(_load(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q104_STATUS:", result["status"])
    print("Q104_CANDIDATES:", result["candidate_count"])
    print("Q104_FINGERPRINT:", result["contract_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
