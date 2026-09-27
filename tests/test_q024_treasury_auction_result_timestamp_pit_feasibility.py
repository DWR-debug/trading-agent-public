from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from automation import q024_treasury_auction_result_timestamp_pit_feasibility as q024


EVENT = {
    "record_date": "2025-08-20",
    "auction_date": "2025-08-06",
    "cusip": "91282CNT4",
    "bid_to_cover_ratio": "2.35",
    "security_term": "10-Year",
}


def _result_xml(
    *,
    cusip: str = EVENT["cusip"],
    auction_date: str = EVENT["auction_date"],
    bid_to_cover_ratio: str = "2.35",
    release_time: str = "13:02",
) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <td:AuctionData xmlns:td="http://www.treasurydirect.gov/">
      <AuctionAnnouncement>
        <SecurityType>NOTE</SecurityType>
        <CUSIP>{cusip}</CUSIP>
        <AuctionDate>{auction_date}</AuctionDate>
      </AuctionAnnouncement>
      <AuctionResults>
        <BidToCoverRatio>{bid_to_cover_ratio}</BidToCoverRatio>
        <ReleaseTime>{release_time}</ReleaseTime>
        <ResultsPDFName>R_20250806_2.pdf</ResultsPDFName>
      </AuctionResults>
    </td:AuctionData>
    """.encode()


def test_result_pdf_candidates_are_official_and_deterministic():
    urls = q024._candidate_result_urls(EVENT)
    assert len(urls) == q024.MAX_RESULT_SEQUENCE
    assert urls[0].endswith("/2025/R_20250806_1.pdf")
    assert all(url.startswith(q024.RESULT_PDF_BASE) for url in urls)


def test_pdf_matching_still_requires_result_identity_and_bid_to_cover():
    text = """
    TREASURY AUCTION RESULTS
    Term and Type of Security: 10-Year Note
    CUSIP Number: 91282CNT4
    Bid-to-Cover Ratio: 2.35
    """
    assert q024._pdf_matches(text, EVENT)
    assert not q024._pdf_matches(text.replace("91282CNT4", "91282CXX9"), EVENT)
    assert not q024._pdf_matches(
        text.replace("Bid-to-Cover Ratio:", "Other Ratio:"), EVENT
    )


def test_xml_candidates_use_official_date_sequence_archive():
    urls = q024._candidate_result_xml_urls(EVENT)
    assert len(urls) == q024.MAX_RESULT_SEQUENCE
    assert urls[0] == "https://www.treasurydirect.gov/xml/R_20250806_1.xml"
    assert urls[1] == "https://www.treasurydirect.gov/xml/R_20250806_2.xml"


def test_xml_content_supplies_event_identity_signal_and_release_time():
    parsed = q024._parse_result_xml(_result_xml())
    assert parsed == {
        "cusip": "91282CNT4",
        "auction_date": "2025-08-06",
        "bid_to_cover_ratio": "2.35",
        "release_time": "13:02",
        "results_pdf_name": "R_20250806_2.pdf",
    }
    assert q024._xml_identity_matches(
        parsed, EVENT, "https://www.treasurydirect.gov/xml/R_20250806_2.xml"
    )


def test_xml_matching_requires_cusip_date_ratio_and_file_identity():
    url = "https://www.treasurydirect.gov/xml/R_20250806_2.xml"
    for body in (
        _result_xml(cusip="91282CXX9"),
        _result_xml(auction_date="2025-08-07"),
        _result_xml(bid_to_cover_ratio="2.36"),
        _result_xml().replace(b"R_20250806_2.pdf", b"R_20250806_1.pdf"),
    ):
        assert not q024._xml_identity_matches(
            q024._parse_result_xml(body), EVENT, url
        )


def test_xml_release_time_is_timezone_aware_and_normalized_to_utc():
    timestamp = q024._publication_timestamp(EVENT, "13:02")
    assert timestamp["time_zone"] == "America/New_York"
    assert timestamp["publication_timestamp_local"] == "2025-08-06T13:02:00-04:00"
    assert timestamp["publication_timestamp_utc"] == "2025-08-06T17:02:00Z"

    winter = q024._publication_timestamp(
        {**EVENT, "auction_date": "2025-01-08"}, "13:02"
    )
    assert winter["publication_timestamp_utc"] == "2025-01-08T18:02:00Z"


def test_rss_pubdate_is_normalized_to_utc():
    body = b"""<rss><channel><item>
    <title>10-Year Note 91282CNT4</title>
    <description>&lt;strong&gt;CUSIP:&lt;/strong&gt; 91282CNT4</description>
    <pubDate>Wed, 06 Aug 2025 13:00:00 GMT</pubDate>
    </item></channel></rss>"""
    items = q024._parse_rss(body)
    assert items[0]["publication_timestamp_utc"] == "2025-08-06T13:00:00Z"


def test_xml_resolver_validates_one_matching_official_release_time(monkeypatch):
    def fetch(url):
        if url.endswith("_2.xml"):
            return _result_xml(), {"ETag": '"source-etag"'}
        return None

    monkeypatch.setattr(q024, "_fetch_xml_response", fetch)
    result = q024._resolve_result_xml(EVENT)
    assert result["status"] == "RESULT_TIMESTAMP_VALIDATED"
    assert result["matching_xml_count"] == 1
    assert result["identity"]["bid_to_cover_ratio"] == "2.35"
    assert result["http_metadata"] == {"ETag": '"source-etag"'}
    assert result["attempts"][1]["status"] == "XML_IDENTITY_MATCH"
    assert result["attempts"][0]["status"] == "HTTP_404"
    assert (
        result["publication_timestamp"]["publication_timestamp_utc"]
        == "2025-08-06T17:02:00Z"
    )


def test_xml_resolver_preserves_archive_headers_but_never_uses_last_modified(monkeypatch):
    def fetch(url):
        if url.endswith("_2.xml"):
            return _result_xml(release_time=""), {
                "Last-Modified": "Fri, 22 May 2026 15:17:06 GMT",
                "ETag": '"0x8DEB8152FB2B105"',
            }
        return None

    monkeypatch.setattr(q024, "_fetch_xml_response", fetch)
    result = q024._resolve_result_xml(EVENT)
    assert result["status"] == "RESULT_TIMESTAMP_INSUFFICIENT"
    assert result["identity"]["cusip"] == EVENT["cusip"]
    assert result["http_metadata"]["Last-Modified"].startswith("Fri, 22 May 2026")
    assert result.get("publication_timestamp") is None


def test_xml_resolver_rejects_signal_mismatch(monkeypatch):
    def fetch(url):
        if url.endswith("_2.xml"):
            return _result_xml(bid_to_cover_ratio="2.36"), {}
        return None

    monkeypatch.setattr(q024, "_fetch_xml_response", fetch)
    result = q024._resolve_result_xml(EVENT)
    assert result["status"] == "RESULT_XML_IDENTITY_INSUFFICIENT"
    assert result["matching_xml_count"] == 0
    assert result["attempts"][1]["status"] == "XML_IDENTITY_MISMATCH"


def test_rss_timestamp_requires_unique_cusip_date_and_signal_match():
    item = {
        "title": "10-Year Note Treasury Auction Results",
        "description": (
            "<strong>CUSIP:</strong> 91282CNT4; "
            "<strong>Auction Date:</strong> 08/06/2025; "
            "<strong>Bid-to-Cover Ratio:</strong> 2.35"
        ),
        "link": "https://www.treasurydirect.gov/instit/annceresult/press/press_secannpr.htm",
        "guid": "R_20250806_2.pdf",
        "publication_timestamp_utc": "2025-08-06T17:02:00Z",
    }
    assert q024._find_rss_match(EVENT, [item]) == item
    assert q024._find_rss_match(
        EVENT, [{**item, "description": item["description"].replace("2.35", "2.36")}]
    ) is None
    assert q024._find_rss_match(
        EVENT, [{**item, "description": item["description"].replace("08/06/2025", "08/07/2025")}]
    ) is None
    assert q024._find_rss_match(
        EVENT, [{**item, "description": item["description"].replace("91282CNT4", "91282CXX9")}]
    ) is None
    assert q024._find_rss_match(
        EVENT, [{**item, "description": "Auction Date: 08/06/2025"}]
    ) is None


def test_pit_requires_result_on_auction_date_before_q019_record_date():
    timestamp = q024._publication_timestamp(EVENT, "13:02")
    assert q024._event_pit_status(EVENT, timestamp) == "PIT_VALIDATED"
    assert q024._event_pit_status(
        {**EVENT, "record_date": EVENT["auction_date"]}, timestamp
    ) == "PIT_INSUFFICIENT"
    assert q024._event_pit_status(EVENT, None) == "PIT_INSUFFICIENT"


def test_q024_governance_is_fixed_89_event_feasibility_only():
    assert q024.Q019_EVENT_COUNT == 89
    assert q024.MIN_TIMESTAMP_COVERAGE == 1.0


def test_runner_keeps_fixed_population_and_emits_coverage_pit_only_result(
    monkeypatch, tmp_path
):
    events = []
    for index in range(q024.Q019_EVENT_COUNT):
        auction = date(2025, 1, 1) + timedelta(days=index)
        events.append({
            "record_date": (auction + timedelta(days=10)).isoformat(),
            "auction_date": auction.isoformat(),
            "cusip": f"TEST{index:05d}",
            "bid_to_cover_ratio": "2.35",
            "security_term": "10-Year",
        })

    monkeypatch.setattr(q024, "_q019_events", lambda: events)
    monkeypatch.setattr(q024, "_fetch_bytes", lambda *args, **kwargs: b"<rss><channel/></rss>")
    monkeypatch.setattr(
        q024,
        "_resolve_result_xml",
        lambda event: {
            "status": "RESULT_TIMESTAMP_VALIDATED",
            "publication_timestamp": q024._publication_timestamp(event, "13:02"),
        },
    )
    monkeypatch.setattr(
        q024,
        "_resolve_result_pdf",
        lambda event, result_xml: {"status": "RESULT_IDENTITY_VALIDATED"},
    )
    output_path = tmp_path / "q024.json"

    result = q024.run(output_path=output_path)
    persisted = json.loads(output_path.read_text(encoding="utf-8"))
    assert result == persisted
    assert result["status"] == "COVERAGE_VALIDATED"
    assert result["fixed_population"]["total_events"] == 89
    assert result["coverage"]["timestamp_validated_events"] == 89
    assert result["coverage"]["pit_validated_events"] == 89
    assert result["timestamp_convention"]["http_last_modified_used_as_publication_time"] is False
    assert result["governance"]["performance_evaluation"] is False
    assert result["governance"]["holdout_used"] is False
    assert result["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_runner_rejects_changed_q019_event_count(monkeypatch, tmp_path):
    monkeypatch.setattr(q024, "_q019_events", lambda: [])
    with pytest.raises(q024.SourceError, match="expected 89"):
        q024.run(output_path=tmp_path / "q024.json")
