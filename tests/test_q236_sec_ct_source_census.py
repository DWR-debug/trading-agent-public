from automation.q236_sec_ct_source_census import (
    accession_from_filename,
    extract_detail_metadata,
    parse_index,
    quarter_list,
    sample_rows,
)


def test_fixed_quarter_window():
    q = quarter_list()
    assert q[0] == (2015, 1)
    assert q[-1] == (2025, 4)
    assert len(q) == 44


def test_parse_ct_order_fixed_width():
    row = (
        "CT ORDER    EXAMPLE COMPANY                                           "
        "12345       2018-02-09  "
        "edgar/data/12345/999999999718000747/9999999997-18-000747-index.htm"
    ).encode("latin-1")
    rows = parse_index(row)
    assert len(rows) == 1
    assert rows[0]["form"] == "CT ORDER"
    assert rows[0]["cik"] == "0000012345"
    assert rows[0]["filed_date"] == "2018-02-09"


def test_compact_date_and_accession():
    row = (
        "CT ORDER    EXAMPLE COMPANY                                           "
        "12345       20180209      edgar/data/12345/999999999718000747/9999999997-18-000747-index.htm"
    ).encode("latin-1")
    rows = parse_index(row)
    assert rows[0]["filed_date"] == "2018-02-09"
    assert accession_from_filename(rows[0]["filename"]) == "9999999997-18-000747"


def test_out_of_window_is_dropped():
    row = (
        "CT ORDER    EXAMPLE COMPANY                                           "
        "12345       20140209      edgar/data/12345/999999999714000747/9999999997-14-000747-index.htm"
    ).encode("latin-1")
    assert parse_index(row) == []


def test_deterministic_sample_first_median_last_per_year():
    rows = [
        {"filed_date":"2020-01-01","filename":"edgar/data/1/000000000020000001/a-index.htm","cik":"0000000001","company_name":"A","form":"CT ORDER"},
        {"filed_date":"2020-02-01","filename":"edgar/data/2/000000000020000002/b-index.htm","cik":"0000000002","company_name":"B","form":"CT ORDER"},
        {"filed_date":"2020-03-01","filename":"edgar/data/3/000000000020000003/c-index.htm","cik":"0000000003","company_name":"C","form":"CT ORDER"},
        {"filed_date":"2021-01-01","filename":"edgar/data/4/000000000021000001/d-index.htm","cik":"0000000004","company_name":"D","form":"CT ORDER"},
    ]
    sampled = sample_rows(rows)
    assert len(sampled) == 4
    assert [r["filename"] for r in sampled] == [
        "edgar/data/1/000000000020000001/a-index.htm",
        "edgar/data/2/000000000020000002/b-index.htm",
        "edgar/data/3/000000000020000003/c-index.htm",
        "edgar/data/4/000000000021000001/d-index.htm",
    ]


def test_accession_filename_without_archive_directory():
    filename = "edgar/data/7032/999999999720001304.txt"
    assert accession_from_filename(filename) == "9999999997-20-001304"


def test_extract_detail_metadata_acceptance_fallback():
    html = """
    <html><body>
      Form CT ORDER - Confidential treatment order
      SEC Accession No. 9999999997-15-010856
      Filing Date 2015-06-15
      Accepted 2015-06-15 16:22:10
    </body></html>
    """
    meta = extract_detail_metadata(html)
    assert meta["accession"] == "9999999997-15-010856"
    assert meta["form"] == "CT ORDER"
    assert meta["filed_date"] == "2015-06-15"
    assert meta["accepted_datetime"] == "2015-06-15T16:22:10"


def test_submission_text_url_preserves_dashed_ct_order_accession():
    from automation.q236_sec_ct_source_census import submission_text_url
    url = submission_text_url("edgar/data/1368148/999999999715010856/9999999997-15-010856-index.htm")
    assert url.endswith("/999999999715010856/9999999997-15-010856.txt")
