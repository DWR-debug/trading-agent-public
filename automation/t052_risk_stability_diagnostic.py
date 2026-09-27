"""Deterministic, diagnostic-only risk/stability decomposition for T052."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TRIAL_ID = "T-2026-09-27-052"
SOURCE_FINGERPRINT = "a0a1dc33ce281e7addcf9cf924881b6a30797c1a744d4160fbff91d3384b1b09"
DIAGNOSTIC_ID = "Q-029-T052-RISK-STABILITY-DIAGNOSTIC-2026-09-27"

SLEEVES = ("trend_sma_50_200", "cs_momentum_12_1_top2")
GATES = (
    "research_return_positive",
    "research_drawdown_lte_10pct",
    "research_profit_factor_gte_1_10",
    "rolling_profit_factor_gte_1_10",
    "rolling_profitable_window_ratio_gte_0_50",
    "rolling_average_drawdown_lte_10pct",
    "oos_to_is_return_ratio_gte_0_25",
    "holdout_return_positive",
    "holdout_profit_factor_gte_1_10",
    "holdout_drawdown_lte_10pct",
    "stress_1_5x_holdout_nonnegative",
    "stress_2x_holdout_nonnegative",
    "total_return_sensitivity_holdout_nonnegative",
)
RISK_GATES = (
    "research_drawdown_lte_10pct",
    "rolling_average_drawdown_lte_10pct",
    "holdout_drawdown_lte_10pct",
)
GENERALIZATION_GATES = (
    "oos_to_is_return_ratio_gte_0_25",
    "holdout_return_positive",
    "holdout_profit_factor_gte_1_10",
)
COST_STRESS_GATES = (
    "stress_1_5x_holdout_nonnegative",
    "stress_2x_holdout_nonnegative",
    "total_return_sensitivity_holdout_nonnegative",
)
RESEARCH_ROLLING_GATES = (
    "research_return_positive",
    "research_profit_factor_gte_1_10",
    "rolling_profit_factor_gte_1_10",
    "rolling_profitable_window_ratio_gte_0_50",
)
EXPECTED_SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


class DiagnosticContractError(ValueError):
    """Raised when the frozen T052 evidence contract is violated."""


def _fp(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_source(ledger_path: Path) -> dict[str, Any]:
    ledger = _load(ledger_path)
    trials = ledger.get("trials")
    if not isinstance(trials, list):
        raise DiagnosticContractError("trial_ledger.json has no supported trials list")
    matches = [item for item in trials if item.get("trial_id") == TRIAL_ID]
    if len(matches) != 1:
        raise DiagnosticContractError(f"expected exactly one {TRIAL_ID} entry")
    trial = matches[0]
    if trial.get("outcome", {}).get("result_fingerprint") != SOURCE_FINGERPRINT:
        raise DiagnosticContractError("T052 result fingerprint mismatch")
    if trial.get("selection", {}).get("selected") is not False:
        raise DiagnosticContractError("T052 selection state is not false")
    if trial.get("search_scope", {}).get("selection_used") is not False:
        raise DiagnosticContractError("T052 search scope is not frozen")
    if trial.get("data_scope", {}).get("holdout_used_for_selection") is not False:
        raise DiagnosticContractError("T052 holdout selection state is not false")
    if trial.get("safety") != EXPECTED_SAFETY:
        raise DiagnosticContractError("T052 safety contract mismatch")
    cells = trial.get("outcome", {}).get("cells")
    if not isinstance(cells, dict) or len(cells) != 4:
        raise DiagnosticContractError("T052 must contain exactly four frozen cells")
    for key, cell in cells.items():
        if not isinstance(cell, dict):
            raise DiagnosticContractError(f"invalid cell {key}")
        gates = cell.get("gates")
        if not isinstance(gates, dict) or set(gates) != set(GATES):
            raise DiagnosticContractError(f"gate contract mismatch in {key}")
        if cell.get("all_gates_passed") != all(bool(gates[g]) for g in GATES):
            raise DiagnosticContractError(f"gate aggregate mismatch in {key}")
        base = cell.get("base", {})
        if not isinstance(base, dict) or not {"research", "holdout"} <= set(base):
            raise DiagnosticContractError(f"base metrics missing in {key}")
        if not isinstance(cell.get("rolling"), dict):
            raise DiagnosticContractError(f"rolling summary missing in {key}")
    return trial


def run(ledger_path: Path, output_path: Path) -> dict[str, Any]:
    trial = _validate_source(ledger_path)
    cells = trial["outcome"]["cells"]
    cell_keys = tuple(sorted(cells))

    gate_failure_counts = {
        gate: sum(not bool(cells[key]["gates"][gate]) for key in cell_keys)
        for gate in GATES
    }
    all_four_failed = [
        gate for gate in GATES if gate_failure_counts[gate] == len(cell_keys)
    ]
    failed_by_cell = {
        key: [gate for gate in GATES if not cells[key]["gates"][gate]]
        for key in cell_keys
    }

    universes = sorted({key.split(":", 1)[0] for key in cell_keys})
    shared_failed_by_universe = {}
    for universe in universes:
        keys = [key for key in cell_keys if key.startswith(universe + ":")]
        if len(keys) != len(SLEEVES):
            raise DiagnosticContractError(f"expected two sleeves for {universe}")
        shared_failed_by_universe[universe] = [
            gate for gate in GATES
            if all(not bool(cells[key]["gates"][gate]) for key in keys)
        ]

    shifts = {}
    rolling = {}
    for key in cell_keys:
        base = cells[key]["base"]
        research = base["research"]
        holdout = base["holdout"]
        shifts[key] = {
            "research_return": research["period_return"],
            "holdout_return": holdout["period_return"],
            "return_holdout_minus_research": holdout["period_return"] - research["period_return"],
            "research_max_drawdown_percent": research["max_drawdown_percent"],
            "holdout_max_drawdown_percent": holdout["max_drawdown_percent"],
            "max_drawdown_holdout_minus_research_pct_points": (
                holdout["max_drawdown_percent"] - research["max_drawdown_percent"]
            ),
            "research_profit_factor": research["profit_factor"],
            "holdout_profit_factor": holdout["profit_factor"],
            "profit_factor_holdout_minus_research": (
                holdout["profit_factor"] - research["profit_factor"]
            ),
        }
        rolling[key] = cells[key]["rolling"]

    categories = {
        "risk_and_stability": {
            "gates": list(RISK_GATES),
            "failed_cells_by_gate": {gate: gate_failure_counts[gate] for gate in RISK_GATES},
        },
        "generalization": {
            "gates": list(GENERALIZATION_GATES),
            "failed_cells_by_gate": {gate: gate_failure_counts[gate] for gate in GENERALIZATION_GATES},
        },
        "cost_stress": {
            "gates": list(COST_STRESS_GATES),
            "failed_cells_by_gate": {gate: gate_failure_counts[gate] for gate in COST_STRESS_GATES},
        },
        "research_and_rolling_quality": {
            "gates": list(RESEARCH_ROLLING_GATES),
            "failed_cells_by_gate": {gate: gate_failure_counts[gate] for gate in RESEARCH_ROLLING_GATES},
        },
    }

    risk_common = all(gate in all_four_failed for gate in RISK_GATES)
    primary_pattern = (
        "COMMON_RISK_STABILITY_FAILURE" if risk_common else "MIXED_RISK_STABILITY_PATTERN"
    )

    result = {
        "schema_version": 1,
        "diagnostic_id": DIAGNOSTIC_ID,
        "source_trial_id": TRIAL_ID,
        "source_workflow_run_id": trial["outcome"]["workflow_run_id"],
        "source_artifact_id": trial["data_scope"]["source_artifact_id"],
        "source_result_fingerprint": trial["outcome"]["result_fingerprint"],
        "source_scope": {
            "universes": universes,
            "cells": list(cell_keys),
            "fixed_population": True,
            "performance_recomputed": False,
        },
        "governance": {
            "diagnostic_only": True,
            "selection_used": False,
            "ranking_used": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "variant_search": False,
            "holdout_used_for_selection": False,
            "gate_changes": False,
            "promotion_decision": False,
            "live_execution": False,
        },
        "diagnostic": {
            "primary_pattern": primary_pattern,
            "gate_failure_counts": gate_failure_counts,
            "all_four_cells_failed_gates": all_four_failed,
            "failed_gates_by_cell": failed_by_cell,
            "shared_failed_gates_by_universe": shared_failed_by_universe,
            "categories": categories,
            "research_to_holdout_shifts": shifts,
            "rolling_stability": rolling,
        },
        "safety": EXPECTED_SAFETY,
    }
    result["fingerprint"] = _fp(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.ledger, args.output)
    print("T052 RISK/STABILITY DIAGNOSTIC OK")
    print("PRIMARY_PATTERN:", result["diagnostic"]["primary_pattern"])
    print("RESULT_FINGERPRINT:", result["fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
