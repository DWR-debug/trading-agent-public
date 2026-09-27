"""Q024 Treasury auction-result publication timestamp feasibility.

Design/feasibility only. Uses the fixed Q019 event population, official
Treasury Auction Results PDFs for event identity/content, and the official
Treasury Auction Results RSS feed for an explicit publication timestamp when
historically available. No performance or P&L is computed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import exchange_calendars as xcals
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
EXPECTED_Q019_EVENTS = 89
TREASURY_API = (
    "https://api.fiscaldata.treasury.gov/services/api/"
    "fiscal_service/v1/accounting/od/auctions_query"
)
RESULT_PDF_BASE = (
    "https://www.treasurydirect.gov/instit/annceresult/press/preanre"
)
RESULT_RSS_URL = "https://www.treasurydirect.gov/TA_WS/securities/auctioned/rss"
MAX_RESULT_SEQUENCE = 8
MIN_TIMESTAMP_COVERAGE = 1.0


class SourceError(RuntimeError):
    pass


def _fp(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _fetch_bytes(url: str, timeout: int = 30, *, headers: dict[str, str] | None = None) -> bytes:
    request_headers = {"User-Agent": "trading-agent-public Q024 research"}
    if headers:
        request_headers.update(headers)
    req = Request(url, headers=request_headers)
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SourceError(f"{url}: {exc}") from exc


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


def _pdf_matches(text: str, event: dict) -> bool:
    normalized = _normalize(text)
    cusip = str(event["cusip"]).strip()
    return (
        cusip in normalized
        and re.search(r"\bTREASURY AUCTION RESULTS\b", normalized, re.I)
        and re.search(r"\b10-Year\s+Note\b", normalized, re.I)
        and re.search(r"Bid-to-Cover Ratio\s*:", normalized, re.I)
    )


def _resolve_result_pdf(event: dict) -> dict:
    errors: list[str] = []
    for url in _candidate_result_urls(event):
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
    auction_token = datetime.strptime(
        event["auction_date"], "%Y-%m-%d"
    ).strftime("%Y%m%d")
    matches: list[dict] = []
    for item in rss_items:
        combined = " ".join(
            [item.get("title", ""), item.get("description", ""),
             item.get("link", ""), item.get("guid", "")]
        )
        # A PDF link alone identifies a document, not the Q019 event.  The
        # result timestamp must be tied to both fixed event identifiers and
        # the value used by Q019.
        if cusip not in combined or auction_token not in combined:
            continue
        ratio = str(event.get("bid_to_cover_ratio", "")).strip()
        ratio_present = ratio and re.search(
            rf"\b{re.escape(ratio)}\b", combined
        )
        label_present = re.search(
            r"bid[\s-]*to[\s-]*cover(?:\s+ratio)?", combined, re.I
        )
        if not (ratio_present and label_present):
            continue
        matches.append(item)
    if not matches:
        return None
    matches.sort(key=lambda item: item["publication_timestamp_utc"])
    return matches[0]


def run(*, output_path: str | Path) -> dict:
    events = _q019_events()
    if not events:
        raise SourceError("Q019 event population is empty")
    if len(events) != EXPECTED_Q019_EVENTS:
        raise SourceError(
            f"Q019 fixed population changed: expected {EXPECTED_Q019_EVENTS}, "
            f"received {len(events)}"
        )
    if len({
        (event.get("cusip"), event.get("auction_date")) for event in events
    }) != len(events):
        raise SourceError("Q019 fixed population contains duplicate CUSIP/auction_date keys")

    try:
        rss_items = _parse_rss(_fetch_bytes(RESULT_RSS_URL, headers={"Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.1", "User-Agent": "Mozilla/5.0 (compatible; trading-agent-public Q024 research)" }))
        rss_source_status = "RSS_RETRIEVED"
    except SourceError as exc:
        rss_items = []
        rss_source_status = "RSS_INSUFFICIENT"
        rss_error = str(exc)

    calendar = xcals.get_calendar("XNYS")
    sessions = [
        stamp.date()
        for stamp in calendar.sessions_in_range(
            STUDY_START.isoformat(), STUDY_END.isoformat()
        )
    ]
    rows: list[dict] = []
    for event in events:
        result_pdf = _resolve_result_pdf(event)
        rss_match = _find_rss_match(event, rss_items) if rss_items else None
        publication_timestamp = (
            rss_match["publication_timestamp_utc"] if rss_match else None
        )
        record_date = date.fromisoformat(event["record_date"])
        following_sessions = [session for session in sessions if session > record_date]
        next_session = following_sessions[0] if following_sessions else None
        pit_valid = bool(
            publication_timestamp
            and next_session
            and datetime.fromisoformat(
                publication_timestamp.replace("Z", "+00:00")
            ).date() < next_session
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
            "rss_result_publication": (
                {
                    "status": "RESULT_TIMESTAMP_VALIDATED",
                    **rss_match,
                }
                if rss_match
                else {
                    "status": "RESULT_TIMESTAMP_INSUFFICIENT",
                    "source_url": RESULT_RSS_URL,
                }
            ),
            "pit": {
                "first_following_xnys_session": (
                    next_session.isoformat() if next_session else None
                ),
                "information_timestamp_before_following_session": pit_valid,
            },
        })

    timestamp_validated = sum(
        row["rss_result_publication"]["status"] == "RESULT_TIMESTAMP_VALIDATED"
        for row in rows
    )
    pit_validated = sum(
        row["pit"]["information_timestamp_before_following_session"]
        for row in rows
    )
    total = len(rows)
    ratio = timestamp_validated / total
    status = (
        "COVERAGE_VALIDATED"
        if ratio >= MIN_TIMESTAMP_COVERAGE and pit_validated == total
        else "DATA_INSUFFICIENT"
    )

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
            "expected_events": EXPECTED_Q019_EVENTS,
        },
        "sources": {
            "treasury_auction_api": TREASURY_API,
            "official_result_pdf_base": RESULT_PDF_BASE,
            "official_result_rss": RESULT_RSS_URL,
            "rss_source_status": rss_source_status,
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
            "timestamp_validated_events": timestamp_validated,
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
        "timestamp_validated_events": timestamp_validated,
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
