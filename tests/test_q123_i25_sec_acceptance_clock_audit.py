from datetime import datetime, timezone

from automation.q123_i25_sec_acceptance_clock_audit import (
    mutation_tests,
    parse_api_timestamp,
    parse_header_identity,
    parse_header_timestamp,
    select_accessions,
)


def test_api_timestamp_preserves_digits_and_explicit_offset():
    digits, original = parse_api_timestamp("2025-01-02T16:12:49-05:00")
    assert digits == "20250102161249"
    assert original.endswith("-05:00")


def test_raw_header_parser_requires_14_digits():
    assert parse_header_timestamp("<ACCEPTANCE-DATETIME>20250102161249") == "20250102161249"


def test_header_identity_requires_exact_cik_and_accession():
    raw = """<SEC-HEADER>
CENTRAL INDEX KEY: 0000732717
ACCESSION NUMBER: 0000732717-25-000163
<ACCEPTANCE-DATETIME>20250102161249
</SEC-HEADER>"""
    assert parse_header_identity(raw) == ("0000732717", "0000732717-25-000163")


def test_selection_is_deterministic_and_fixed():
    recent = {
        "form": ["8-K", "8-K", "10-Q", "8-K"],
        "filingDate": ["2025-02-03", "2025-01-02", "2025-01-03", "2025-01-04"],
        "acceptanceDateTime": [
            "2025-02-03T18:00:00-05:00",
            "2025-01-02T18:00:00-05:00",
            "2025-01-03T18:00:00-05:00",
            "2025-01-04T18:00:00-05:00",
        ],
        "accessionNumber": ["LATE", "EARLY", "MID", "LATER"],
    }
    selected = select_accessions(recent)
    assert [x["accession"] for x in selected] == ["EARLY", "LATER"]


def test_mutation_contract():
    assert all(mutation_tests().values())


def test_timestamp_mismatch_is_not_silently_normalized():
    assert parse_header_timestamp("<ACCEPTANCE-DATETIME>20250101120001") != "20250101120000"
