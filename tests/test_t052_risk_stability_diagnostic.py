from __future__ import annotations

import json
from pathlib import Path

import pytest

from automation.t052_risk_stability_diagnostic import (
    DIAGNOSTIC_ID,
    SOURCE_FINGERPRINT,
    DiagnosticContractError,
    run,
)

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

SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def _cell() -> dict:
    gates = {gate: False for gate in GATES}
    gates["research_return_positive"] = True
    gates["research_profit_factor_gte_1_10"] = True
    gates["rolling_profit_factor_gte_1_10"] = True
    gates["rolling_profitable_window_ratio_gte_0_50"] = True
    return {
        "base": {
            "research": {
                "period_return": 1.0,
                "max_drawdown_percent": 20.0,
                "profit_factor": 1.2,
                "day_count": 2798,
            },
            "holdout": {
                "period_return": 0.0,
                "max_drawdown_percent": 20.0,
                "profit_factor": 1.0,
                "day_count": 700,
            },
            "rolling": [],
        },
        "rolling": {
            "rolling_profit_factor": 1.2,
            "rolling_profitable_window_ratio": 0.8,
            "rolling_average_drawdown_percent": 15.0,
            "oos_to_is_return_ratio": 0.0,
        },
        "gates": gates,
        "all_gates_passed": False,
    }


def _ledger() -> dict:
    cells = {}
    for universe in ("T-2026-09-27-049", "T-2026-09-27-050"):
        for sleeve in ("trend_sma_50_200", "cs_momentum_12_1_top2"):
            cells[f"{universe}:{sleeve}"] = _cell()
    return {
        "trials": [
            {
                "trial_id": "T-2026-09-27-052",
                "data_scope": {
                    "source_artifact_id": 10938097809,
                    "holdout_used_for_selection": False,
                },
                "search_scope": {"selection_used": False},
                "selection": {"selected": False},
                "safety": SAFETY,
                "outcome": {
                    "workflow_run_id": 36338219883,
                    "result_fingerprint": SOURCE_FINGERPRINT,
                    "cells": cells,
                },
            }
        ]
    }


def test_diagnostic_is_deterministic_and_unranked(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    output = tmp_path / "result.json"
    ledger.write_text(json.dumps(_ledger()), encoding="utf-8")

    result = run(ledger, output)

    assert result["diagnostic_id"] == DIAGNOSTIC_ID
    assert result["diagnostic"]["primary_pattern"] == "COMMON_RISK_STABILITY_FAILURE"
    assert result["governance"]["diagnostic_only"] is True
    assert result["governance"]["selection_used"] is False
    assert result["governance"]["ranking_used"] is False
    assert result["governance"]["holdout_used_for_selection"] is False
    assert result["safety"] == SAFETY
    assert result["fingerprint"]
    assert json.loads(output.read_text())["fingerprint"] == result["fingerprint"]


def test_common_failure_counts_match_contract(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    output = tmp_path / "result.json"
    ledger.write_text(json.dumps(_ledger()), encoding="utf-8")

    result = run(ledger, output)
    failures = result["diagnostic"]["gate_failure_counts"]

    assert failures["research_drawdown_lte_10pct"] == 4
    assert failures["rolling_average_drawdown_lte_10pct"] == 4
    assert failures["oos_to_is_return_ratio_gte_0_25"] == 4
    assert failures["holdout_profit_factor_gte_1_10"] == 4
    assert failures["holdout_drawdown_lte_10pct"] == 4


def test_wrong_source_fingerprint_is_rejected(tmp_path: Path) -> None:
    data = _ledger()
    data["trials"][0]["outcome"]["result_fingerprint"] = "0" * 64
    ledger = tmp_path / "ledger.json"
    output = tmp_path / "result.json"
    ledger.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(DiagnosticContractError, match="fingerprint"):
        run(ledger, output)


def test_duplicate_t052_is_rejected(tmp_path: Path) -> None:
    data = _ledger()
    data["trials"].append(data["trials"][0])
    ledger = tmp_path / "ledger.json"
    output = tmp_path / "result.json"
    ledger.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(DiagnosticContractError, match="exactly one"):
        run(ledger, output)
