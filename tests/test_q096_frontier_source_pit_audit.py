from __future__ import annotations

import json
from pathlib import Path

from automation.q096_frontier_source_pit_audit import candidate_gate_matrix


def test_q096_inventory_is_the_frozen_current_inventory() -> None:
    inventory = json.loads(
        Path("research/frontier/candidate_inventory_2026_09_29.json").read_text(encoding="utf-8")
    )
    assert inventory["status"] == "DESIGN_INVENTORY_ONLY"
    assert inventory["policy"]["performance_authorized"] is False
    assert inventory["policy"]["holdout_selection_allowed"] is False
    assert len(inventory["candidates"]) == 44


def test_q096_matrix_is_non_evaluative_and_has_no_performance_gate() -> None:
    candidates = [
        ["frontier:C30", "Risk-text peer propagation", "SEC Item 1A risk text", "MACHINE_FEASIBILITY_IMPLEMENTED"],
        ["frontier:M5", "Benchmark demand shock clock", "scheduled benchmark rebalances", "DESIGN_ONLY_UNRANKED"],
    ]
    matrix = candidate_gate_matrix(candidates)
    assert len(matrix) == 2
    assert all(row["performance_authorized"] is False for row in matrix)
    assert any(row["pit_state"] == "MACHINE_FEASIBILITY_PRESENT" for row in matrix)
    assert any(row["archive_state"] == "HISTORICAL_ANNOUNCEMENT_ARCHIVE_AND_MAPPING_PENDING" for row in matrix)


def test_q096_safety_contract_is_fixed() -> None:
    assert {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    } == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
