from __future__ import annotations

from automation.q198_pit_clock_census import (
    FROZEN_DATES,
    HISTORICAL_API_TEMPLATE,
    _is_access_blocked,
    parse_public_inspection,
    parse_public_inspection_api,
)


SAMPLE = """
# 01/10/2020 Public Inspection Issue
# Special Filing
Filed on:01/10/2020 at 4:15 pmScheduled Pub. Date:01/13/2020FR Document:[2020-00469]
# Regular Filing
Filed on:01/10/2020 at 8:45 amScheduled Pub. Date:01/13/2020FR Document:[2020-00152]
Filed on:01/09/2020 at 11:15 amScheduled Pub. Date:01/13/2020FR Document:[2020-00373]
"""


def test_frozen_date_set_is_fixed_and_spans_history():
    assert FROZEN_DATES == (
        "2020/01/10",
        "2020/04/22",
        "2020/12/16",
        "2026/10/02",
    )


def test_parser_extracts_filing_and_publication_clock():
    d = parse_public_inspection(SAMPLE)
    assert d["page_date"] == "2020-01-10"
    assert d["regular_or_special_sections_present"]["regular"] is True
    assert d["regular_or_special_sections_present"]["special"] is True
    assert d["filing_records"] == 3
    assert d["records_with_filed_timestamp"] == 3
    assert d["records_with_scheduled_publication_date"] == 3
    assert d["same_day_clock_ambiguous_count"] == 0



def test_api_parser_does_not_equate_partial_timestamp_coverage_with_complete_coverage():
    import json as _json

    sample = {
        "count": 2,
        "results": [
            {
                "document_number": "a",
                "filed_at": "2020-12-16T08:45:00.000-05:00",
                "publication_date": "2020-12-17",
                "last_public_inspection_issue": "2020-12-16",
            },
            {
                "document_number": "b",
                "filed_at": None,
                "publication_date": None,
                "last_public_inspection_issue": "2020-12-16",
            },
        ],
    }
    d = parse_public_inspection_api(_json.dumps(sample), "2020-12-16")
    assert d["filing_records"] == 2
    assert d["records_with_filed_timestamp"] == 1
    assert d["records_with_scheduled_publication_date"] == 1
    assert d["missing_filed_timestamp_count"] == 1
    assert d["missing_publication_date_count"] == 1


def test_parser_rejects_ambiguous_same_day_record():
    ambiguous = """
    # 01/10/2020 Public Inspection Issue
    Filed on:01/10/2020 at 8:45 amScheduled Pub. Date:01/10/2020FR Document:[x]
    """
    d = parse_public_inspection(ambiguous)
    assert d["same_day_clock_ambiguous_count"] == 1



def test_historical_api_contract_is_fixed_and_non_authorizing():
    assert "conditions%5Bavailable_on%5D={date}" in HISTORICAL_API_TEMPLATE
    sample = {
        "count": 2,
        "results": [
            {
                "document_number": "2020-08581",
                "filed_at": "2020-04-21T08:45:00.000-04:00",
                "publication_date": "2020-04-22",
                "last_public_inspection_issue": "2020-04-22",
                "filing_type": "regular",
                "editorial_note": None,
            },
            {
                "document_number": "2020-06967",
                "filed_at": "2020-04-20T16:15:00.000-04:00",
                "publication_date": "2020-04-30",
                "last_public_inspection_issue": "2020-04-29",
                "filing_type": "special",
                "editorial_note": "A correction was made while on public inspection.",
            },
        ],
    }
    d = parse_public_inspection_api(__import__("json").dumps(sample), "2020-04-22")
    assert d["source_route"] == "official_api_by_date"
    assert d["api_count"] == 2
    assert d["records_with_filed_timestamp"] == 2
    assert d["correction_or_withdrawal_note_count"] == 1
    assert d["scientific_boundary"]["performance"] is False
    assert d["scientific_boundary"]["promotion"] is False
    assert d["safety"]["paper_only"] is True


def test_source_boundary_is_non_authorizing():
    d = parse_public_inspection(SAMPLE)
    assert d["scientific_boundary"]["performance"] is False
    assert d["scientific_boundary"]["selection"] is False
    assert d["scientific_boundary"]["promotion"] is False
    assert d["safety"]["paper_only"] is True
    assert d["safety"]["live_trading_enabled"] is False


def test_parser_accepts_raw_html_source():
    html = """
    <html><body>
    <h1>01/10/2020 Public Inspection Issue</h1>
    <h2>Special Filing</h2>
    <p>Filed on: 01/10/2020 at 4:15 pm</p>
    <p>Scheduled Pub. Date: 01/13/2020</p>
    <h2>Regular Filing</h2>
    <p>Filed on: 01/10/2020 at 8:45 am</p>
    <p>Scheduled Pub. Date: 01/13/2020</p>
    </body></html>
    """
    d = parse_public_inspection(html)
    assert d["page_date"] == "2020-01-10"
    assert d["regular_or_special_sections_present"]["regular"] is True
    assert d["regular_or_special_sections_present"]["special"] is True
    assert d["filing_records"] == 2
    assert d["records_with_filed_timestamp"] == 2
    assert d["records_with_scheduled_publication_date"] == 2


def test_federal_register_access_challenge_is_explicitly_blocked():
    challenge = """
    <html><body>
    <h1>Request Access</h1>
    <p>Your request has been flagged as potentially automated.</p>
    <p>Due to aggressive automated scraping of FederalRegister.gov.</p>
    <a href="https://unblock.federalregister.gov/">Request Access</a>
    <div class="g-recaptcha"></div>
    </body></html>
    """
    assert _is_access_blocked(challenge) is True
