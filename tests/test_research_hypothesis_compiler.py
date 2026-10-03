from pathlib import Path

import pytest

from automation.research_hypothesis_compiler import (
    compile_inventories,
    _validate_candidate,
)


ROOT = Path(__file__).parents[1]


def test_discovery_compiler_compiles_current_frontier_inventories():
    result = compile_inventories([
        ROOT / "research/frontier/q104_candidate_wave_2026_10_01.json",
        ROOT / "research/frontier/q109_candidate_wave_2026_10_01.json",
        ROOT / "research/frontier/q123_candidate_wave_2026_10_02.json",
        ROOT / "research/frontier/q126_q132_candidate_wave_2026_10_03.json",
    ])
    assert result["candidate_count"] == 21
    assert result["scientific_boundary"]["performance"] is False
    assert len(result["bundle_fingerprint"]) == 64


def test_q126_q132_discovery_wave_is_quarantined_and_non_authoritative():
    result = compile_inventories([
        ROOT / "research/frontier/q126_q132_candidate_wave_2026_10_03.json",
    ])
    assert result["candidate_count"] == 7
    assert {x["id"] for x in result["candidates"]} == {"Q126","Q127","Q128","Q129","Q130","Q131","Q132"}
    assert all(x["status"] == "QUARANTINED_HYPOTHESIS_ONLY" for x in result["candidates"])
    assert all(x["performance_authorized"] is False for x in result["candidates"])
    assert result["scientific_boundary"]["ranking"] is False
    assert result["scientific_boundary"]["selection"] is False


def test_discovery_compiler_rejects_performance_fields():
    candidate = {
        "id": "X",
        "name": "unsafe",
        "hypothesis": "x",
        "construction": "y",
        "sources": ["source"],
        "next_gate": "source_feasibility",
        "holdout_return": 0.2,
    }
    with pytest.raises(ValueError, match="DISCOVERY_FORBIDDEN_FIELDS"):
        _validate_candidate(candidate, "synthetic.json")
