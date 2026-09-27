"""Q023 Treasury release-timestamp / PIT feasibility.

Design/feasibility only. No returns, P&L, holdout, candidate ranking, or
parameter/asset/horizon/variant search is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
TREASURY_API = (
    "https://api.fiscaldata.treasury.gov/services/api/"
    "fiscal_service/v1/accounting/od/auctions_query"
)
TREASURY_PDF_BASE = (
    "https://www.treasurydirect.gov/instit/annceresult/press/preanre"
)
MAX_PDF_SEQUENCE = 8
MAX_ANNOUNCEMENT_LOOKBACK_DAYS = 14
MIN_TIMESTAMP_COVERAGE = 1.0
EASTERN = ZoneInfo("America/New_York")


class SourceError(RuntimeError):
    """Raised when an official source cannot be retrieved or parsed."""


def _fingerprint(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _fetch_bytes(url: str, timeout: int = 30) -> bytes:
    request = Request(
        url,
        headers={"User-Agent": "trading-agent-public Q023 research"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SourceError(f"{url}: {exc}") from exc


def _fetch_json(url: str) -> dict:
    body = _fetch_bytes(url)
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"{url}: invalid JSON: {exc}") from exc


def _treasury_events() -> list[dict]:
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
    payload = _fetch_json(TREASURY_API + "?" + urlencode(params))
    rows = payload.get("data", [])
    rows.sort(key=lambda row: (row.get("auction_date", ""), row.get("cusip", "")))
    return rows


def _pdf_text(pdf_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # pypdf exposes several parser-specific exceptions
        raise SourceError(f"PDF parsing failed: {exc}") from exc


def _normalize(text: str) -> str:
    return re.sub(r"[ \t\r\f\v]+", " ", text).replace("\u00a0", " ").strip()


def _parse_embargo_timestamp(text: str) -> tuple[str, str, str]:
    normalized = _normalize(text)
    embargo = re.search(
        r"Embargoed\s+Until\s*:?\s*"
        r"(\d{1,2}:\d{2}\s*(?:A\.?M\.?|P\.?M\.?))",
        normalized,
        re.IGNORECASE,
    )
    if not embargo:
        raise SourceError('official PDF lacks reproducible "Embargoed Until" time')

    tail = normalized[embargo.end(): embargo.end() + 260]
    doc_date = re.search(
        r"\b("
        r"January|February|March|April|May|June|July|August|September|"
        r"October|November|December"
        r")\s+\d{1,2},\s+\d{4}\b",
        tail,
        re.IGNORECASE,
    )
    if not doc_date:
        raise SourceError("official PDF lacks reproducible document date")

    time_text = re.sub(r"\s+", " ", embargo.group(1)).upper()
    time_text = time_text.replace(".", "")
    doc_date_text = doc_date.group(0)

    parsed_date = datetime.strptime(doc_date_text, "%B %d, %Y").date()
    parsed_time = datetime.strptime(time_text, "%I:%M %p").time()
    timestamp = datetime.combine(
        parsed_date, parsed_time, tzinfo=EASTERN
    ).astimezone(timezone.utc)

    return (
        doc_date_text,
        time_text,
        timestamp.isoformat().replace("+00:00", "Z"),
    )


def _extract_field(text: str, label: str) -> str | None:
    normalized = _normalize(text)
    pattern = re.escape(label) + r"\s*:?\s*([^:]+?)(?=\s+[A-Z][A-Za-z /()-]+:|$)"
    match = re.search(pattern, normalized, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _pdf_matches_event(text: str, event: dict) -> bool:
    normalized = _normalize(text)
    cusip = str(event["cusip"]).strip()
    auction = datetime.strptime(
        event["auction_date"], "%Y-%m-%d"
    ).strftime("%B %d, %Y")
    return (
        cusip in normalized
        and re.search(
            rf"Auction Date\s*:?\s*{re.escape(auction)}",
            normalized,
            re.IGNORECASE,
        ) is not None
        and re.search(
            r"\b(?:10-Year Note|10-Year TIPS)\b",
            normalized,
            re.IGNORECASE,
        ) is not None
    )


def _candidate_urls(event: dict) -> list[str]:
    auction_date = datetime.strptime(
        event["auction_date"], "%Y-%m-%d"
    ).date()
    candidates: list[str] = []
    for delta in range(1, MAX_ANNOUNCEMENT_LOOKBACK_DAYS + 1):
        announcement_date = auction_date - timedelta(days=delta)
        date_part = announcement_date.strftime("%Y%m%d")
        year = announcement_date.year
        for sequence in range(1, MAX_PDF_SEQUENCE + 1):
            candidates.append(
                f"{TREASURY_PDF_BASE}/{year}/A_{date_part}_{sequence}.pdf"
            )
    return candidates


def _resolve_announcement(event: dict) -> dict:
    errors: list[str] = []
    candidates = _candidate_urls(event)
    for url in candidates:
        try:
            pdf = _fetch_bytes(url)
            text = _pdf_text(pdf)
            if not _pdf_matches_event(text, event):
                continue
            document_date, embargo_time, release_ts = _parse_embargo_timestamp(text)
            content_fp = hashlib.sha256(pdf).hexdigest()
            parsed_doc = datetime.strptime(document_date, "%B %d, %Y").date()
            auction_date = datetime.strptime(
                event["auction_date"], "%Y-%m-%d"
            ).date()
            record_date = datetime.strptime(
                event["record_date"], "%Y-%m-%d"
            ).date()

            if parsed_doc >= auction_date:
                errors.append(
                    f"document date {parsed_doc.isoformat()} is not before "
                    f"auction_date {event['auction_date']}"
                )
                continue

            return {
                "status": "TIMESTAMP_VALIDATED",
                "source_url": url,
                "source_identifier": f"{event['cusip']}:{event['auction_date']}",
                "document_date": document_date,
                "embargoed_until_local": embargo_time,
                "release_timestamp_utc": release_ts,
                "content_sha256": content_fp,
                "pdf_byte_length": len(pdf),
                "record_date_minus_document_date_days": (
                    record_date - parsed_doc
                ).days,
                "document_date_before_q019_record_date": parsed_doc < record_date,
            }
        except SourceError as exc:
            errors.append(str(exc))

    return {
        "status": "TIMESTAMP_INSUFFICIENT",
        "source_url": None,
        "source_identifier": f"{event['cusip']}:{event['auction_date']}",
        "document_date": None,
        "embargoed_until_local": None,
        "release_timestamp_utc": None,
        "content_sha256": None,
        "pdf_byte_length": None,
        "errors": errors[-5:],
    }


def _next_xnys_session(session_dates: list[date], value: date) -> date | None:
    for session in session_dates:
        if session > value:
            return session
    return None


def run(*, output_path: str | Path) -> dict:
    events = _treasury_events()
    if not events:
        raise SourceError("Q019 Treasury event population is empty")

    calendar = xcals.get_calendar("XNYS")
    sessions = calendar.sessions_in_range(
        STUDY_START.isoformat(), STUDY_END.isoformat()
    )
    session_dates = [stamp.date() for stamp in sessions]

    results: list[dict] = []
    for event in events:
        announcement = _resolve_announcement(event)
        record_date = datetime.strptime(event["record_date"], "%Y-%m-%d").date()
        next_session = _next_xnys_session(session_dates, record_date)

        row = {
            "q019": {
                "record_date": event["record_date"],
                "auction_date": event["auction_date"],
                "cusip": event["cusip"],
                "security_type": event.get("security_type"),
                "security_term": event.get("security_term"),
            },
            "announcement": announcement,
            "pit": {
                "first_following_xnys_session": (
                    next_session.isoformat() if next_session else None
                ),
                "information_timestamp_before_following_session": (
                    announcement["release_timestamp_utc"] is not None
                    and next_session is not None
                ),
            },
        }
        results.append(row)

    sufficient = sum(
        row["announcement"]["status"] == "TIMESTAMP_VALIDATED"
        for row in results
    )
    total = len(results)
    coverage_ratio = sufficient / total
    status = (
        "COVERAGE_VALIDATED"
        if coverage_ratio >= MIN_TIMESTAMP_COVERAGE
        else "DATA_INSUFFICIENT"
    )

    result = {
        "schema_version": "1.0",
        "task_id": "Q-023-TREASURY-RELEASE-TIMESTAMP-PIT-FEASIBILITY",
        "status": status,
        "study_window": {
            "start": STUDY_START.isoformat(),
            "end": STUDY_END.isoformat(),
        },
        "event_population": {
            "source": "Q019 fixed Treasury 10-Year Note event population",
            "total_events": total,
            "timestamp_validated_events": sufficient,
            "timestamp_coverage_ratio": coverage_ratio,
            "minimum_required_ratio": MIN_TIMESTAMP_COVERAGE,
        },
        "source_policy": {
            "primary_sources_only": True,
            "allowed_hosts": [
                "www.treasurydirect.gov",
                "treasurydirect.gov",
            ],
            "release_timestamp_rule": (
                "document_date + explicit Embargoed Until time, "
                "interpreted in America/New_York"
            ),
            "missing_source_policy": "TIMESTAMP_INSUFFICIENT / no rescue source",
        },
        "pit_policy": {
            "calendar": "XNYS via exchange_calendars",
            "rule": "first XNYS session strictly after Q019 record_date",
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
            "promotion_decision": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "events": results,
    }
    result["fingerprint"] = _fingerprint(result)

    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "task_id": result["task_id"],
                "status": result["status"],
                "events": total,
                "timestamp_validated_events": sufficient,
                "coverage_ratio": coverage_ratio,
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=(
            "research/runs/source_feasibility/"
            "q023_treasury_release_timestamp_pit_feasibility.json"
        ),
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
