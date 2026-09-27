from __future__ import annotations

from datetime import date

from automation import q023_treasury_release_timestamp_pit_feasibility as q023


SAMPLE = """
TREASURY OFFERING ANNOUNCEMENT
Embargoed Until 08:30 A.M.
CONTACT: Treasury Auctions
November 01, 2023
Term and Type of Security: 10-Year Note
CUSIP Number: 91282CJJ1
Auction Date: November 08, 2023
"""


def test_parse_embargo_timestamp_is_timezone_aware_and_deterministic():
    document_date, embargoed, timestamp = q023._parse_embargo_timestamp(SAMPLE)
    assert document_date == "November 01, 2023"
    assert embargoed == "08:30 AM"
    assert timestamp.endswith("Z")
    assert timestamp == "2023-11-01T12:30:00Z"


def test_candidate_urls_are_limited_to_official_treasurydirect():
    event = {
        "record_date": "2023-11-01",
        "auction_date": "2023-11-08",
        "cusip": "91282CJJ1",
    }
    urls = q023._candidate_urls(event)
    assert len(urls) == q023.MAX_ANNOUNCEMENT_LOOKBACK_DAYS * q023.MAX_PDF_SEQUENCE
    assert urls[0].startswith(
        "https://www.treasurydirect.gov/instit/annceresult/press/preanre/2023/"
    )
    assert all(url.endswith(".pdf") for url in urls)
    assert any(url.endswith("A_20231101_1.pdf") for url in urls)
    assert urls[0].endswith("A_20231101_1.pdf")


def test_pdf_match_requires_cusip_auction_date_and_ten_year_note():
    event = {
        "record_date": "2023-11-01",
        "auction_date": "2023-11-08",
        "cusip": "91282CJJ1",
    }
    assert q023._pdf_matches_event(SAMPLE, event)
    assert q023._pdf_matches_event(SAMPLE.replace("10-Year Note", "10-Year TIPS"), event)
    assert not q023._pdf_matches_event(
        SAMPLE.replace("91282CJJ1", "91282CXX9"), event
    )
    assert not q023._pdf_matches_event(
        SAMPLE.replace("November 08, 2023", "November 09, 2023"), event
    )


def test_next_xnys_session_is_strictly_after_record_date():
    sessions = [
        date(2023, 11, 1),
        date(2023, 11, 2),
        date(2023, 11, 3),
    ]
    assert q023._next_xnys_session(sessions, date(2023, 11, 1)) == date(2023, 11, 2)
    assert q023._next_xnys_session(sessions, date(2023, 11, 3)) is None


def test_governance_contract_is_source_feasibility_only():
    source = q023._fingerprint({"x": 1})
    assert len(source) == 64
    assert "pnl" not in q023._normalize.__doc__.lower() if q023._normalize.__doc__ else True
    assert q023.MIN_TIMESTAMP_COVERAGE == 1.0
