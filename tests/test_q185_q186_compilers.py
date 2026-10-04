from datetime import date

from automation.q185_legal_state_machine import earliest_public_state, states_as_of
from automation.q186_patent_network import build_edge_weights, compute_grant_shock


def test_q186_excludes_self_citations_and_future_edges() -> None:
    rows = [
        {"cited_firm": "UP", "citing_firm": "DOWN", "citation_public_date": date(2025, 1, 1)},
        {"cited_firm": "DOWN", "citing_firm": "DOWN", "citation_public_date": date(2025, 1, 1)},
        {"cited_firm": "UP2", "citing_firm": "DOWN", "citation_public_date": date(2025, 7, 1)},
    ]
    weights = build_edge_weights(rows, date(2025, 7, 31))
    assert set(weights) == {("UP", "DOWN"), ("UP2", "DOWN")}
    assert weights[("UP", "DOWN")] == 0.5
    assert weights[("UP2", "DOWN")] == 0.5


def test_q186_grant_shock_propagates_only_one_hop() -> None:
    weights = {("UP", "DOWN"): 1.0, ("DOWN", "FAR"): 1.0}
    grants = [{"upstream_firm": "UP", "grant_date": date(2025, 8, 5)}]
    assert compute_grant_shock(grants, weights, date(2025, 8, 5)) == {"DOWN": 1.0}


def test_q185_future_docket_entry_cannot_rewrite_prefix() -> None:
    base = [
        {"case_id": "C1", "public_date": date(2025, 1, 2), "event_id": "1", "event_class": "CASE_FILED"},
        {"case_id": "C1", "public_date": date(2025, 2, 5), "event_id": "2", "event_class": "ACTIVE_DOCKET_ENTRY"},
    ]
    with_future = base + [
        {"case_id": "C1", "public_date": date(2025, 7, 1), "event_id": "3", "event_class": "TERMINATION"}
    ]
    assert states_as_of(base, date(2025, 2, 5)) == states_as_of(with_future, date(2025, 2, 5))


def test_q185_earliest_state_is_filing_not_outcome() -> None:
    entries = [
        {"case_id": "C2", "public_date": date(2025, 1, 5), "event_id": "1", "event_class": "CASE_FILED"},
        {"case_id": "C2", "public_date": date(2025, 8, 1), "event_id": "2", "event_class": "TERMINATION"},
    ]
    first = earliest_public_state(entries, date(2025, 12, 31))
    assert first["C2"].state == "CASE_FILED"
