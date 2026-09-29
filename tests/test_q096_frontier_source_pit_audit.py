from __future__ import annotations

import json
from pathlib import Path

from automation.q096_frontier_source_pit_audit import PROBES, candidate_gate_matrix


def test_q096_inventory_is_the_frozen_current_inventory() -> None:
    inventory = json.loads(
        Path("research/frontier/candidate_inventory_2026_09_29.json").read_text(encoding="utf-8")
    )
    assert inventory["status"] == "DESIGN_INVENTORY_ONLY"
    assert inventory["policy"]["performance_authorized"] is False
    assert inventory["policy"]["holdout_selection_allowed"] is False
    assert len(inventory["candidates"]) == 44
    option_rows = [row for row in inventory["candidates"] if row[0] == "Q078:O1"]
    assert option_rows and option_rows[0][3] == "BLOCKED_FREE_HISTORICAL_SOURCE"


def test_q096_probes_cover_the_new_frontier_data_channels() -> None:
    ids = {probe[0] for probe in PROBES}
    assert {
        "SEC_10K_ITEM1A",
        "SEC_10Q_MDA",
        "SEC_SUBMISSIONS_MSFT",
        "SEC_COMPANYFACTS_MSFT",
        "LSEG_RUSSELL_RECON",
        "CBOE_VIX_HISTORY",
        "GDELT_DAILY_ARCHIVE",
    } <= ids


def test_q096_matrix_is_non_evaluative() -> None:
    candidates = [
        ["frontier:C30", "Risk-text peer propagation", "SEC Item 1A risk text", "MACHINE_FEASIBILITY_IMPLEMENTED"],
        ["frontier:M5", "Benchmark demand shock clock", "scheduled benchmark rebalances", "DESIGN_ONLY_UNRANKED"],
    ]
    matrix = candidate_gate_matrix(candidates)
    assert len(matrix) == 2
    assert all(row["performance_authorized"] is False for row in matrix)
    assert any(row["pit_state"] == "MACHINE_FEASIBILITY_PRESENT" for row in matrix)
    assert any(
        row["archive_state"] == "HISTORICAL_ANNOUNCEMENT_ARCHIVE_AND_MAPPING_PENDING"
        for row in matrix
    )


def test_q096_does_not_enable_performance_or_live_execution() -> None:
    module = Path("automation/q096_frontier_source_pit_audit.py").read_text(encoding="utf-8")
    assert '"performance_evaluation": False' in module
    assert '"holdout_evaluation": False' in module
    assert '"candidate_ranking": False' in module
    assert '"automatic_promotion": False' in module
    assert '"paper_only": True' in module
    assert '"live_trading_enabled": False' in module
    assert '"orders_enabled": False' in module
