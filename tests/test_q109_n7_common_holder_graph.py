from automation.q109_n7_common_holder_graph import graph_from_records, AS_OF


def test_n7_metric_is_deterministic_and_unweighted():
    rows = [
        {"manager_cik": "1", "period_of_report": "31-MAR-2026", "security_key": "A", "symbol": "SPGI", "filing_date": "2026-05-01", "accession": "A1"},
        {"manager_cik": "1", "period_of_report": "31-MAR-2026", "security_key": "B", "symbol": "NDAQ", "filing_date": "2026-05-01", "accession": "A2"},
        {"manager_cik": "2", "period_of_report": "31-MAR-2026", "security_key": "A", "symbol": "SPGI", "filing_date": "2026-05-01", "accession": "B1"},
    ]
    out = graph_from_records(rows, AS_OF)
    assert out["common_holder_edge_count"] == 1
    assert out["symbol_connectedness_degree"]["SPGI"] == 1
    assert out["symbol_connectedness_degree"]["NDAQ"] == 1


def test_n7_future_pit_mutation_does_not_change_snapshot():
    rows = [
        {"manager_cik": "1", "period_of_report": "31-MAR-2026", "security_key": "A", "symbol": "SPGI", "filing_date": "2026-05-01", "accession": "A1"},
        {"manager_cik": "1", "period_of_report": "31-MAR-2026", "security_key": "B", "symbol": "NDAQ", "filing_date": "2026-05-01", "accession": "A2"},
    ]
    future = rows + [{**rows[0], "accession": "FUT", "filing_date": "2026-12-01", "period_of_report": "30-SEP-2026"}]
    assert graph_from_records(rows, AS_OF) == graph_from_records(future, AS_OF)
