from automation.q104_i19_historical_pit_compiler import local_name, numeric_clean


def test_numeric_clean_applies_parentheses_sign_and_scale():
    assert numeric_clean("(1,200)", "", "0") == "-1200"
    assert numeric_clean("12", "-", "3") == "-12000"


def test_local_name_normalizes_qname_forms():
    assert local_name("us-gaap:Assets") == "assets"
    assert local_name("{http://www.xbrl.org/2003/instance}context") == "context"


def test_historical_compiler_imports_as_preperformance_only():
    from automation.q104_i19_historical_pit_compiler import CUTOFF, START
    assert START.isoformat() == "2013-07-01"
    assert CUTOFF.isoformat() == "2025-09-24"


def test_missing_census_fails_closed(tmp_path, monkeypatch):
    import automation.q104_i19_historical_pit_compiler as compiler
    monkeypatch.setattr(compiler, "CENSUS", tmp_path / "missing.json")
    try:
        compiler.require_census()
    except RuntimeError as exc:
        assert "CENSUS_RECEIPT_MISSING" in str(exc)
    else:
        raise AssertionError("historical compiler must require the positive census receipt")



def test_rejects_legacy_source_only_census_without_acceptance_time_join():
    import pytest
    from automation.q104_i19_historical_pit_compiler import validate_census_receipt

    legacy = {
        "candidate_id": "Q104:I19",
        "status": "13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_COMPLETED_SOURCE_ONLY",
        "completed_shards": ["2013-2017", "2018-2021", "2022-2025-09"],
        "archive_count": 50,
        "identity_conflicts": [],
    }
    with pytest.raises(RuntimeError, match="CENSUS_NOT_CLOCK_COMPLETE"):
        validate_census_receipt(legacy)



def test_filing_rows_does_not_require_or_use_json_acceptance_clock():
    from automation.q104_i19_historical_pit_compiler import filing_rows

    payload = {
        "filings": {
            "recent": {
                "accessionNumber": ["0000000123-19-000001"],
                "form": ["10-K"],
                "filingDate": ["2019-03-11"],
                "reportDate": ["2018-12-31"],
                "primaryDocument": ["a.html"],
                "isInlineXBRL": [True],
                "acceptanceDateTime": ["2019-03-11T16:57:59Z"],
            }
        }
    }
    rows = filing_rows(payload)
    assert len(rows) == 1
    assert rows[0]["accessionNumber"] == "0000000123-19-000001"


def test_filing_facts_uses_raw_header_clock_not_submission_json(monkeypatch):
    import hashlib
    import json
    import automation.q104_i19_historical_pit_compiler as compiler

    accession = "0000000123-19-000001"
    header_url = (
        "https://www.sec.gov/Archives/edgar/data/123/"
        "000000012319000001/0000000123-19-000001-index-headers.html"
    )
    header = (
        "<SEC-HEADER>\n"
        "ACCESSION NUMBER: 0000000123-19-000001\n"
        "CONFORMED SUBMISSION TYPE: 10-K\n"
        "FILED AS OF DATE: 20190311\n"
        "CENTRAL INDEX KEY: 0000000123\n"
        "<ACCEPTANCE-DATETIME>20190311165759\n"
        "</SEC-HEADER>"
    ).encode("utf-8")

    def fake_fetch(url):
        if url == header_url:
            return header
        if url.endswith("/a.html"):
            return b"<html></html>"
        if url.endswith("/index.json"):
            return json.dumps({"directory": {"item": []}}).encode("utf-8")
        raise AssertionError("Unexpected fetch URL: " + url)

    monkeypatch.setattr(compiler, "fetch", fake_fetch)
    out = compiler.filing_facts("SPGI", "0000000123", {
        "accessionNumber": accession,
        "form": "10-K",
        "filingDate": "2019-03-11",
        "reportDate": "2018-12-31",
        "fp": "FY",
        "primaryDocument": "a.html",
        "isInlineXBRL": True,
        "acceptanceDateTime": "2019-03-11T16:57:59Z",
    })

    assert out["acceptance_datetime"] == "2019-03-11T20:57:59Z"
    assert out["acceptance_datetime_raw_edgar_local"] == "2019-03-11T16:57:59"
    assert out["acceptance_timezone"] == "America/New_York"
    assert out["acceptance_clock_basis"] == "SEC_EDGAR_SGML_ACCEPTANCE_DATETIME"
    assert out["acceptance_source_url"] == header_url
    assert out["acceptance_header_sha256"] == hashlib.sha256(header).hexdigest()
    assert out["acceptance_header_bytes"] == len(header)
