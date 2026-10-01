import json
from datetime import date

from automation.q104_i22_filing_arrival_compiler import compile_rows, mutation_tests

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
