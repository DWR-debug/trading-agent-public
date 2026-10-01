"""Q106 PIT join integrity primitives for Q104 source channels.

Engineering/data-contract layer only. No market performance, asset selection,
holdout use, parameter search or authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def build_acceptance_index(submissions: dict[str, Any]) -> dict[str, datetime]:
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accns = recent.get("accessionNumber", [])
    accepted = recent.get("acceptanceDateTime", [])
    out: dict[str, datetime] = {}
    for i, accn in enumerate(accns):
        if i >= len(accepted) or not accn or not accepted[i]:
            continue
        try:
            out[accn] = parse_ts(str(accepted[i]))
        except ValueError:
            continue
    return out


def lineage_rows(companyfacts: dict[str, Any], acceptance_index: dict[str, datetime]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for namespace, facts in (companyfacts.get("facts") or {}).items():
        if not isinstance(facts, dict):
            continue
        for concept, spec in facts.items():
            if not isinstance(spec, dict):
                continue
            for unit, values in (spec.get("units") or {}).items():
                if not isinstance(values, list):
                    continue
                for row in values:
                    if not isinstance(row, dict):
                        continue
                    accn = row.get("accn")
                    if accn not in acceptance_index:
                        continue
                    rows.append(
                        {
                            "namespace": namespace,
                            "concept": concept,
                            "unit": unit,
                            "accn": accn,
                            "filed": row.get("filed"),
                            "form": row.get("form"),
                            "value": row.get("val"),
                            "accepted_at": acceptance_index[accn].isoformat(),
                        }
                    )
    return rows


def state_at_cutoff(rows: list[dict[str, Any]], cutoff: str) -> list[dict[str, Any]]:
    cutoff_dt = parse_ts(cutoff)
    return [row for row in rows if parse_ts(row["accepted_at"]) <= cutoff_dt]


def treasury_rows_at_cutoff(rows: list[dict[str, Any]], cutoff_date: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("record_date", "")) <= cutoff_date]


def future_mutation_invariant(rows: list[dict[str, Any]], future_rows: list[dict[str, Any]], cutoff: str) -> bool:
    before = state_at_cutoff(rows, cutoff)
    after = state_at_cutoff(rows + future_rows, cutoff)
    return before == after


def treasury_future_invariant(rows: list[dict[str, Any]], future_rows: list[dict[str, Any]], cutoff_date: str) -> bool:
    return treasury_rows_at_cutoff(rows, cutoff_date) == treasury_rows_at_cutoff(rows + future_rows, cutoff_date)


def fingerprint(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run_synthetic() -> dict[str, Any]:
    submissions = {
        "filings": {
            "recent": {
                "form": ["10-Q", "10-Q"],
                "accessionNumber": ["0000001-25-000001", "0000001-25-000002"],
                "acceptanceDateTime": ["2025-04-01T14:00:00.000Z", "2025-07-01T14:00:00.000Z"],
            }
        }
    }
    facts = {
        "facts": {
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {
                        "shares": [
                            {"val": 100, "accn": "0000001-25-000001", "filed": "2025-04-01", "form": "10-Q"},
                            {"val": 110, "accn": "0000001-25-000002", "filed": "2025-07-01", "form": "10-Q"},
                        ]
                    }
                }
            }
        }
    }
    idx = build_acceptance_index(submissions)
    rows = lineage_rows(facts, idx)
    future = [{"namespace": "dei", "concept": "EntityCommonStockSharesOutstanding", "unit": "shares", "accn": "future", "filed": "2025-10-01", "form": "10-Q", "value": 120, "accepted_at": "2025-10-01T14:00:00+00:00"}]
    treasury = [
        {"record_date": "2025-06-10", "auction_date": "2025-06-04", "bid_to_cover_ratio": "3.13"},
    ]
    future_treasury = [
        {"record_date": "2025-07-10", "auction_date": "2025-07-03", "bid_to_cover_ratio": "2.90"},
    ]
    return {
        "sec_acceptance_rows": len(rows),
        "sec_future_mutation_invariant": future_mutation_invariant(rows, future, "2025-08-01T00:00:00Z"),
        "treasury_future_mutation_invariant": treasury_future_invariant(treasury, future_treasury, "2025-06-30"),
        "all_rows_have_publicity_anchor": all(row["accepted_at"] for row in rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/q106_q104_pit_join/result.json"))
    args = parser.parse_args()
    synthetic = run_synthetic()
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-01-106-Q104-PIT-JOIN-INTEGRITY",
        "status": "PIT_JOIN_STRUCTURAL_INTEGRITY_ONLY",
        "synthetic": synthetic,
        "governance": {
            "synthetic_only": True,
            "new_market_data": False,
            "new_backtest": False,
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
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
    result["receipt_fingerprint"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q106_STATUS:", result["status"])
    print("Q106_SYNTHETIC_ALL_PASS:", all(synthetic.values()))
    print("Q106_FINGERPRINT:", result["receipt_fingerprint"])
    return 0 if all(synthetic.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
