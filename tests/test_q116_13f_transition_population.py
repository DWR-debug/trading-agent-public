from datetime import date

from automation.q116_13f_transition_population import (
    build_transitions,
    find_target,
    latest_as_of,
    synthetic_contract,
)

def test_q116_synthetic():
    assert all(synthetic_contract().values())

def test_q116_alias():
    assert find_target("Williams Companies, Inc.") == "WMB"

def test_q116_sec_date_format_is_normalized_for_q114_transition():
    prior = [{
        "accession": "P1",
        "filing_date": "27-MAY-2026",
        "manager_cik": "1",
        "period_of_report": "2026-03-31",
        "security_key": "CUSIP:78409V104",
        "symbol": "SPGI",
        "shares": "100",
        "reported_value": "10000",
    }]
    current = [{
        "accession": "C1",
        "filing_date": "01-AUG-2026",
        "manager_cik": "1",
        "period_of_report": "2026-06-30",
        "security_key": "CUSIP:78409V104",
        "symbol": "SPGI",
        "shares": "140",
        "reported_value": "15000",
    }]
    out = build_transitions(prior, current, date(2026, 8, 31))
    assert out["paired_current_positions"] == 1
    assert out["transition_counts"]["SPGI"]["INCREASE"] == 1

def test_q116_latest_as_of_orders_sec_dates_chronologically():
    rows = [
        {
            "accession": "A1",
            "filing_date": "27-APR-2026",
            "manager_cik": "1",
            "period_of_report": "2026-03-31",
            "security_key": "CUSIP:78409V104",
            "symbol": "SPGI",
            "shares": "100",
            "reported_value": "10000",
        },
        {
            "accession": "A2",
            "filing_date": "01-MAY-2026",
            "manager_cik": "1",
            "period_of_report": "2026-03-31",
            "security_key": "CUSIP:78409V104",
            "symbol": "SPGI",
            "shares": "110",
            "reported_value": "11000",
        },
    ]
    chosen = latest_as_of(rows, date(2026, 8, 31))
    key = ("1", "2026-03-31", "CUSIP:78409V104", "SPGI")
    assert chosen[key]["accession"] == "A2"
