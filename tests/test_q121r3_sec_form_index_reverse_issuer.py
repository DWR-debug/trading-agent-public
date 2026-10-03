from automation.q121r3_sec_form_index_reverse_issuer import (
    accession_from_filename,
    index_url,
    parse_index,
    within_window,
)


def test_index_urls_are_fixed_quarterly():
    assert index_url(2024, 1).endswith("/2024/QTR1/form.idx")
    assert index_url(2025, 3).endswith("/2025/QTR3/form.idx")


def test_accession_parser():
    value = "edgar/data/820027/000119312524258276/0001193125-24-258276-index.htm"
    assert accession_from_filename(value) == "0001193125-24-258276"


def test_parse_filters_to_beneficial_forms():
    def row(form, company, cik, filed, filename):
        return (
            f"{form:<12}{company:<58}{cik:<12}{filed:<12}{filename}"
        ).encode()

    body = b"\n".join([
        b"Form Index header",
        b"Form Type   Company Name                                              CIK         Date Filed  File Name",
        b"-" * 140,
        row(
            "SC 13G/A",
            "S&P Global Inc.",
            "64040",
            "2024-02-13",
            "edgar/data/64040/000110465924021877/0001104659-24-021877-index.htm",
        ),
        row(
            "10-Q",
            "S&P Global Inc.",
            "64040",
            "2024-02-13",
            "edgar/data/64040/000000000000000000/0000000000-24-000000-index.htm",
        ),
    ])
    rows = parse_index(body)
    assert len(rows) == 1
    assert rows[0]["form"] == "SC 13G/A"
    assert rows[0]["cik"] == "0000064040"


def test_window_boundaries():
    assert within_window("2024-02-05")
    assert within_window("2025-09-24")
    assert not within_window("2024-02-04")
    assert not within_window("2025-09-25")


def test_parse_fixed_width_form_index():
    from automation.q121r3_sec_form_index_reverse_issuer import parse_index

    body = (
        "Description: Form Index of EDGAR Dissemination Feed\\n"
        "Form Type   Company Name                                              CIK         Date Filed  File Name\\n"
        "----------------------------------------------------------------------------------------------------------------\\n"
        "SC 13G      SPGI TEST COMPANY                                          64040       2024-02-13  edgar/data/64040/000110465924021877.txt\\n"
    ).encode("latin-1")
    assert parse_index(body) == [{
        "cik": "0000064040",
        "company_name": "SPGI TEST COMPANY",
        "form": "SC 13G",
        "filed_date": "2024-02-13",
        "filename": "edgar/data/64040/000110465924021877.txt",
    }]
