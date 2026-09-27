from __future__ import annotations

from automation import q024_treasury_auction_result_timestamp_pit_feasibility as q024


def test_result_pdf_candidates_are_official_and_deterministic():
    urls = q024._candidate_result_urls({
        "auction_date": "2025-08-06",
        "cusip": "91282CNT4",
    })
    assert len(urls) == q024.MAX_RESULT_SEQUENCE
    assert urls[0].endswith("/2025/R_20250806_1.pdf")
    assert all(url.startswith(q024.RESULT_PDF_BASE) for url in urls)


def test_pdf_matching_requires_result_identity_and_bid_to_cover():
    event = {
        "auction_date": "2025-08-06",
        "cusip": "91282CNT4",
    }
    text = """
    TREASURY AUCTION RESULTS
    Term and Type of Security: 10-Year Note
    CUSIP Number: 91282CNT4
    Bid-to-Cover Ratio: 2.35
    """
    assert q024._pdf_matches(text, event)
    assert not q024._pdf_matches(text.replace("10-Year Note", "10-Year TIPS"), event)
    assert not q024._pdf_matches(text.replace("91282CNT4", "91282CXX9"), event)
    assert not q024._pdf_matches(text.replace("Bid-to-Cover Ratio:", "Other Ratio:"), event)


def test_rss_pubdate_is_normalized_to_utc():
    xml = b"""<rss><channel><item>
    <title>10-Year Note 91282CNT4</title>
    <link>https://www.treasurydirect.gov/instit/annceresult/press/preanre/2025/R_20250806_2.pdf</link>
    <pubDate>Wed, 06 Aug 2025 13:00:00 GMT</pubDate>
    <guid>R_20250806_2.pdf</guid>
    </item></channel></rss>"""
    items = q024._parse_rss(xml)
    assert items[0]["publication_timestamp_utc"] == "2025-08-06T13:00:00Z"


def test_rss_match_requires_cusip_and_auction_identity():
    event = {
        "auction_date": "2025-08-06",
        "cusip": "91282CNT4",
        "bid_to_cover_ratio": "2.35",
    }
    pdf = {"source_url": "https://www.treasurydirect.gov/instit/annceresult/press/preanre/2025/R_20250806_2.pdf"}
    items = [{
        "title": "10-Year Note 91282CNT4",
        "description": "Bid-to-Cover Ratio: 2.35",
        "link": pdf["source_url"],
        "guid": "R_20250806_2.pdf",
        "pubDate": "Wed, 06 Aug 2025 13:00:00 GMT",
        "publication_timestamp_utc": "2025-08-06T13:00:00Z",
    }]
    match = q024._find_rss_match(event, items)
    assert match is not None
    assert match["publication_timestamp_utc"] == "2025-08-06T13:00:00Z"


def test_rss_match_rejects_pdf_identity_without_event_and_signal_identity():
    event = {"auction_date": "2025-08-06", "cusip": "91282CNT4"}
    pdf = {"source_url": "https://www.treasurydirect.gov/instit/annceresult/press/preanre/2025/R_20250806_2.pdf"}
    items = [{
        "title": "10-Year Note Auction Results",
        "description": "",
        "link": pdf["source_url"],
        "guid": "R_20250806_2.pdf",
        "pubDate": "Wed, 06 Aug 2025 13:00:00 GMT",
        "publication_timestamp_utc": "2025-08-06T13:00:00Z",
    }]
    assert q024._find_rss_match(event, items) is None


def test_rss_match_requires_cusip_auction_date_and_q019_signal():
    event = {
        "auction_date": "2025-08-06",
        "cusip": "91282CNT4",
        "bid_to_cover_ratio": "2.35",
    }
    pdf = {"source_url": "https://example.test/R_20250806_2.pdf"}
    items = [{
        "title": "10-Year Note 91282CNT4 Auction Results",
        "description": "Bid-to-Cover Ratio: 2.35",
        "link": pdf["source_url"],
        "guid": "R_20250806_2.pdf",
        "pubDate": "Wed, 06 Aug 2025 13:00:00 GMT",
        "publication_timestamp_utc": "2025-08-06T13:00:00Z",
    }]
    assert q024._find_rss_match(event, items) is not None
    items[0]["description"] = "Bid-to-Cover Ratio: 2.36"
    assert q024._find_rss_match(event, items) is None


def test_q024_governance_is_feasibility_only():
    assert q024.MIN_TIMESTAMP_COVERAGE == 1.0
