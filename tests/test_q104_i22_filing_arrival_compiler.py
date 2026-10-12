import json
from datetime import date

from automation.q104_i22_filing_arrival_compiler import compile_rows, mutation_tests, target_cik_mapping

def rows():
    return [
        {"form":"8-K","filingDate":"2025-09-22","acceptanceDateTime":"2025-09-22T18:00:00Z","accessionNumber":"A1"},
        {"form":"8-K/A","filingDate":"2025-09-23","acceptanceDateTime":"2025-09-23T18:00:00Z","accessionNumber":"A2"},
        {"form":"10-Q","filingDate":"2025-09-24","acceptanceDateTime":"2025-09-24T18:00:00Z","accessionNumber":"A3"},
    ]

def test_i22_filters_fixed_forms_and_preserves_accessions():
    out=compile_rows(rows(), date(2025,9,30))
    assert out["filing_count"]==3
    assert [x["accession"] for x in out["events"]]==["A1","A2","A3"]

def test_i22_is_invariant_to_input_order_and_future_rows():
    result=mutation_tests([{"symbol":"X","cik":"1","raw_rows":rows(),"compiled":compile_rows(rows()),"source_sha256":"x"}])
    assert all(result.values())

def test_i22_ignores_future_cutoff():
    base=compile_rows(rows(), date(2025,9,24))
    future=rows()+[{"form":"8-K","filingDate":"2025-12-01","acceptanceDateTime":"2025-12-01T18:00:00Z","accessionNumber":"FUTURE"}]
    assert base==compile_rows(future, date(2025,9,24))


def test_i22_density_uses_actual_xnys_sessions_not_event_sessions():
    sparse = [
        {"form":"8-K","filingDate":"2025-01-02","acceptanceDateTime":"2025-01-02T18:00:00Z","accessionNumber":"EARLY"},
        {"form":"8-K","filingDate":"2025-03-03","acceptanceDateTime":"2025-03-03T18:00:00Z","accessionNumber":"LATE"},
    ]
    out = compile_rows(sparse, date(2025,3,5))
    late_session = next(
        row["eligible_session"]
        for row in out["events"]
        if row["accession"] == "LATE"
    )
    late_density = next(
        row for row in out["arrival_density_20"]
        if row["decision_session"] == late_session
    )
    assert late_density["arrival_count_20"] == 1
    assert late_density["window_session_count"] == 20


def test_i22_target_cik_mapping_ignores_unrelated_catalog_order():
    target_rows = [
        {"ticker":"SPGI","cik_str":64040},
        {"ticker":"NDAQ","cik_str":1120193},
        {"ticker":"AMP","cik_str":820027},
        {"ticker":"RJF","cik_str":720005},
        {"ticker":"WMB","cik_str":107263},
        {"ticker":"VLO","cik_str":1035002},
        {"ticker":"DVN","cik_str":1090012},
        {"ticker":"EMN","cik_str":915389},
    ]
    first = {str(i): row for i, row in enumerate(target_rows)}
    second_rows = list(reversed(target_rows)) + [
        {"ticker":"UNRELATED","cik_str":9999999}
    ]
    second = {str(i): row for i, row in enumerate(second_rows)}

    expected = {
        "SPGI":64040, "NDAQ":1120193, "AMP":820027, "RJF":720005,
        "WMB":107263, "VLO":1035002, "DVN":1090012, "EMN":915389,
    }
    assert target_cik_mapping(first) == expected
    assert target_cik_mapping(second) == expected
