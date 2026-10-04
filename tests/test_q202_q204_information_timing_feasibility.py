from __future__ import annotations

import json
from pathlib import Path

from automation.q202_q204_information_timing_feasibility import (
    BOUNDARY,
    FIXED,
    SAFETY,
    parse_fr_by_date,
    probe_markers,
)


ROOT = Path(__file__).resolve().parents[1]


def test_fixed_information_timing_routes_and_safety():
    assert FIXED["Q202_CT_STUDY"].startswith("https://clinicaltrials.gov/")
    assert FIXED["Q203_SEC_SUBMISSIONS"].startswith("https://data.sec.gov/")
    assert FIXED["Q204_FR_20200110"].startswith("https://www.federalregister.gov/api/")
    assert all(v is False for v in BOUNDARY.values())
    assert SAFETY == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_parser_rejects_bad_federal_register_shape():
    import pytest

    with pytest.raises(ValueError):
        class _Nope(bytes):
            pass
        # Avoid network dependence: call with a clearly invalid fixed URL.
        parse_fr_by_date("https://example.invalid/not-a-federal-register-route")


def test_marker_probe_contract_is_non_authorizing():
    d = probe_markers(
        "test",
        "https://example.invalid/no-network",
        ["required-marker"],
        "DWR-debug/trading-agent-public/test",
    )
    assert d["scientific_boundary"]["performance"] is False
    assert d["scientific_boundary"]["live_execution"] is False


def test_candidate_design_contains_q202_q203_q204():
    d = json.loads(
        (
            ROOT / "research/candidates/orthogonal_candidate_specs_2026-10-04.json"
        ).read_text(encoding="utf-8")
    )
    ids = [x["id"] for x in d["candidates"]]
    assert ids[-3:] == ["Q202", "Q203", "Q204"]
    assert all(
        x["scientific_boundary"] == "discovery_contract_only"
        for x in d["candidates"][-3:]
    )
