"""Q109:N7 deterministic common-holder graph integrity/PIT feasibility.

This stage freezes an unweighted one-mode common-holder degree on the existing
Q107 eight-symbol universe. It performs no performance evaluation or selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from automation.q116_13f_transition_population import (
    DATASETS,
    TARGETS,
    download,
    latest_as_of,
    scan,
)

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 8, 31)


def graph_from_records(records: list[dict], as_of: date) -> dict[str, object]:
    latest = latest_as_of(records, as_of)
    manager_symbols: dict[str, set[str]] = {}
    symbol_managers: dict[str, set[str]] = {symbol: set() for symbol in TARGETS}
    edges: set[tuple[str, str, str]] = set()

    for row in latest.values():
        manager = str(row["manager_cik"])
        symbol = str(row["symbol"])
        manager_symbols.setdefault(manager, set()).add(symbol)
        symbol_managers.setdefault(symbol, set()).add(manager)

    symbol_degree: dict[str, int] = {symbol: 0 for symbol in TARGETS}
    for manager, symbols in sorted(manager_symbols.items()):
        ordered = sorted(symbols)
        for left in ordered:
            for right in ordered:
                if left >= right:
                    continue
                edges.add((manager, left, right))
                symbol_degree[left] += 1
                symbol_degree[right] += 1

    return {
        "as_of": as_of.isoformat(),
        "node_count": len(TARGETS),
        "manager_node_count": len(manager_symbols),
        "common_holder_edge_count": len(edges),
        "manager_symbol_membership_count": sum(len(v) for v in manager_symbols.values()),
        "symbol_manager_counts": {k: len(v) for k, v in sorted(symbol_managers.items())},
        "symbol_connectedness_degree": symbol_degree,
        "edge_examples": [
            {"manager_cik": m, "symbol_a": a, "symbol_b": b}
            for m, a, b in sorted(edges)[:25]
        ],
    }


def validate_snapshot(records: list[dict]) -> dict[str, object]:
    required = {"manager_cik", "accession", "filing_date", "period_of_report", "security_key", "symbol"}
    missing = []
    keys = set()
    for row in records:
        if not required.issubset(row):
            missing.append(sorted(required - set(row)))
            continue
        if any(row.get(key) in (None, "") for key in required):
            missing.append(["empty_required_field"])
        keys.add((row["manager_cik"], row["period_of_report"], row["security_key"], row["symbol"]))
    if missing:
        raise RuntimeError("N7_REQUIRED_PIT_LINEAGE_MISSING")
    return {
        "record_count": len(records),
        "required_lineage_complete": True,
        "unique_manager_period_security_keys": len(keys),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/q109_n7_common_holder_graph/result.json"))
    args = parser.parse_args()

    prior = scan(download(DATASETS["prior"]), "prior")
    current = scan(download(DATASETS["current"]), "current")
    prior_snapshot = list(latest_as_of(prior["records"], AS_OF).values())
    current_snapshot = list(latest_as_of(current["records"], AS_OF).values())
    prior_validation = validate_snapshot(prior_snapshot)
    current_validation = validate_snapshot(current_snapshot)
    baseline = graph_from_records(current_snapshot, AS_OF)

    future = list(current_snapshot)
    future.append({
        **current["records"][0],
        "accession": "FUTURE-N7-001",
        "filing_date": "2026-12-01",
        "period_of_report": "30-SEP-2026",
    })
    mutated = graph_from_records(future, AS_OF)
    if baseline != mutated:
        raise RuntimeError("N7_FUTURE_MUTATION_FAILED")

    result = {
        "schema_version": 1,
        "task_id": "Q-2026-10-02-109-N7-COMMON-HOLDER-GRAPH-INTEGRITY",
        "status": "N7_GRAPH_INTEGRITY_AND_PIT_FEASIBILITY_COMPLETED",
        "frozen_metric": "unweighted_one_mode_common_holder_degree",
        "frozen_universe": sorted(TARGETS),
        "as_of": AS_OF.isoformat(),
        "datasets": DATASETS,
        "prior_validation": prior_validation,
        "current_validation": current_validation,
        "graph": baseline,
        "future_mutation_invariance": True,
        "governance": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "promotion": False,
            "performance_authorized": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("N7_STATUS=" + result["status"])
    print("N7_EDGES=" + str(baseline["common_holder_edge_count"]))
    print("N7_RECEIPT_FINGERPRINT=" + result["receipt_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
