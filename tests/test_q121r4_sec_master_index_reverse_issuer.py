from automation.q121r4_sec_master_index_reverse_issuer import accession_from_filename,filing_index_url,index_url,parse_master,within_window

def test_master_route_is_quarterly():
    assert index_url(2024,1).endswith("/2024/QTR1/master.idx")

def test_accession_parser():
    assert accession_from_filename("edgar/data/64040/000110465924021877/0001104659-24-021877-index.htm")=="0001104659-24-021877"

def test_pipe_delimited_master_parser_filters_forms():
    body=b"\n".join([
      b"Description header",
      b"CIK|Company Name|Form Type|Date Filed|Filename",
      b"--------------------------------------------------------------------------------",
      b"0000064040|S&P Global Inc.|SC 13G/A|2024-02-13|edgar/data/64040/000110465924021877/0001104659-24-021877.txt",
      b"0000064040|S&P Global Inc.|10-Q|2024-02-13|edgar/data/64040/000006404024000010/0000064040-24-000010.txt"
    ])
    rows=parse_master(body)
    assert len(rows)==2
    assert rows[0]["form"]=="SC 13G/A"
    assert rows[0]["cik"]=="0000064040"

def test_window():
    assert within_window("2024-02-05")
    assert within_window("2025-09-24")
    assert not within_window("2024-02-04")
    assert not within_window("2025-09-25")


def test_master_parser_preserves_same_accession_across_ciks():
    body = b"\n".join([
        b"CIK|Company Name|Form Type|Date Filed|Filename",
        b"1|Company A|SC 13G/A|2024-02-13|edgar/data/1/000110465924021877/0001104659-24-021877.txt",
        b"2|Person B|SC 13G/A|2024-02-13|edgar/data/2/000110465924021877/0001104659-24-021877.txt",
    ])
    rows = parse_master(body)
    assert len(rows) == 2
    assert {row["cik"] for row in rows} == {"0000000001", "0000000002"}


def test_filing_index_url_is_derived_from_submission_path():
    value = "edgar/data/64040/000110465924021877/0001104659-24-021877.txt"
    assert filing_index_url(value).endswith("/000110465924021877/0001104659-24-021877-index.htm")


def test_header_url_uses_submission_header_endpoint():
    from automation.q121r4_sec_master_index_reverse_issuer import header_url
    assert header_url("edgar/data/820027/000119312524258276/0001193125-24-258276-index.htm").endswith(
        "/0001193125-24-258276-index-headers.html"
    )
