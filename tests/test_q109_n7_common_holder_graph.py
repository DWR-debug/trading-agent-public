from automation.q109_n7_common_holder_graph import graph_from_records, AS_OF, validate_snapshot


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

def test_n7_snapshot_validation_allows_amendment_duplicates_before_pit_collapse():
    rows = [
        {"manager_cik": "1", "period_of_report": "31-MAR-2026", "security_key": "A", "symbol": "SPGI", "filing_date": "2026-05-01", "accession": "A1"},
        {"manager_cik": "1", "period_of_report": "31-MAR-2026", "security_key": "A", "symbol": "SPGI", "filing_date": "2026-05-03", "accession": "A2"},
    ]
    snapshot = [rows[-1]]
    out = validate_snapshot(snapshot)
    assert out["required_lineage_complete"] is True
    assert out["unique_manager_period_security_keys"] == 1


def test_n7_pit_boundary_is_explicitly_date_level_until_acceptance_enrichment():
    from automation.q109_n7_common_holder_graph import AS_OF
    assert AS_OF.isoformat() == "2026-08-31"


def test_n7_degree_counts_distinct_issuer_neighbors_not_manager_edges():
    rows = [
        {"manager_cik": "1", "period_of_report": "31-MAR-2026", "security_key": "A", "symbol": "SPGI", "filing_date": "2026-05-01", "accession": "A1"},
        {"manager_cik": "1", "period_of_report": "31-MAR-2026", "security_key": "B", "symbol": "NDAQ", "filing_date": "2026-05-01", "accession": "A2"},
        {"manager_cik": "2", "period_of_report": "31-MAR-2026", "security_key": "A", "symbol": "SPGI", "filing_date": "2026-05-02", "accession": "B1"},
        {"manager_cik": "2", "period_of_report": "31-MAR-2026", "security_key": "B", "symbol": "NDAQ", "filing_date": "2026-05-02", "accession": "B2"},
    ]
    out = graph_from_records(rows, AS_OF)
    assert out["common_holder_edge_count"] == 2
    assert out["symbol_connectedness_degree"]["SPGI"] == 1
    assert out["symbol_connectedness_degree"]["NDAQ"] == 1
