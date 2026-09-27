"""Q024 Treasury auction-result publication timestamp feasibility.

Design/feasibility only. Uses the fixed Q019 event population, official
Treasury Auction Results PDFs for event identity/content, and the official
Treasury Auction Results RSS feed for an explicit publication timestamp when
historically available. No performance or P&L is computed.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
Q019_EVENT_COUNT = 89
TREASURY_API = (
    "https://api.fiscaldata.treasury.gov/services/api/"
    "fiscal_service/v1/accounting/od/auctions_query"
)
RESULT_PDF_BASE = (
    "https://www.treasurydirect.gov/instit/annceresult/press/preanre"
)
RESULT_XML_BASE = "https://www.treasurydirect.gov/xml"
RESULT_RSS_URL = "https://www.treasurydirect.gov/TA_WS/securities/auctioned/rss"
RESULT_TIME_ZONE = "America/New_York"
MAX_RESULT_SEQUENCE = 8
MIN_TIMESTAMP_COVERAGE = 1.0


class SourceError(RuntimeError):
    pass


def _fetch_response(
    url: str,
    timeout: int = 30,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[bytes, dict[str, str]]:
    request_headers = {"User-Agent": "trading-agent-public Q024 research"}
    if headers:
        request_headers.update(headers)
    req = Request(url, headers=request_headers)
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.read(), {
                key: value
                for key in ("Content-Length", "Content-MD5", "ETag", "Last-Modified")
                if (value := response.headers.get(key)) is not None
            }
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SourceError(f"{url}: {exc}") from exc


def _fp(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _fetch_bytes(url: str, timeout: int = 30, *, headers: dict[str, str] | None = None) -> bytes:
    return _fetch_response(url, timeout, headers=headers)[0]


def _fetch_json(url: str) -> dict:
    body = _fetch_bytes(url)
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"{url}: invalid JSON: {exc}") from exc


def _q019_events() -> list[dict]:
    params = {
        "fields": (
            "record_date,security_type,security_term,auction_date,"
            "cusip,bid_to_cover_ratio"
        ),
        "filter": (
            "security_type:eq:Note,"
            "security_term:eq:10-Year,"
            f"record_date:gte:{STUDY_START.isoformat()},"
            f"record_date:lte:{STUDY_END.isoformat()}"
        ),
        "sort": "auction_date",
        "page[size]": 2000,
    }
    rows = _fetch_json(TREASURY_API + "?" + urlencode(params)).get("data", [])
    rows.sort(key=lambda row: (row.get("auction_date", ""), row.get("cusip", "")))
    return rows


def _pdf_text(body: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(body))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise SourceError(f"PDF parsing failed: {exc}") from exc


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def _candidate_result_urls(event: dict) -> list[str]:
    auction = datetime.strptime(event["auction_date"], "%Y-%m-%d").date()
    return [
        f"{RESULT_PDF_BASE}/{auction.year}/R_{auction:%Y%m%d}_{sequence}.pdf"
        for sequence in range(1, MAX_RESULT_SEQUENCE + 1)
    ]


def _candidate_result_xml_urls(event: dict) -> list[str]:
    auction = datetime.strptime(event["auction_date"], "%Y-%m-%d").date()
    return [
        f"{RESULT_XML_BASE}/R_{auction:%Y%m%d}_{sequence}.xml"
        for sequence in range(1, MAX_RESULT_SEQUENCE + 1)
    ]


def _pdf_matches(text: str, event: dict) -> bool:
    normalized = _normalize(text)
    cusip = str(event["cusip"]).strip()
    return (
        cusip in normalized
        and re.search(r"\bTREASURY AUCTION RESULTS\b", normalized, re.I)
        and re.search(r"\b10-Year\s+Note\b", normalized, re.I)
        and re.search(r"Bid-to-Cover Ratio\s*:", normalized, re.I)
    )


def _resolve_result_pdf(event: dict, result_xml: dict | None = None) -> dict:
    errors: list[str] = []
    pdf_name = (
        result_xml.get("identity", {}).get("results_pdf_name")
        if result_xml
        else None
    )
    urls = (
        [f"{RESULT_PDF_BASE}/{date.fromisoformat(event['auction_date']).year}/{pdf_name}"]
        if pdf_name
        else _candidate_result_urls(event)
    )
    for url in urls:
        try:
            body = _fetch_bytes(url)
            text = _pdf_text(body)
            if not _pdf_matches(text, event):
                continue
            return {
                "status": "RESULT_IDENTITY_VALIDATED",
                "source_url": url,
                "content_sha256": hashlib.sha256(body).hexdigest(),
                "pdf_byte_length": len(body),
            }
        except SourceError as exc:
            errors.append(str(exc))
    return {
        "status": "RESULT_IDENTITY_INSUFFICIENT",
        "source_url": None,
        "content_sha256": None,
        "pdf_byte_length": None,
        "errors": errors[-5:],
    }


def _xml_values(body: bytes) -> dict[str, list[str]]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise SourceError(f"result XML parse failed: {exc}") from exc
    values: dict[str, list[str]] = {}
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        text = (element.text or "").strip()
        if text:
            values.setdefault(tag, []).append(text)
    return values


def _one_xml_value(values: dict[str, list[str]], tag: str) -> str | None:
    found = values.get(tag, [])
    return found[0] if len(found) == 1 else None


def _parse_result_xml(body: bytes) -> dict:
    values = _xml_values(body)
    return {
        "cusip": _one_xml_value(values, "CUSIP"),
        "auction_date": _one_xml_value(values, "AuctionDate"),
        "bid_to_cover_ratio": _one_xml_value(values, "BidToCoverRatio"),
        "release_time": _one_xml_value(values, "ReleaseTime"),
        "results_pdf_name": _one_xml_value(values, "ResultsPDFName"),
    }


def _same_ratio(source_value: object, event_value: object) -> bool:
    try:
        source_ratio = Decimal(str(source_value))
        event_ratio = Decimal(str(event_value))
    except (InvalidOperation, TypeError, ValueError):
        return False
    return (
        source_ratio.is_finite()
        and event_ratio.is_finite()
        and source_ratio == event_ratio
    )


def _xml_identity_matches(parsed: dict, event: dict, source_url: str) -> bool:
    expected_date = date.fromisoformat(event["auction_date"]).isoformat()
    expected_result_pdf = Path(source_url).stem + ".pdf"
    return (
        parsed.get("cusip") == str(event["cusip"]).strip()
        and parsed.get("auction_date") == expected_date
        and _same_ratio(parsed.get("bid_to_cover_ratio"), event.get("bid_to_cover_ratio"))
        and parsed.get("results_pdf_name") == expected_result_pdf
    )


def _publication_timestamp(event: dict, release_time: str | None) -> dict | None:
    if not release_time or not re.fullmatch(r"\d{2}:\d{2}", release_time):
        return None
    try:
        auction = date.fromisoformat(event["auction_date"])
        wall_time = time.fromisoformat(release_time)
        local_timestamp = datetime.combine(
            auction, wall_time, tzinfo=ZoneInfo(RESULT_TIME_ZONE)
        )
    except (TypeError, ValueError):
        return None
    return {
        "source_field": "AuctionResults/ReleaseTime",
        "source_date_field": "AuctionAnnouncement/AuctionDate",
        "source_local_time": release_time,
        "time_zone": RESULT_TIME_ZONE,
        "time_zone_interpretation": (
            "Treasury auction local clock; the XML field has no explicit UTC offset"
        ),
        "publication_timestamp_local": local_timestamp.isoformat(),
        "publication_timestamp_utc": (
            local_timestamp.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        ),
    }


def _fetch_xml_response(url: str) -> tuple[bytes, dict[str, str]] | None:
    request = Request(
        url,
        headers={
            "User-Agent": "trading-agent-public Q024 research",
            "Accept": "application/xml, text/xml;q=0.9, */*;q=0.1",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return response.read(), {
                key: value
                for key in ("Content-Length", "Content-MD5", "ETag", "Last-Modified")
                if (value := response.headers.get(key)) is not None
            }
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise SourceError(f"{url}: {exc}") from exc
    except (URLError, TimeoutError) as exc:
        raise SourceError(f"{url}: {exc}") from exc


def _resolve_result_xml(event: dict) -> dict:
    matches: list[dict] = []
    attempts: list[dict] = []
    errors: list[str] = []
    for url in _candidate_result_xml_urls(event):
        try:
            response = _fetch_xml_response(url)
            if response is None:
                attempts.append({"source_url": url, "status": "HTTP_404"})
                continue
            body, http_metadata = response
            parsed = _parse_result_xml(body)
            attempt = {
                "source_url": url,
                "status": (
                    "XML_IDENTITY_MATCH"
                    if _xml_identity_matches(parsed, event, url)
                    else "XML_IDENTITY_MISMATCH"
                ),
                "content_sha256": hashlib.sha256(body).hexdigest(),
                "http_metadata": http_metadata,
                "identity": {
                    "cusip": parsed.get("cusip"),
                    "auction_date": parsed.get("auction_date"),
                    "bid_to_cover_ratio": parsed.get("bid_to_cover_ratio"),
                    "results_pdf_name": parsed.get("results_pdf_name"),
                },
            }
            attempts.append(attempt)
            if attempt["status"] != "XML_IDENTITY_MATCH":
                continue
            matches.append({
                **attempt,
                "xml_byte_length": len(body),
                "release_time": parsed.get("release_time"),
            })
        except SourceError as exc:
            errors.append(str(exc))
            attempts.append({
                "source_url": url,
                "status": "SOURCE_ERROR",
                "error": str(exc),
            })

    if len(matches) != 1:
        return {
            "status": "RESULT_XML_IDENTITY_INSUFFICIENT",
            "source_url": None,
            "content_sha256": None,
            "http_metadata": {},
            "matching_xml_count": len(matches),
            "attempts": attempts,
            "errors": errors[-5:],
        }

    match = matches[0]
    timestamp = _publication_timestamp(event, match["release_time"])
    return {
        "status": (
            "RESULT_TIMESTAMP_VALIDATED"
            if timestamp is not None
            else "RESULT_TIMESTAMP_INSUFFICIENT"
        ),
        "source_url": match["source_url"],
        "content_sha256": match["content_sha256"],
        "xml_byte_length": match["xml_byte_length"],
        "http_metadata": match["http_metadata"],
        "matching_xml_count": 1,
        "identity": match["identity"],
        "attempts": attempts,
        "publication_timestamp": timestamp,
        "errors": errors[-5:],
    }


def _parse_rss(body: bytes) -> list[dict]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise SourceError(f"RSS XML parse failed: {exc}") from exc

    items: list[dict] = []
    for item in root.findall(".//item"):
        values = {
            child.tag.rsplit("}", 1)[-1]: (child.text or "").strip()
            for child in item
        }
        pub_date = values.get("pubDate")
        if not pub_date:
            continue
        try:
            timestamp = parsedate_to_datetime(pub_date)
        except (TypeError, ValueError) as exc:
            raise SourceError(f"invalid RSS pubDate {pub_date!r}: {exc}") from exc
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        items.append({
            "title": values.get("title", ""),
            "description": values.get("description", ""),
            "link": values.get("link", ""),
            "guid": values.get("guid", ""),
            "pubDate": pub_date,
            "publication_timestamp_utc": timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        })
    return items


def _find_rss_match(event: dict, rss_items: list[dict]) -> dict | None:
    cusip = str(event["cusip"]).strip()
    auction_date = date.fromisoformat(event["auction_date"])
    matches: list[dict] = []
    for item in rss_items:
        combined = " ".join(
            [item.get("title", ""), item.get("description", ""),
             item.get("link", ""), item.get("guid", "")]
        )
        link_host = urlparse(item.get("link", "")).netloc.lower()
        if link_host not in {"www.treasurydirect.gov", "treasurydirect.gov"}:
            continue
        description = _normalize(
            re.sub(r"<[^>]*>", " ", html.unescape(item.get("description", "")))
        )
        date_field = re.search(
            r"\bAuction Date\b\s*:?\s*(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})",
            description,
            re.IGNORECASE,
        )
        if cusip not in combined or not date_field:
            continue
        try:
            item_auction_date = date.fromisoformat(date_field.group(1))
        except ValueError:
            try:
                item_auction_date = datetime.strptime(
                    date_field.group(1), "%m/%d/%Y"
                ).date()
            except ValueError:
                continue
        if item_auction_date != auction_date:
            continue
        ratio_match = re.search(
            r"Bid[- ]to[- ]Cover Ratio\b[^0-9]*([0-9]+(?:\.[0-9]+)?)",
            description,
            re.IGNORECASE,
        )
        if not ratio_match or not _same_ratio(
            ratio_match.group(1), event.get("bid_to_cover_ratio")
        ):
            continue
        matches.append(item)
    if len(matches) != 1:
        return None
    return matches[0]


def _event_pit_status(event: dict, publication_timestamp: dict | None) -> str:
    if publication_timestamp is None:
        return "PIT_INSUFFICIENT"
    auction = date.fromisoformat(event["auction_date"])
    record = date.fromisoformat(event["record_date"])
    local_timestamp = publication_timestamp.get("publication_timestamp_local")
    if local_timestamp:
        published = datetime.fromisoformat(local_timestamp).date()
    else:
        utc_timestamp = datetime.fromisoformat(
            publication_timestamp["publication_timestamp_utc"].replace("Z", "+00:00")
        )
        published = utc_timestamp.astimezone(ZoneInfo(RESULT_TIME_ZONE)).date()
    return (
        "PIT_VALIDATED"
        if published == auction and auction < record
        else "PIT_INSUFFICIENT"
    )


def run(*, output_path: str | Path) -> dict:
    events = _q019_events()
    if len(events) != Q019_EVENT_COUNT:
        raise SourceError(
            f"fixed Q019 population has {len(events)} events; "
            f"expected {Q019_EVENT_COUNT}"
        )
    event_keys = [
        (event.get("cusip"), event.get("auction_date"))
        for event in events
    ]
    if any(not cusip or not auction_date for cusip, auction_date in event_keys):
        raise SourceError("fixed Q019 population has an event without CUSIP/auction_date")
    if len(set(event_keys)) != Q019_EVENT_COUNT:
        raise SourceError("fixed Q019 population has duplicate CUSIP/auction_date keys")

    try:
        rss_items = _parse_rss(_fetch_bytes(RESULT_RSS_URL, headers={"Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.1", "User-Agent": "Mozilla/5.0 (compatible; trading-agent-public Q024 research)" }))
        rss_source_status = "RSS_RETRIEVED"
    except SourceError as exc:
        rss_items = []
        rss_source_status = "RSS_INSUFFICIENT"
        rss_error = str(exc)

    rows: list[dict] = []
    for event in events:
        result_xml = _resolve_result_xml(event)
        xml_publication = result_xml.get("publication_timestamp")
        result_pdf = _resolve_result_pdf(event, result_xml)
        rss_match = _find_rss_match(event, rss_items) if rss_items else None
        rss_publication = (
            {
                "status": "RESULT_TIMESTAMP_VALIDATED",
                **rss_match,
            }
            if rss_match
            else {
                "status": "RESULT_TIMESTAMP_INSUFFICIENT",
                "source_url": RESULT_RSS_URL,
            }
        )
        publication = xml_publication
        publication_source = "official_result_xml"
        if publication is None and rss_match:
            publication = {
                "source_field": "RSS/pubDate",
                "time_zone": "UTC",
                "publication_timestamp_utc": rss_match["publication_timestamp_utc"],
            }
            publication_source = "official_result_rss"
        timestamp_status = (
            "RESULT_TIMESTAMP_VALIDATED"
            if publication is not None
            else "RESULT_TIMESTAMP_INSUFFICIENT"
        )
        rows.append({
            "q019": {
                "record_date": event["record_date"],
                "auction_date": event["auction_date"],
                "cusip": event["cusip"],
                "bid_to_cover_ratio": event.get("bid_to_cover_ratio"),
                "security_term": event.get("security_term"),
            },
            "result_pdf": result_pdf,
            "result_xml": result_xml,
            "rss_result_publication": rss_publication,
            "result_publication": {
                "status": timestamp_status,
                "source": publication_source if publication is not None else None,
                "timestamp": publication,
            },
            "pit_status": _event_pit_status(event, publication),
        })

    validated = sum(
        row["result_publication"]["status"] == "RESULT_TIMESTAMP_VALIDATED"
        for row in rows
    )
    total = len(rows)
    ratio = validated / total
    pit_validated = sum(row["pit_status"] == "PIT_VALIDATED" for row in rows)
    status = "COVERAGE_VALIDATED" if ratio >= MIN_TIMESTAMP_COVERAGE else "DATA_INSUFFICIENT"

    result = {
        "schema_version": "1.0",
        "task_id": "Q-024-TREASURY-AUCTION-RESULT-TIMESTAMP-PIT-FEASIBILITY",
        "status": status,
        "study_window": {
            "start": STUDY_START.isoformat(),
            "end": STUDY_END.isoformat(),
        },
        "fixed_population": {
            "source": "Q019 fixed Treasury 10-Year result events",
            "total_events": total,
        },
        "sources": {
            "treasury_auction_api": TREASURY_API,
            "official_result_pdf_base": RESULT_PDF_BASE,
            "official_result_xml_base": RESULT_XML_BASE,
            "official_result_rss": RESULT_RSS_URL,
            "rss_source_status": rss_source_status,
        },
        "timestamp_convention": {
            "xml_date_field": "AuctionAnnouncement/AuctionDate",
            "xml_release_time_field": "AuctionResults/ReleaseTime",
            "xml_time_zone": RESULT_TIME_ZONE,
            "xml_field_has_explicit_offset": False,
            "http_last_modified_used_as_publication_time": False,
        },
        "rss_item_count": len(rss_items),
        "rss_catalog": [
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "guid": item.get("guid", ""),
                "pubDate": item.get("pubDate", ""),
                "publication_timestamp_utc": item.get("publication_timestamp_utc", ""),
            }
            for item in rss_items
        ],
        "coverage": {
            "timestamp_validated_events": validated,
            "timestamp_coverage_ratio": ratio,
            "minimum_required_ratio": MIN_TIMESTAMP_COVERAGE,
            "pit_validated_events": pit_validated,
            "pit_coverage_ratio": pit_validated / total,
        },
        "governance": {
            "source_feasibility_only": True,
            "performance_evaluation": False,
            "pnl_evaluation": False,
            "holdout_used": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "variant_search": False,
            "research_gate_changes": False,
            "promotion_decision": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "events": rows,
    }
    if rss_source_status != "RSS_RETRIEVED":
        result["rss_error"] = rss_error
    result["fingerprint"] = _fp(result)

    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": result["task_id"],
        "status": result["status"],
        "events": total,
        "rss_items": len(rss_items),
        "timestamp_validated_events": validated,
        "pit_validated_events": pit_validated,
        "coverage_ratio": ratio,
        "fingerprint": result["fingerprint"],
    }, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="research/runs/source_feasibility/q024_treasury_auction_result_timestamp_pit_feasibility.json",
    )
    args = parser.parse_args()
    try:
        run(output_path=args.output)
    except (SourceError, ValueError, OSError) as exc:
        print(json.dumps({"status": "DATA_INSUFFICIENT", "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
