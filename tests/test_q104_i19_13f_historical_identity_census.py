import io,zipfile
from datetime import date
from automation.q104_i19_13f_historical_identity_census import SHARDS,discover_archives,scan_archive,synthetic_contract

def test_archive_discovery_and_partition():
    page=b'''<a href="/files/structureddata/data/form-13f-data-sets/2013q3_form13f.zip">2013 Q3</a>
    <a href="/files/structureddata/data/form-13f-data-sets/2017q4_form13f.zip">2017 Q4</a>
    <a href="/files/structureddata/data/form-13f-data-sets/2018q1_form13f.zip">2018 Q1</a>
    <a href="/files/data/form-13f-data-sets/01jun2025-31aug2025_form13f.zip">2025 Jun-Aug</a>'''
    a=discover_archives(page)
    assert [x["period_start"] for x in a]==["2013-07-01","2017-10-01","2018-01-01","2025-06-01"]
    assert len([x for x in a if SHARDS["2013-2017"][0]<=date.fromisoformat(x["period_start"])<SHARDS["2013-2017"][1]])==2
    assert len([x for x in a if SHARDS["2022-2025-09"][0]<=date.fromisoformat(x["period_start"])<SHARDS["2022-2025-09"][1]])==1

def test_future_filing_is_excluded():
    sub="ACCESSION_NUMBER\tFILING_DATE\tPERIODOFREPORT\nA1\t01-JUL-2017\t30-JUN-2017\nA2\t01-NOV-2025\t30-SEP-2025\n"
    info="ACCESSION_NUMBER\tNAMEOFISSUER\tTITLEOFCLASS\tCUSIP\nA1\tOld Name Corp\tCommon Stock\t78409V104\nA2\tFuture Name Corp\tCommon Stock\t78409V104\n"
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:z.writestr("SUBMISSION.tsv",sub);z.writestr("INFOTABLE.tsv",info)
    r=scan_archive(b.getvalue(),{"url":"synthetic://q104","label":"2017 Q3","period_start":"2017-07-01"},{"SPGI":{"78409V104"}})
    assert r["target_hits"]["SPGI"]["row_count"]==1
    assert r["target_hits"]["SPGI"]["issuer_names"]==["Old Name Corp"]

def test_synthetic_contract():
    assert all(synthetic_contract().values())


def test_frozen_source_page_loader(tmp_path):
    from automation.q104_i19_13f_historical_identity_census import load_page
    p=tmp_path/"source_page.html"
    payload=b"<html>frozen</html>"
    p.write_bytes(payload)
    assert load_page(p)==payload


def test_accession_header_url_uses_filer_cik_and_normalized_accession():
    from automation.q104_i19_13f_historical_identity_census import accession_header_url
    assert accession_header_url("0001045810", "0001045810-26-000065") == "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000065/0001045810-26-000065-index-headers.html"


def test_parse_acceptance_header_validates_identity_and_timestamp():
    from automation.q104_i19_13f_historical_identity_census import parse_acceptance_header
    raw="""<SEC-HEADER>\nACCESSION NUMBER: 0001045810-26-000065\nCONFORMED SUBMISSION TYPE: 13F-HR\nPUBLIC DOCUMENT COUNT: 3\nCONFORMED PERIOD OF REPORT: 20260331\nFILED AS OF DATE: 20260515\nCENTRAL INDEX KEY: 0001045810\n<ACCEPTANCE-DATETIME>20260515161542\n</SEC-HEADER>"""
    assert parse_acceptance_header(raw,"0001045810","0001045810-26-000065","13F-HR","2026-05-15") == "2026-05-15T16:15:42"


def test_parse_acceptance_header_fails_closed_on_identity_mismatch():
    import pytest
    from automation.q104_i19_13f_historical_identity_census import parse_acceptance_header
    raw="""ACCESSION NUMBER: 0001045810-26-000065\nCONFORMED SUBMISSION TYPE: 13F-HR\nFILED AS OF DATE: 20260515\nCENTRAL INDEX KEY: 0001045810\n<ACCEPTANCE-DATETIME>20260515161542"""
    with pytest.raises(ValueError, match="ACCESSION_MISMATCH"):
        parse_acceptance_header(raw,"0001045810","0001045810-26-999999","13F-HR","2026-05-15")
    with pytest.raises(ValueError, match="FILER_CIK_MISMATCH"):
        parse_acceptance_header(raw,"0009999999","0001045810-26-000065","13F-HR","2026-05-15")


def test_scan_archive_counts_unique_target_accessions():
    from automation.q104_i19_13f_historical_identity_census import scan_archive
    sub="ACCESSION_NUMBER\tFILING_DATE\tPERIODOFREPORT\tCIK\tSUBMISSIONTYPE\n0001045810-26-000065\t15-MAY-2025\t31-MAR-2025\t0001045810\t13F-HR\n"
    info="ACCESSION_NUMBER\tNAMEOFISSUER\tTITLEOFCLASS\tCUSIP\n0001045810-26-000065\tIssuer A\tCommon Stock\t78409V104\n0001045810-26-000065\tIssuer B\tCommon Stock\t999999999\n"
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("SUBMISSION.tsv",sub); z.writestr("INFOTABLE.tsv",info)
    r=scan_archive(b.getvalue(),{"url":"synthetic://unique","label":"unique","period_start":"2026-04-01"},{"SPGI":{"78409V104"},"OTHER":{"78409V104"}})
    assert r["target_unique_accession_count"] == 1


def test_q104_i19_workflow_has_exactly_one_bounded_retry():
    workflow = (Path(__file__).parents[1] / ".github/workflows/q104-i19-13f-historical-identity-census.yml").read_text(encoding="utf-8")
    assert "permissions:" in workflow
    assert "actions: write" in workflow
    assert workflow.count("retry_failed:") == 1
    assert "github.run_attempt == 1" in workflow
    assert 'gh run rerun "$GITHUB_RUN_ID" --failed' in workflow
