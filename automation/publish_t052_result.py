"""Publish T052 result and synchronized canonical state."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

TRIAL_ID = "T-2026-09-27-052"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def publish(result_path: Path, ledger_path: Path, result_doc_path: Path,
            checkpoint_path: Path, state_path: Path, decision_path: Path) -> None:
    result = _load(result_path)
    ledger = _load(ledger_path)
    if result.get("trial_id") != TRIAL_ID or result.get("status") != "COMPLETED":
        raise RuntimeError("T052 result is incomplete or mismatched")
    if result.get("safety") != {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }:
        raise RuntimeError("Unsafe T052 result")
    governance = result.get("governance", {})
    forbidden = (
        "selection_used",
        "parameter_search",
        "asset_search",
        "threshold_search",
        "horizon_search",
        "variant_search",
        "holdout_used_for_selection",
        "automatic_promotion",
    )
    if any(governance.get(key) is True for key in forbidden):
        raise RuntimeError("T052 contains forbidden selection or promotion state")
    trials = ledger.get("trials")
    if not isinstance(trials, list):
        raise RuntimeError("Unsupported ledger schema")
    if any(item.get("trial_id") == TRIAL_ID for item in trials):
        raise RuntimeError("T052 already exists in immutable ledger")

    cells = {}
    for trial_id, universe in result["universes"].items():
        for sleeve in ("trend_sma_50_200", "cs_momentum_12_1_top2"):
            cell = universe[sleeve]
            cells[f"{trial_id}:{sleeve}"] = cell

    all_passed = all(bool(cell["all_gates_passed"]) for cell in cells.values())
    workflow_id = int(os.environ["GITHUB_RUN_ID"])
    attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
    entry = {
        "trial_id": TRIAL_ID,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": "formal_completed",
        "research_family": "fixed_core_strategy_replication",
        "data_scope": {
            "target_common_candles": 3500,
            "research_periods": 2798,
            "holdout_periods": 700,
            "universes": [
                {
                    "trial_id": trial_id,
                    "universe": value["universe"],
                    "snapshot_fingerprint": value["snapshot_fingerprint"],
                }
                for trial_id, value in result["universes"].items()
            ],
            "holdout_used_for_selection": False,
        },
        "search_scope": {
            "raw_trial_count": 1,
            "independent_trial_count": 1,
            "parameter_search": False,
            "threshold_search": False,
            "asset_search": False,
            "variant_search": False,
            "selection_used": False,
            "holdout_used_for_selection": False,
        },
        "selection": {
            "selected": False,
            "selection_method": "No selection; all four pre-specified universe/sleeve cells reported",
        },
        "statistical_evidence": {
            "independent_trial_count": 1,
            "ready": False,
        },
        "outcome": {
            "validation_status": "COMPLETED_FIXED_RULE",
            "scientific_outcome": "EVIDENCE_RECORDED_NO_AUTOMATIC_PROMOTION",
            "workflow_run_id": workflow_id,
            "workflow_run_attempt": attempt,
            "source_master_sha": os.environ["GITHUB_SHA"],
            "result_fingerprint": result["report_fingerprint"],
            "result_document": "docs/trial_052_fixed_core_sleeve_performance_result_2026_09_27.md",
            "result_checkpoint": "research/checkpoints/trial_052_fixed_core_sleeve_performance_2026_09_27.json",
            "cells": cells,
            "all_cells_passed": all_passed,
        },
        "safety": result["safety"],
    }
    trials.append(entry)
    ledger["generated_at"] = datetime.now(timezone.utc).isoformat()
    _write(ledger_path, ledger)

    checkpoint = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source_master_sha": os.environ["GITHUB_SHA"],
        "workflow_run_id": workflow_id,
        "workflow_run_attempt": attempt,
        "result_fingerprint": result["report_fingerprint"],
        "scientific_outcome": "EVIDENCE_RECORDED_NO_AUTOMATIC_PROMOTION",
        "all_cells_passed": all_passed,
        "governance": result["governance"],
        "safety": result["safety"],
        "universes": result["universes"],
    }
    _write(checkpoint_path, checkpoint)

    state = _load(state_path)
    state["updated"] = datetime.now(timezone.utc).date().isoformat()
    state["latest_formal_trial"] = TRIAL_ID
    state["latest_trial_status"] = "EVIDENCE_RECORDED_NO_AUTOMATIC_PROMOTION"
    state["current_preregistered_trial"] = TRIAL_ID
    state["current_trial_status"] = "COMPLETED"
    state["t052"] = {
        "status": "EVIDENCE_RECORDED_NO_AUTOMATIC_PROMOTION",
        "workflow_run_id": workflow_id,
        "result_fingerprint": result["report_fingerprint"],
        "all_cells_passed": all_passed,
        "cells_reported": sorted(cells),
    }
    _write(state_path, state)

    decision = _load(decision_path)
    decision["recorded_on"] = datetime.now(timezone.utc).date().isoformat()
    decision["current_stage"] = "T052_FIXED_CORE_EVALUATED"
    decision["verified_facts"] = list(decision.get("verified_facts", []))
    fact = (
        "T052 evaluated both unchanged fixed-core sleeves across fresh T049/T050 universes "
        "under the pre-registered 2798/700 split and unchanged cost/risk gates; no selection or promotion occurred."
    )
    if fact not in decision["verified_facts"]:
        decision["verified_facts"].append(fact)
    decision["next_action"] = (
        "Interpret T052 evidence without selection or automatic promotion. "
        "If another performance study is considered, create a separate ex-ante preregistration "
        "and preserve all T052 results unchanged."
    )
    _write(decision_path, decision)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--result-doc", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    publish(
        Path(args.result),
        Path(args.ledger),
        Path(args.result_doc),
        Path(args.checkpoint),
        Path(args.state),
        Path(args.decision),
    )
    print("T052 PUBLISH OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
