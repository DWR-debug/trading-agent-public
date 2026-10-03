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
    body = (
        b"CIK|Company Name|Form Type|Date Filed|Filename\\n"
        b"0000820027|American|SC 13G|2024-11-14|edgar/data/820027/000119312524258276/0001193125-24-258276-index.htm\\n"
        b"0000820027|American|10-Q|2024-11-14|edgar/data/820027/000000000000000000/0000000000-24-000000-index.htm\\n"
    )
    rows = parse_index(body)
    assert len(rows) == 1
    assert rows[0]["form"] == "SC 13G"


def test_window_boundaries():
    assert within_window("2024-02-05")
    assert within_window("2025-09-24")
    assert not within_window("2024-02-04")
    assert not within_window("2025-09-25")
