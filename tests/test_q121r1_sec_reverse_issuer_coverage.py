from automation.q121r1_sec_reverse_issuer_coverage import (
    deterministic_sample,
    extract_labeled_cik,
    extract_accepted,
    parse_atom_entries,
    browse_url,
)

def test_atom_parser_preserves_accession_and_filing_link():
    body = b'''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
    <entry><accession-nunber>0001234567-24-000001</accession-nunber>
    <filing-date>2024-02-05</filing-date><filing-type>SC 13G</filing-type>
    <title>SC 13G</title>
    <link rel="alternate" href="https://www.sec.gov/Archives/edgar/data/111/abc-index.htm"/>
    </entry></feed>'''
    rows = parse_atom_entries(body)
    assert rows == [{
        "accession_number": "0001234567-24-000001",
        "filing_date": "2024-02-05",
        "filing_type": "SC 13G",
        "title": "SC 13G",
        "filing_href": "https://www.sec.gov/Archives/edgar/data/111/abc-index.htm",
    }]

def test_identity_parser_distinguishes_subject_and_filer():
    text = "Example Co. (Subject) CIK: 0000123456 Some Filer (Filed by) CIK: 0000654321"
    assert extract_labeled_cik(text, "Subject") == "0000123456"
    assert extract_labeled_cik(text, "Filed by") == "0000654321"

def test_acceptance_parser_is_explicit():
    assert extract_accepted("Accepted 2024-02-05 17:53:54") == "2024-02-05 17:53:54"

def test_deterministic_sample_positions():
    rows = [{"accession_number": str(i)} for i in range(5)]
    out = deterministic_sample(rows)
    assert [x["accession_number"] for x in out] == ["0", "2", "4"]

def test_browse_url_freezes_dates_and_form():
    url = browse_url("0000123456", "SC 13G/A", 200)
    assert "CIK=0000123456" in url
    assert "type=SC+13G%2FA" in url
    assert "datea=20240205" in url
    assert "dateb=20250924" in url
    assert "start=200" in url
    assert "output=atom" in url

def test_governance_boundary_is_source_only():
    import automation.q121r1_sec_reverse_issuer_coverage as mod
    assert mod.START == "20240205"
    assert mod.END == "20250924"
    assert "performance" not in mod.browse_url("0000123456", "SC 13G", 0).lower()
