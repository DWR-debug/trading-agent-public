from __future__ import annotations

from automation import q126_q132_frontier_feasibility as frontier


def test_q126_q132_contract_inventory_covers_exact_seven_candidates():
    result = frontier.evaluate()
    assert {row["candidate_id"] for row in result["findings"]} == {
        "Q126", "Q127", "Q128", "Q129", "Q130", "Q131", "Q132"
    }
    assert result["scientific_boundary"]["performance"] is False
    assert result["scientific_boundary"]["holdout"] is False
    assert result["scientific_boundary"]["selection"] is False
    assert result["safety"]["paper_only"] is True


def test_q127_free_source_markers_are_fail_closed(monkeypatch):
    monkeypatch.setattr(
        frontier,
        "fetch_text",
        lambda url: (200, "Daily Short Sale Volume Files; no later than 6:00:00pm ET; Updated"),
    )
    result = frontier.evaluate()
    q127 = next(row for row in result["findings"] if row["candidate_id"] == "Q127")
    assert q127["status"] == "SOURCE_FEASIBILITY_COMPLETED"


def test_q127_missing_publication_marker_blocks(monkeypatch):
    monkeypatch.setattr(
        frontier,
        "fetch_text",
        lambda url: (200, "Daily Short Sale Volume Files"),
    )
    result = frontier.evaluate()
    q127 = next(row for row in result["findings"] if row["candidate_id"] == "Q127")
    assert q127["status"] == "BLOCKED_FINRA_SOURCE_PROBE"


def test_q128_q129_q130_remain_blocked_without_registered_free_history():
    result = frontier.evaluate()
    by_id = {row["candidate_id"]: row for row in result["findings"]}
    assert by_id["Q128"]["status"] == "BLOCKED_FREE_HISTORICAL_SOURCE_NOT_ESTABLISHED"
    assert by_id["Q129"]["status"] == "BLOCKED_FREE_HISTORICAL_SOURCE_NOT_ESTABLISHED"
    assert by_id["Q130"]["status"] == "BLOCKED_PUBLIC_HISTORICAL_ATTENTION_SOURCE_NOT_ESTABLISHED"


def test_q132_fixed_decomposition_is_future_invariant():
    checks = frontier.synthetic_q132_mutation_test()
    assert all(checks.values())


def test_q131_sec_contract_requires_public_specs_and_local_compilers(monkeypatch):
    monkeypatch.setattr(
        frontier,
        "fetch_text",
        lambda url: (200, "Schedule 13D & 13G Form 13F Form XBRL"),
    )
    result = frontier.evaluate()
    q131 = next(row for row in result["findings"] if row["candidate_id"] == "Q131")
    assert q131["status"] == "SOURCE_AVAILABLE_CONTRACT_NOT_FROZEN"
