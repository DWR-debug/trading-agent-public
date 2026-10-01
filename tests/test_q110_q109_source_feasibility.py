from __future__ import annotations

import json
from pathlib import Path

from automation.q110_q109_source_feasibility import page_probe


def test_q110_preregistration_is_design_only():
    root = Path(__file__).parents[1]
    data = json.loads(
        (root / "research/preregistrations/q110_q109_source_feasibility_2026_10_01.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["status"] == "PREREGISTERED_SOURCE_FEASIBILITY_ONLY"
    assert data["gating_rules"]["no_performance"] is False
    assert data["gating_rules"]["no_holdout"] is False
    assert data["gating_rules"]["no_ranking"] is False
    assert data["gating_rules"]["no_parameter_search"] is False
    assert data["gating_rules"]["no_asset_selection"] is False
    assert data["gating_rules"]["no_llm_text_scoring"] is True
    assert data["safety"]["paper_only"] is True


def test_q110_probe_is_non_authorizing():
    result = page_probe(
        "SEC_TECHNICAL",
        "https://www.sec.gov/submit-filings/technical-specifications",
        ["Schedule 13D & 13G"],
    )
    assert result["id"] == "SEC_TECHNICAL"
    assert "performance" not in result["status"].lower()
