from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_q187_q192_inventory_is_design_only_and_complete() -> None:
    data = json.loads(
        (
            ROOT
            / "research/frontier/q187_q192_candidate_wave_2026_10_04.json"
        ).read_text(encoding="utf-8")
    )
    assert data["status"] == "DESIGN_INVENTORY_ONLY"
    assert len(data["candidates"]) == 6
    for candidate in data["candidates"]:
        assert all(
            candidate.get(k)
            for k in ("id", "name", "hypothesis", "construction", "sources", "next_gate")
        )
        assert candidate.get("id") in {"Q187", "Q188", "Q189", "Q190", "Q191", "Q192"}
        assert "performance" not in candidate
        assert "promotion" not in candidate
    assert data["policy"]["performance_authorized"] is False
    assert data["policy"]["family_ranking_allowed"] is False
    assert data["safety"]["paper_only"] is True
    assert data["safety"]["automatic_promotion"] is False


def test_q187_q192_source_feasibility_is_non_authorizing() -> None:
    text = (
        ROOT / "automation/q187_q192_source_feasibility.py"
    ).read_text(encoding="utf-8")
    for marker in (
        "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED",
        "future_row_prefix_invariant",
        "reordering_future_row_cannot_change_prefix",
        "performance",
        "holdout_selection",
        "parameter_search",
        "candidate_results",
        "live_execution",
        "automatic_promotion",
    ):
        assert marker in text


def test_q187_q192_workflow_is_hosted_and_non_performance() -> None:
    text = (
        ROOT / ".github/workflows/q187-q192-source-feasibility.yml"
    ).read_text(encoding="utf-8")
    assert "runs-on: ubuntu-24.04" in text
    assert "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED" in text
    assert "automatic_promotion" in text
    assert "holdout_selection" in text


def test_q187_uses_documented_transaction_post_probe():
    text = (ROOT / "automation/q187_q192_source_feasibility.py").read_text(encoding="utf-8")
    assert "def post_json(" in text
    assert "spending_by_transaction" in text
    assert '"Action Date"' in text
    assert '"Transaction Amount"' in text
    assert '"required_keys_present"' in text


def test_q187_transaction_probe_has_required_award_type_filter():
    text = (ROOT / "automation/q187_q192_source_feasibility.py").read_text(encoding="utf-8")
    assert '"award_type_codes": ["A", "B", "C", "D"]' in text
    assert '"sort": "Transaction Amount"' in text
