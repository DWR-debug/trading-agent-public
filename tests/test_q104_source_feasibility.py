from __future__ import annotations

import json
from pathlib import Path

from automation.q104_source_feasibility import candidate_matrix


def test_q104_source_matrix_is_non_authorizing():
    probes = {
        "SEC_13F": {"status": "VERIFIABLE"},
        "SEC_COMPANYFACTS": {"status": "VERIFIABLE"},
        "SEC_FTD": {"status": "VERIFIABLE"},
        "FINRA_SHORT_INTEREST": {"status": "VERIFIABLE"},
        "FINRA_REGSHO": {"status": "VERIFIABLE"},
        "SEC_SUBMISSIONS": {"status": "VERIFIABLE"},
        "TREASURY_AUCTIONS_API": {"status": "VERIFIABLE"},
    }
    result = candidate_matrix(probes)
    assert len(result) == 6
    assert all(row["performance_authorized"] is False for row in result)
    assert all(row["source_status"] in {"SOURCE_FEASIBLE", "SYNTHETIC_ONLY"} for row in result)


def test_q104_source_matrix_matches_wave_inventory():
    root = Path(__file__).parents[1]
    wave = json.loads(
        (root / "research/frontier/q104_candidate_wave_2026_10_01.json").read_text(
            encoding="utf-8"
        )
    )
    ids = [row["id"] for row in wave["candidates"]]
    probes = {
        "SEC_13F": {"status": "VERIFIABLE"},
        "SEC_COMPANYFACTS": {"status": "VERIFIABLE"},
        "SEC_FTD": {"status": "VERIFIABLE"},
        "FINRA_SHORT_INTEREST": {"status": "VERIFIABLE"},
        "FINRA_REGSHO": {"status": "VERIFIABLE"},
        "SEC_SUBMISSIONS": {"status": "VERIFIABLE"},
        "TREASURY_AUCTIONS_API": {"status": "VERIFIABLE"},
    }
    matrix_ids = [row["id"] for row in candidate_matrix(probes)]
    assert matrix_ids == ids
