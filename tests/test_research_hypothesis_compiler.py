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
    ])
    assert result["candidate_count"] == 14
    assert result["scientific_boundary"]["performance"] is False
    assert len(result["bundle_fingerprint"]) == 64


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
