from __future__ import annotations

import json
from datetime import date, timedelta

from automation import q024_treasury_result_timestamp_pit as q024


def test_pdf_identity_requires_q019_cusip_and_bid_to_cover_value():
    event = {
        "auction_date": "2025-08-06",
        "cusip": "91282CNT4",
        "bid_to_cover_ratio": "2.35",
    }
    text = (
        "TREASURY AUCTION RESULTS 10-Year Note CUSIP Number: 91282CNT4 "
        "Bid-to-Cover Ratio: 2.35"
    )
    assert q024._pdf_matches(text, event)
    assert not q024._pdf_matches(text.replace("91282CNT4", "91282CXX9"), event)
    assert not q024._pdf_matches(text.replace("2.35", "2.34"), event)


def test_feed_accepts_only_timezone_qualified_explicit_publication_time():
    body = b"""<rss><channel><item>
    <title>10-Year Note results</title>
    <link>https://www.treasurydirect.gov/result.pdf</link>
    <guid>result.pdf</guid>
    <pubDate>Wed, 06 Aug 2025 13:00:00 GMT</pubDate>
    </item></channel></rss>"""
    items = q024._parse_feed(body)
    assert items[0]["publication_timestamp_utc"] == "2025-08-06T13:00:00Z"

    naive = b"""<feed><entry><link href="https://www.treasurydirect.gov/x.pdf"/>
    <publishedAt>2025-08-06T13:00:00</publishedAt></entry></feed>"""
    try:
        q024._parse_feed(naive)
    except q024.SourceError as exc:
        assert "lacks timezone" in str(exc)
    else:
        raise AssertionError("timezone-free publication timestamp was accepted")

    xml_result = b"""<results><result>
    <publicationTimestamp>2025-08-06T13:00:00-04:00</publicationTimestamp>
    <link>https://www.treasurydirect.gov/result.pdf</link>
    </result></results>"""
    assert q024._parse_feed(xml_result)[0]["publication_timestamp_utc"] == (
        "2025-08-06T17:00:00Z"
    )


def test_feed_match_requires_unique_official_result_file_identity():
    event = {
        "auction_date": "2025-08-06",
        "cusip": "91282CNT4",
        "bid_to_cover_ratio": "2.35",
    }
    result_url = q024._candidate_result_urls(event)[1]
    result_pdf = {
        "source_url": result_url
    }
    item = {
        "link": result_url,
        "guid": "R_20250806_2.pdf",
    }
    assert q024._feed_result_candidates(event, [item]) == [(result_url, item)]
    assert q024._feed_result_candidates(event, [item, item]) == [
        (result_url, item),
        (result_url, item),
    ]
    assert q024._find_feed_match(result_pdf, [item]) == item
    assert q024._find_feed_match(result_pdf, [item, item]) is None
    wrong_host = {"link": "https://example.org/R_20250806_2.pdf", "guid": ""}
    assert q024._find_feed_match(result_pdf, [wrong_host]) is None


def test_fixed_population_requires_89_unique_valid_events():
    events = [
        {
            "record_date": (date(2011, 1, 1) + timedelta(days=index)).isoformat(),
            "auction_date": (date(2010, 12, 1) + timedelta(days=index)).isoformat(),
            "cusip": f"cusip-{index}",
            "security_type": "Note",
            "security_term": "10-Year",
            "bid_to_cover_ratio": "2.35",
        }
        for index in range(q024.EXPECTED_EVENTS)
    ]
    assert q024._fixed_population_valid(events) == (True, [])
    valid, errors = q024._fixed_population_valid(events[:-1])
    assert not valid
    assert any("must contain 89" in error for error in errors)
    wrong_security = [dict(event) for event in events]
    wrong_security[0]["security_term"] = "2-Year"
    assert not q024._fixed_population_valid(wrong_security)[0]
    duplicate_key = [dict(event) for event in events]
    duplicate_key[-1]["cusip"] = duplicate_key[0]["cusip"]
    duplicate_key[-1]["auction_date"] = duplicate_key[0]["auction_date"]
    assert not q024._fixed_population_valid(duplicate_key)[0]


def test_run_pass_requires_89_of_89_and_preserves_safety(tmp_path, monkeypatch):
    events = [
        {
            "record_date": (date(2011, 1, 1) + timedelta(days=index)).isoformat(),
            "auction_date": (date(2010, 12, 1) + timedelta(days=index)).isoformat(),
            "cusip": f"cusip-{index}",
            "security_type": "Note",
            "security_term": "10-Year",
            "bid_to_cover_ratio": "2.35",
        }
        for index in range(q024.EXPECTED_EVENTS)
    ]
    monkeypatch.setattr(q024, "_q019_events", lambda: events)
    monkeypatch.setattr(q024, "_fetch_bytes", lambda _url, timeout=30: b"<rss/>")
    monkeypatch.setattr(q024, "_parse_feed", lambda _body: [])
    monkeypatch.setattr(
        q024,
        "_feed_result_candidates",
        lambda event, _items: [(q024._candidate_result_urls(event)[0], {})],
    )
    monkeypatch.setattr(
        q024,
        "_resolve_result_pdf",
        lambda event, url: {
            "status": "RESULT_IDENTITY_VALIDATED",
            "source_url": url,
            "content_sha256": "a" * 64,
            "pdf_byte_length": 100,
        },
    )
    monkeypatch.setattr(
        q024,
        "_find_feed_match",
        lambda _pdf, _items: {
            "timestamp_field": "pubDate",
            "timestamp_source_value": "Wed, 06 Aug 2025 13:00:00 GMT",
            "publication_timestamp_utc": "2025-08-06T13:00:00Z",
        },
    )
    output = tmp_path / "q024.json"

    result = q024.run(output_path=output)

    assert result["status"] == "COVERAGE_VALIDATED"
    assert result["coverage"]["timestamp_validated_events"] == 89
    assert result["governance"]["performance_evaluation"] is False
    assert result["governance"]["holdout_used"] is False
    assert result["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    assert json.loads(output.read_text(encoding="utf-8"))["fingerprint"] == result["fingerprint"]


def test_run_is_data_insufficient_when_any_timestamp_is_missing(tmp_path, monkeypatch):
    events = [
        {
            "record_date": (date(2011, 1, 1) + timedelta(days=index)).isoformat(),
            "auction_date": (date(2010, 12, 1) + timedelta(days=index)).isoformat(),
            "cusip": f"cusip-{index}",
            "security_type": "Note",
            "security_term": "10-Year",
            "bid_to_cover_ratio": "2.35",
        }
        for index in range(q024.EXPECTED_EVENTS)
    ]
    monkeypatch.setattr(q024, "_q019_events", lambda: events)
    monkeypatch.setattr(q024, "_fetch_bytes", lambda _url, timeout=30: b"<rss/>")
    monkeypatch.setattr(q024, "_parse_feed", lambda _body: [])
    monkeypatch.setattr(
        q024,
        "_feed_result_candidates",
        lambda event, _items: [(q024._candidate_result_urls(event)[0], {})],
    )
    monkeypatch.setattr(
        q024,
        "_resolve_result_pdf",
        lambda event, url: {
            "status": "RESULT_IDENTITY_VALIDATED",
            "source_url": url,
        },
    )
    calls = 0

    def feed_match(_pdf, _items):
        nonlocal calls
        calls += 1
        if calls == q024.EXPECTED_EVENTS:
            return None
        return {
            "timestamp_field": "pubDate",
            "timestamp_source_value": "Wed, 06 Aug 2025 13:00:00 GMT",
            "publication_timestamp_utc": "2025-08-06T13:00:00Z",
        }

    monkeypatch.setattr(q024, "_find_feed_match", feed_match)

    result = q024.run(output_path=tmp_path / "q024.json")

    assert result["status"] == "DATA_INSUFFICIENT"
    assert result["coverage"]["timestamp_validated_events"] == 88
