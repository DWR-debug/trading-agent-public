from __future__ import annotations

import json
from pathlib import Path

import pytest

from automation.candidate_robustness_gate import (
    ROBUSTNESS_DIMENSIONS,
    compile_receipt,
    require_receipt_for_formal_phase,
    validate_candidate,
)

ROOT = Path(__file__).parents[1]


def test_current_frontier_candidates_pass_structural_robustness_gate():
    paths = [
        ROOT / "research/frontier/q104_candidate_wave_2026_10_01.json",
        ROOT / "research/frontier/q109_candidate_wave_2026_10_01.json",
        ROOT / "research/frontier/q123_candidate_wave_2026_10_02.json",
        ROOT / "research/frontier/q126_q132_candidate_wave_2026_10_03.json",
    ]
    receipt = compile_receipt(paths, "research/runs/self_hosted/pre_formal_candidate_robustness.json")
    assert receipt["status"] == "PRE_FORMAL_ROBUSTNESS_COMPLETED"
    assert receipt["failed_candidate_count"] == 0
    assert receipt["candidate_count"] == 67
    assert receipt["formalization_allowed"] is False
    for item in receipt["candidates"]:
        assert item["status"] == "PRE_FORMAL_ROBUSTNESS_COMPLETED"
        assert set(item["dimensions"]) == set(ROBUSTNESS_DIMENSIONS)
        assert all(item["dimensions"].values())
        assert item["research_only"] is True
        assert item["no_post_hoc_tuning"] is True


def test_gate_rejects_unsafe_candidate_fields():
    candidate = {
        "id": "X",
        "name": "unsafe",
        "hypothesis": "x",
        "construction": "fixed deterministic PIT construction",
        "sources": ["source"],
        "next_gate": "source_feasibility",
        "parameter_search": True,
    }
    result = validate_candidate(candidate, "synthetic.json", "artifact.json")
    assert result["status"] == "PRE_FORMAL_ROBUSTNESS_FAILED"
    assert any("forbidden_fields" in item for item in result["violations"])


def test_formal_phase_requires_a_completed_receipt():
    failed = {"status": "PRE_FORMAL_ROBUSTNESS_FAILED", "candidates": []}
    with pytest.raises(RuntimeError, match="UNIVERSAL_CANDIDATE_ROBUSTNESS_GATE_FAIL"):
        require_receipt_for_formal_phase("QX", failed)


def test_gate_is_non_scientific_and_non_authorizing():
    candidate = {
        "id": "X",
        "name": "safe",
        "hypothesis": "x",
        "construction": "fixed deterministic PIT construction",
        "sources": ["source"],
        "next_gate": "source_feasibility",
    }
    result = validate_candidate(candidate, "synthetic.json", "artifact.json")
    assert result["status"] == "PRE_FORMAL_ROBUSTNESS_COMPLETED"
    assert result["formalization_allowed"] is False
    assert result["scientific_evidence"] is False
    assert result["performance_authorization"] is False
    assert result["promotion"] is False
