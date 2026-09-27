"""Coverage-only PIT feasibility for public Treasury auction-result timestamps."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
EXPECTED_EVENTS = 89
TREASURY_API = (
    "https://api.fiscaldata.treasury.gov/services/api/"
    "fiscal_service/v1/accounting/od/auctions_query"
)
RESULT_PDF_BASE = (
    "https://www.treasurydirect.gov/instit/annceresult/press/preanre"
)
RESULT_RSS_URL = "https://www.treasurydirect.gov/TA_WS/securities/auctioned/rss"
MAX_RESULT_SEQUENCE = 8
OFFICIAL_RESULT_HOST = "www.treasurydirect.gov"


class SourceError(RuntimeError):
    """A public Treasury source could not be retrieved or interpreted."""


def _fingerprint(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _fetch_bytes(url: str, timeout: int = 30) -> bytes:
    request = Request(
        url,
        headers={
            "Accept": "application/rss+xml, application/xml;q=0.9, "
            "text/xml;q=0.8, */*;q=0.1",
            "User-Agent": "trading-agent-public Q024 research",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SourceError(f"{url}: {exc}") from exc


def _fetch_json(url: str) -> dict:
    try:
        return json.loads(_fetch_bytes(url).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"{url}: invalid JSON: {exc}") from exc


def _q019_events() -> list[dict]:
    params = {
        "fields": (
            "record_date,security_type,security_term,auction_date,"
            "cusip,bid_to_cover_ratio"
        ),
        "filter": (
            "security_type:eq:Note,security_term:eq:10-Year,"
            f"record_date:gte:{STUDY_START.isoformat()},"
            f"record_date:lte:{STUDY_END.isoformat()}"
        ),
        "sort": "auction_date",
        "page[size]": 2000,
    }
    payload = _fetch_json(TREASURY_API + "?" + urlencode(params))
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise SourceError("Treasury auction API response has no data list")
    if any(not isinstance(row, dict) for row in rows):
        raise SourceError("Treasury auction API data list contains a non-object row")
    return sorted(
        rows,
        key=lambda row: (row.get("auction_date", ""), row.get("cusip", "")),
    )


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def _candidate_result_urls(event: dict) -> list[str]:
    try:
        auction = date.fromisoformat(event["auction_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceError(f"invalid Q019 auction_date: {exc}") from exc
    return [
        f"{RESULT_PDF_BASE}/{auction.year}/R_{auction:%Y%m%d}_{sequence}.pdf"
        for sequence in range(1, MAX_RESULT_SEQUENCE + 1)
    ]


def _decimal(value: object) -> Decimal | None:
    try:
        parsed = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _pdf_matches(text: str, event: dict) -> bool:
    normalized = _normalize(text)
    cusip = str(event.get("cusip", "")).strip()
    expected_ratio = _decimal(event.get("bid_to_cover_ratio"))
    ratio_match = re.search(
        r"Bid-to-Cover Ratio\s*:\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
        normalized,
        re.IGNORECASE,
    )
    if not cusip or expected_ratio is None or not ratio_match:
        return False
    cusip_match = re.search(
        rf"(?<![A-Z0-9]){re.escape(cusip)}(?![A-Z0-9])",
        normalized,
        re.IGNORECASE,
    )
    return (
        cusip_match is not None
        and re.search(r"\bTREASURY AUCTION RESULTS\b", normalized, re.I) is not None
        and re.search(
            r"\b10-Year(?:\s+TIPS|\s+Note)?\b", normalized, re.I
        ) is not None
        and _decimal(ratio_match.group(1)) == expected_ratio
    )


def _resolve_result_pdf(event: dict, source_url: str) -> dict:
    if source_url not in _candidate_result_urls(event):
        raise SourceError("result file URL is not an official Q019 auction-date candidate")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise SourceError("pypdf is required to validate official result PDFs") from exc

    try:
        body = _fetch_bytes(source_url)
        reader = PdfReader(io.BytesIO(body))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except (SourceError, OSError, ValueError) as exc:
        return {
            "status": "RESULT_IDENTITY_INSUFFICIENT",
            "source_url": source_url,
            "content_sha256": None,
            "pdf_byte_length": None,
            "errors": [str(exc)],
        }
    except Exception as exc:
        return {
            "status": "RESULT_IDENTITY_INSUFFICIENT",
            "source_url": source_url,
            "content_sha256": hashlib.sha256(body).hexdigest(),
            "pdf_byte_length": len(body),
            "errors": [f"PDF parsing failed: {exc}"],
        }
    if not _pdf_matches(text, event):
        return {
            "status": "RESULT_IDENTITY_INSUFFICIENT",
            "source_url": source_url,
            "content_sha256": hashlib.sha256(body).hexdigest(),
            "pdf_byte_length": len(body),
            "errors": ["official result file does not match Q019 identity/content"],
        }
    return {
        "status": "RESULT_IDENTITY_VALIDATED",
        "source_url": source_url,
        "content_sha256": hashlib.sha256(body).hexdigest(),
        "pdf_byte_length": len(body),
    }


def _parse_publication_timestamp(value: str) -> str:
    try:
        timestamp = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise SourceError(f"invalid publication timestamp {value!r}") from exc
    if timestamp.tzinfo is None:
        raise SourceError(f"publication timestamp lacks timezone: {value!r}")
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_feed(body: bytes) -> list[dict]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise SourceError(f"Treasury result feed XML parse failed: {exc}") from exc

    records: list[dict] = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1].lower() not in {"item", "entry", "result"}:
            continue
        fields = {
            child.tag.rsplit("}", 1)[-1].lower(): (child.text or "").strip()
            for child in node
        }
        for child in node:
            if child.tag.rsplit("}", 1)[-1].lower() == "link":
                fields["link"] = child.attrib.get("href", fields.get("link", ""))
        timestamp_field = next((
            name
            for name in (
                "pubdate",
                "publicationtimestamp",
                "publicationdatetime",
                "publishedat",
            )
            if fields.get(name)
        ), None)
        if timestamp_field is None:
            continue
        records.append({
            "title": fields.get("title", ""),
            "description": fields.get("description", ""),
            "link": fields.get("link", ""),
            "guid": fields.get("guid", ""),
            "timestamp_field": timestamp_field,
            "timestamp_source_value": fields[timestamp_field],
            "publication_timestamp_utc": _parse_publication_timestamp(
                fields[timestamp_field]
            ),
        })
    return records


def _same_official_result(item: dict, result_pdf: dict) -> bool:
    source_url = result_pdf.get("source_url")
    if not source_url:
        return False
    expected = urlsplit(source_url)
    if expected.hostname != OFFICIAL_RESULT_HOST:
        return False
    pdf_name = Path(expected.path).name

    link = urljoin(RESULT_RSS_URL, item.get("link", ""))
    parsed_link = urlsplit(link)
    linked_pdf = (
        parsed_link.hostname == OFFICIAL_RESULT_HOST
        and parsed_link.path == expected.path
    )
    guid = item.get("guid", "").strip()
    guid_matches = guid == pdf_name or guid == source_url
    return linked_pdf or guid_matches


def _find_feed_match(result_pdf: dict, feed_items: list[dict]) -> dict | None:
    matches = [item for item in feed_items if _same_official_result(item, result_pdf)]
    if len(matches) != 1:
        return None
    return matches[0]


def _feed_result_candidates(event: dict, feed_items: list[dict]) -> list[tuple[str, dict]]:
    candidates = []
    for url in _candidate_result_urls(event):
        for item in feed_items:
            if _same_official_result(item, {"source_url": url}):
                candidates.append((url, item))
    return candidates


def _fixed_population_valid(events: list[dict]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if len(events) != EXPECTED_EVENTS:
        errors.append(
            f"fixed Q019 population must contain {EXPECTED_EVENTS} events; "
            f"received {len(events)}"
        )
    keys: set[tuple[str, str]] = set()
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"event {index} is not a Q019 object")
            continue
        try:
            auction_date = date.fromisoformat(event["auction_date"]).isoformat()
            record_date = date.fromisoformat(event["record_date"]).isoformat()
            cusip = str(event["cusip"]).strip()
            ratio = _decimal(event["bid_to_cover_ratio"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"event {index} is missing valid Q019 identity/content fields")
            continue
        if (
            event.get("security_type") != "Note"
            or event.get("security_term") != "10-Year"
        ):
            errors.append(f"event {index} is not a Q019 10-Year Note")
        if not cusip or ratio is None or ratio <= 0:
            errors.append(f"event {index} has empty CUSIP or invalid bid-to-cover ratio")
        key = (cusip, auction_date)
        if key in keys:
            errors.append(f"duplicate fixed-population key: CUSIP + auction_date {key}")
        keys.add(key)
        if not STUDY_START <= date.fromisoformat(record_date) <= STUDY_END:
            errors.append(f"event {index} is outside the fixed Q019 record-date window")
    return not errors, errors


def run(*, output_path: str | Path) -> dict:
    events = _q019_events()
    population_valid, population_errors = _fixed_population_valid(events)
    feed_body = None
    feed_error = None
    try:
        feed_body = _fetch_bytes(RESULT_RSS_URL)
        feed_items = _parse_feed(feed_body)
        feed_status = "RETRIEVED"
    except SourceError as exc:
        feed_items = []
        feed_status = "INSUFFICIENT"
        feed_error = str(exc)

    rows: list[dict] = []
    for event in events:
        feed_candidates = (
            _feed_result_candidates(event, feed_items) if population_valid else []
        )
        if len(feed_candidates) == 1:
            result_url, _ = feed_candidates[0]
            result_pdf = _resolve_result_pdf(event, result_url)
            feed_match = (
                _find_feed_match(result_pdf, feed_items)
                if result_pdf["status"] == "RESULT_IDENTITY_VALIDATED"
                else None
            )
        else:
            result_pdf = {
                "status": "RESULT_IDENTITY_INSUFFICIENT",
                "source_url": None,
                "content_sha256": None,
                "pdf_byte_length": None,
                "errors": [
                    "fixed Q019 population validation failed"
                    if not population_valid
                    else "no unique official result file linked by the publication feed"
                ],
            }
            feed_match = None
        rows.append({
            "q019": {
                "record_date": event.get("record_date"),
                "auction_date": event.get("auction_date"),
                "cusip": event.get("cusip"),
                "security_type": event.get("security_type"),
                "security_term": event.get("security_term"),
                "bid_to_cover_ratio": event.get("bid_to_cover_ratio"),
            },
            "result_identity": result_pdf,
            "result_publication": (
                {
                    "status": "RESULT_TIMESTAMP_VALIDATED",
                    **feed_match,
                    "source_url": RESULT_RSS_URL,
                }
                if feed_match
                else {
                    "status": "RESULT_TIMESTAMP_INSUFFICIENT",
                    "source_url": RESULT_RSS_URL,
                }
            ),
        })

    validated = sum(
        row["result_publication"]["status"] == "RESULT_TIMESTAMP_VALIDATED"
        for row in rows
    )
    passed = population_valid and validated == EXPECTED_EVENTS
    result = {
        "schema_version": "1.0",
        "task_id": "Q-024-TREASURY-AUCTION-RESULT-TIMESTAMP-PIT-FEASIBILITY",
        "status": "COVERAGE_VALIDATED" if passed else "DATA_INSUFFICIENT",
        "study_window": {
            "start": STUDY_START.isoformat(),
            "end": STUDY_END.isoformat(),
        },
        "fixed_population": {
            "source": "Q019 Treasury 10-Year auction result events",
            "expected_events": EXPECTED_EVENTS,
            "observed_events": len(events),
            "valid": population_valid,
            "validation_errors": population_errors,
        },
        "sources": {
            "treasury_auction_api": TREASURY_API,
            "official_result_pdf_base": RESULT_PDF_BASE,
            "official_result_feed": RESULT_RSS_URL,
            "result_feed_status": feed_status,
            "result_feed_record_count": len(feed_items),
            "result_feed_sha256": (
                hashlib.sha256(feed_body).hexdigest() if feed_body is not None else None
            ),
            "result_feed_byte_length": len(feed_body) if feed_body is not None else None,
        },
        "coverage": {
            "timestamp_validated_events": validated,
            "total_events": EXPECTED_EVENTS,
            "pass_rule": "89/89 unique CUSIP + auction_date matches",
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
    if feed_error:
        result["result_feed_error"] = feed_error
    result["fingerprint"] = _fingerprint(result)

    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "task_id": result["task_id"],
        "status": result["status"],
        "events": len(events),
        "timestamp_validated_events": validated,
        "fingerprint": result["fingerprint"],
    }, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=(
            "research/runs/source_feasibility/"
            "q024_treasury_result_timestamp_pit.json"
        ),
    )
    args = parser.parse_args()
    try:
        run(output_path=args.output)
    except (SourceError, OSError, ValueError) as exc:
        print(json.dumps({"status": "DATA_INSUFFICIENT", "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
