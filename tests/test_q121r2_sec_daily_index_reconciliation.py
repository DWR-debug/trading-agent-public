from automation.q121r2_sec_daily_index_reconciliation import (
    accession_from_filename,
    daily_master_index_url,
    normalize_accession,
    parse_master_index,
)

def test_daily_master_index_url_quarter_mapping():
    assert daily_master_index_url("2025-09-24").endswith("/2025/QTR3/master.20250924.idx")
    assert daily_master_index_url("2024-02-05").endswith("/2024/QTR1/master.20240205.idx")
    assert daily_master_index_url("2024-12-31").endswith("/2024/QTR4/master.20241231.idx")

def test_parse_master_index():
    body = (
        "Description: Master Index of EDGAR Dissemination Feed\n"
        "CIK|Company Name|Form Type|Date Filed|File Name\n"
        "1234567890|Example Filing LLC|SC 13G|2025-09-24|edgar/data/1234567890/000123456725000001/a-index.html\n"
    ).encode("latin-1")
    rows = parse_master_index(body)
    assert rows == [{
        "cik": "1234567890",
        "company_name": "Example Filing LLC",
        "form": "SC 13G",
        "filed_date": "2025-09-24",
        "filename": "edgar/data/1234567890/000123456725000001/a-index.html",
    }]

def test_accession_parsing():
    assert normalize_accession("0001234567-25-000001") == "0001234567-25-000001"
    assert accession_from_filename("edgar/data/1234567890/000123456725000001/a-index.html") == "0001234567-25-000001"
