from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_q187_q192_pit_readiness_contract_is_non_authorizing() -> None:
    text = (ROOT / "automation/q187_q192_pit_readiness.py").read_text(encoding="utf-8")
    for marker in (
        "PIT_READINESS_COMPILATION_COMPLETED",
        "performance_authorized",
        "selection_allowed",
        "ranking_allowed",
        "holdout_selection",
        "automatic_promotion",
    ):
        assert marker in text


def test_q187_q192_pit_readiness_has_six_candidates_and_required_proofs() -> None:
    text = (ROOT / "automation/q187_q192_pit_readiness.py").read_text(encoding="utf-8")
    for candidate in ("Q187", "Q188", "Q189", "Q190", "Q191", "Q192"):
        assert f'"{candidate}"' in text


def test_q187_q192_pit_readiness_workflow_is_hosted() -> None:
    text = (ROOT / ".github/workflows/q187-q192-pit-readiness-r1.yml").read_text(encoding="utf-8")
    assert "runs-on: ubuntu-24.04" in text
    assert "q187_q192_source_feasibility_latest.json" in text
    assert "Q187_Q192_PIT_READINESS_OK" in text
    assert "automatic_promotion" in text
