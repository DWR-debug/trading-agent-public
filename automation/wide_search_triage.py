"""Deterministic triage controller for the wide-search research lane.

The controller never computes returns and never touches holdout data. It converts
an ex-ante hypothesis catalog into coverage/pruning actions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from config import settings

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "research" / "exploration" / "hypothesis_catalog_2026_09_25.json"


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _classify(item: dict) -> str:
    if not item.get("fixed_rule"):
        return "PRUNE_NOT_FIXED_EX_ANTE"
    if not item.get("fresh_disjoint_required"):
        return "PRUNE_NO_FRESH_DISJOINT_CONTRACT"
    if item.get("coverage_stage") == "unavailable" or item.get("pit_path") == "missing":
        return "PRUNE_DATA_CONTRACT"
    action = item.get("action")
    if action == "prune_duplicate_family":
        return "PRUNE_DUPLICATE_FAMILY"
    if action == "control_replication_not_new_alpha":
        return "CONTROL_REPLICATION_ONLY"
    if action == "coverage_only_diagnostic":
        return "COVERAGE_DIAGNOSTIC_ONLY"
    return "ADVANCE_TO_COVERAGE"


def run(*, catalog_path: str | Path = DEFAULT_CATALOG, output_path: str | Path = "research/runs/wide_search/hypothesis_triage.json") -> dict:
    if settings.PAPER_ONLY is not True:
        raise RuntimeError("Wide-search triage requires PAPER_ONLY=True")
    if settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Wide-search triage requires LIVE_TRADING_ENABLED=False")
    if settings.ORDERS_ENABLED is not False:
        raise RuntimeError("Wide-search triage requires ORDERS_ENABLED=False")

    catalog = Path(catalog_path)
    if not catalog.is_absolute():
        catalog = ROOT / catalog
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    hypotheses = payload.get("hypotheses", [])
    ids = [item.get("id") for item in hypotheses]
    if len(hypotheses) != 12:
        raise ValueError("Wide-search catalog must contain exactly 12 fixed hypotheses.")
    if len(ids) != len(set(ids)):
        raise ValueError("Wide-search hypothesis IDs must be unique.")

    results = []
    for item in hypotheses:
        results.append({
            "id": item["id"],
            "family": item["family"],
            "classification": _classify(item),
            "data_source": item["data_source"],
            "pit_path": item["pit_path"],
            "coverage_stage": item["coverage_stage"],
            "performance_evaluation": False,
            "holdout_used": False,
            "selection_used": False,
        })

    counts = {}
    for item in results:
        counts[item["classification"]] = counts.get(item["classification"], 0) + 1

    report = {
        "schema_version": "1.0",
        "task_id": "WIDE-SEARCH-ROUND-001",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "catalog_fingerprint": _fingerprint(payload),
        "results": results,
        "counts": counts,
        "next_gate": "Only ADVANCE_TO_COVERAGE items may enter a dedicated coverage run; no item is performance-authorized.",
        "governance": {
            "performance_evaluation": False,
            "oos_evaluation": False,
            "holdout_evaluation": False,
            "selection_used": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    report["fingerprint"] = _fingerprint(report)

    path = Path(output_path)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"task_id": report["task_id"], "counts": counts, "fingerprint": report["fingerprint"]}, sort_keys=True))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--output", default="research/runs/wide_search/hypothesis_triage.json")
    args = parser.parse_args()
    run(catalog_path=args.catalog, output_path=args.output)


if __name__ == "__main__":
    main()
