"""Validate Q109 literature frontier as a design-only inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_WAVE = "Q109-2026-10-01"
REQUIRED = 6
FORBIDDEN_TRUE = {
    "performance_authorized",
    "performance_evaluation",
    "holdout_selection",
    "candidate_selection",
    "candidate_ranking",
    "parameter_search",
    "threshold_search",
    "horizon_search",
    "asset_search",
    "variant_search",
    "family_ranking",
    "automatic_promotion",
    "paid_data_required",
}


def fp(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def validate(data: dict[str, Any]) -> dict[str, Any]:
    assert data["wave_id"] == EXPECTED_WAVE
    assert data["status"] == "DESIGN_INVENTORY_ONLY"
    policy = data["policy"]
    assert all(policy.get(k) is not True for k in FORBIDDEN_TRUE)
    candidates = data["candidates"]
    assert isinstance(candidates, list) and len(candidates) == REQUIRED
    ids = []
    for row in candidates:
        assert row["id"].startswith("Q109:")
        assert row["status"] == "DESIGN_ONLY_UNRANKED"
        assert row.get("id") and row.get("name") and row.get("family")
        assert row.get("hypothesis") and row.get("construction")
        assert row.get("sources") and row.get("pit_requirements") and row.get("next_gate")
        assert row.get("id") not in ids
        ids.append(row["id"])
    result = {
        "schema_version": "1.0",
        "wave_id": EXPECTED_WAVE,
        "status": "DESIGN_CONTRACT_VALIDATED",
        "candidate_count": len(candidates),
        "candidate_ids": ids,
        "governance": {
            "performance_authorized": False,
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "family_ranking": False,
            "automatic_promotion": False,
            "paid_data_required": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["contract_fingerprint"] = fp(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("research/frontier/q109_candidate_wave_2026_10_01.json"))
    parser.add_argument("--output", type=Path, default=Path("research/runs/q109_candidate_wave_contract/result.json"))
    args = parser.parse_args()
    result = validate(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Q109_STATUS:", result["status"])
    print("Q109_CANDIDATES:", result["candidate_count"])
    print("Q109_FINGERPRINT:", result["contract_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
