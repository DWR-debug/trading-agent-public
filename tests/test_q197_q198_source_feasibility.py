from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_inventory_is_design_only():
    d = json.loads(
        (ROOT / "research/frontier/q197_q198_candidate_wave_2026_10_04.json").read_text(
            encoding="utf-8"
        )
    )
    assert d["status"] == "DESIGN_INVENTORY_ONLY"
    assert {x["id"] for x in d["candidates"]} == {"Q197", "Q198"}
    assert d["policy"]["performance_authorized"] is False
    assert d["policy"]["asset_search_allowed"] is False
    assert d["safety"]["paper_only"] is True


def test_q198_separates_filing_publication_and_effective_dates():
    d = json.loads(
        (ROOT / "research/frontier/q197_q198_candidate_wave_2026_10_04.json").read_text(
            encoding="utf-8"
        )
    )
    q = next(x for x in d["candidates"] if x["id"] == "Q198")
    assert q["robustness_contract"]["official_filing_timestamp_locked"] is False
    assert q["robustness_contract"]["publication_date_separate"] is True
    assert q["robustness_contract"]["effective_date_separate"] is True
    assert q["robustness_contract"]["online_posting_time_not_substituted"] is True


def test_source_gate_contains_fail_closed_mutation_guards():
    s = (ROOT / "automation/q197_q198_source_feasibility.py").read_text(
        encoding="utf-8"
    )
    for marker in (
        "award_date_not_observation_time",
        "online_posting_time_not_official_filing_time",
        "same_day_ambiguous_events_fail_closed",
        "holdout_selection",
        "parameter_search",
        "live_execution",
    ):
        assert marker in s


def test_q198_has_official_historical_single_document_api_probe():
    s = (ROOT / "automation/q197_q198_source_feasibility.py").read_text(
        encoding="utf-8"
    )
    assert "Q198_HISTORICAL_PI_API" in s
    assert "public-inspection-documents/2021-07287.json" in s
    assert "filed_at" in s
    assert "last_public_inspection_issue" in s


def test_workflow_is_bounded_and_non_authorizing():
    s = (ROOT / ".github/workflows/q197-q198-source-feasibility.yml").read_text(
        encoding="utf-8"
    )
    assert "runs-on: ubuntu-24.04" in s
    assert "automatic_promotion" in s
    assert "holdout_selection" in s
    assert "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED" in s
