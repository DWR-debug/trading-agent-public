from __future__ import annotations

import json
from pathlib import Path

from automation.q096_frontier_source_pit_audit import (
    SEC_SAMPLE_CIKS,
    STATIC_PROBES,
    candidate_gate_matrix,
    filing_url,
    recent_filing_rows,
)


def test_q096_inventory_is_the_frozen_current_inventory() -> None:
    inventory = json.loads(
        Path("research/frontier/candidate_inventory_2026_09_29.json").read_text(encoding="utf-8")
    )
    assert inventory["status"] == "DESIGN_INVENTORY_ONLY"
    assert inventory["policy"]["performance_authorized"] is False
    assert inventory["policy"]["holdout_selection_allowed"] is False
    assert len(inventory["candidates"]) == 48
    option_rows = [row for row in inventory["candidates"] if row[0] == "Q078:O1"]
    assert option_rows and option_rows[0][3] == "BLOCKED_FREE_HISTORICAL_SOURCE"


def test_q096_probes_cover_the_new_frontier_data_channels() -> None:
    ids = {probe[0] for probe in STATIC_PROBES}
    assert {
        "LSEG_RUSSELL_RECON",
        "CBOE_VIX_HISTORY",
        "SEC_FTD_HISTORY",
        "FINRA_SHORT_INTEREST",
    } <= ids
    module = Path("automation/q096_frontier_source_pit_audit.py").read_text(encoding="utf-8")
    assert "MSFT_10K_10Q" in module
    assert "AAPL_10K_10Q" in module
    assert "FORM4_SAMPLE" in module
    assert "FORM13F_SAMPLE" in module
    assert "BENEFICIAL_OWNERSHIP_SAMPLE" in module
    assert "FORM144_SAMPLE" in module
    assert "GDELT_DAILY_ARCHIVE" in module
    assert "SEC_FTD_HISTORY" in module
    assert "FINRA_SHORT_INTEREST" in module
    assert "BENEFICIAL_OWNERSHIP_SAMPLE" in module
    assert "FORM144_SAMPLE" in module


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


def test_q096_sec_sample_ciks_match_verified_public_filers() -> None:
    assert SEC_SAMPLE_CIKS["MSFT"] == "0000789019"
    assert SEC_SAMPLE_CIKS["SEC_13F_SAMPLE"] == "0001067983"
    assert SEC_SAMPLE_CIKS["SEC_FORM144_SAMPLE"] == "0001326801"


def test_q096_sec_submission_row_normalization_and_filing_url() -> None:
    payload = {
        "filings": {
            "recent": {
                "form": ["10-K", "10-Q"],
                "filingDate": ["2026-08-01", "2026-05-01"],
                "accessionNumber": ["0000789019-26-000001", "0000789019-26-000002"],
                "primaryDocument": ["annual.htm", "quarter.htm"],
                "acceptanceDateTime": ["20260801160000", "20260501160000"],
            }
        }
    }
    rows = recent_filing_rows(payload)
    assert rows[0]["form"] == "10-K"
    assert rows[1]["accessionNumber"] == "0000789019-26-000002"
    assert rows[0]["acceptanceDateTime"] == "20260801160000"
    assert filing_url(SEC_SAMPLE_CIKS["MSFT"], rows[0]["accessionNumber"], rows[0]["primaryDocument"]).endswith(
        "/Archives/edgar/data/789019/000078901926000001/annual.htm"
    )


def test_q096_matrix_classifies_q097_public_channels_as_sec_or_public_source() -> None:
    candidates = [
        ["Q097:I15", "Fails-to-deliver stress change", "SEC Fails-to-Deliver", "SOURCE_FEASIBILITY_ONLY"],
        ["Q097:I16", "Short-interest change", "FINRA Short Interest", "SOURCE_FEASIBILITY_ONLY"],
        ["Q097:I17", "Beneficial-ownership change", "SEC Schedule 13D/13G", "SOURCE_FEASIBILITY_ONLY"],
        ["Q097:I18", "Proposed insider-sale flow", "SEC Form 144", "SOURCE_FEASIBILITY_ONLY"],
    ]
    matrix = candidate_gate_matrix(candidates)
    assert all(row["source_state"] == "PUBLIC_SOURCE_CHANNEL_CONFIRMED" for row in matrix)
    assert all(row["performance_authorized"] is False for row in matrix)
