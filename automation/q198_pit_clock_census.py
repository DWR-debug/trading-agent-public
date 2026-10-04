"""Q198 bounded historical Federal Register public-inspection PIT census.

This is archive/clock feasibility evidence only. It reads no market data and
does not authorize performance, selection, ranking, tuning, promotion, or live
execution.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


FROZEN_DATES = (
    "2020/01/10",
    "2020/04/22",
    "2020/12/16",
    "2026/10/02",
)

FILING_RE = re.compile(
    r"Filed on:\s*(?P<filed_m>\d{1,2})/(?P<filed_d>\d{1,2})/(?P<filed_y>\d{4})"
    r"\s+at\s+(?P<filed_h>\d{1,2}):(?P<filed_min>\d{2})\s+(?P<ampm>am|pm)"
    r"\s*Scheduled Pub\. Date:\s*(?P<pub_m>\d{1,2})/(?P<pub_d>\d{1,2})/(?P<pub_y>\d{4})",
    re.IGNORECASE,
)

HISTORICAL_API_TEMPLATE = (
    "https://www.federalregister.gov/api/v1/public-inspection-documents.json"
    "?conditions%5Bavailable_on%5D={date}&per_page=1000"
)

ACCESS_BLOCK_MARKERS = (
    "request access",
    "your request has been flagged as potentially automated",
    "unblock.federalregister.gov",
    "recaptcha",
    "aggressive automated scraping",
)


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DWR-debug/trading-agent-public/Q198-PIT-census/1",
            "Accept": "text/html,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}".encode()


def _iso_date(y: str, m: str, d: str) -> str:
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"




class _HTMLTextParser(HTMLParser):
    """Extract visible source text from raw HTML deterministically."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.parts.append(value)

    def text(self) -> str:
        return " ".join(self.parts)


def _normalize_source_text(source: str) -> str:
    """Normalize raw HTML and textual fixtures without changing field values."""
    parser = _HTMLTextParser()
    try:
        parser.feed(source)
        parser.close()
        normalized = parser.text()
    except Exception:
        normalized = re.sub(r"<[^>]+>", " ", source)
    normalized = html.unescape(normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _is_access_blocked(normalized: str) -> bool:
    lowered = normalized.lower()
    return any(marker in lowered for marker in ACCESS_BLOCK_MARKERS)


def parse_public_inspection_api(payload: str, requested_date: str) -> dict[str, object]:
    """Parse the officially supported historical Public Inspection By-Date API."""
    data = json.loads(payload)
    results = data.get("results")
    count = data.get("count")
    if not isinstance(results, list) or not isinstance(count, int):
        raise ValueError("invalid historical public-inspection API payload")
    if count != len(results):
        raise ValueError(f"unexpected pagination: count={count} results={len(results)}")
    rows: list[dict[str, object]] = []
    missing_filed = 0
    missing_publication = 0
    same_day = 0
    correction_or_withdrawal = 0
    for item in results:
        if not isinstance(item, dict):
            raise ValueError("invalid historical public-inspection result row")
        filed_at = item.get("filed_at")
        publication_date = item.get("publication_date")
        document_number = item.get("document_number")
        issue_date = item.get("last_public_inspection_issue")
        if not document_number or not issue_date:
            raise ValueError("historical public-inspection row missing identity/issue date")
        if filed_at is None:
            missing_filed += 1
        else:
            filed_date = str(filed_at)[:10]
            if publication_date and filed_date == str(publication_date):
                same_day += 1
        if publication_date is None:
            missing_publication += 1
        note = str(item.get("editorial_note") or "").lower()
        if any(token in note for token in ("correction", "withdrawal", "withdrawn", "agency letter requesting")):
            correction_or_withdrawal += 1
        rows.append({
            "document_number": str(document_number),
            "filed_at": filed_at,
            "publication_date": publication_date,
            "last_public_inspection_issue": issue_date,
            "filing_type": item.get("filing_type"),
        })
    return {
        "page_date": requested_date,
        "source_route": "official_api_by_date",
        "api_count": count,
        "filing_records": len(rows),
        "records_with_filed_timestamp": len(rows) - missing_filed,
        "records_with_scheduled_publication_date": len(rows) - missing_publication,
        "missing_filed_timestamp_count": missing_filed,
        "missing_publication_date_count": missing_publication,
        "same_day_clock_ambiguous_count": same_day,
        "correction_or_withdrawal_note_count": correction_or_withdrawal,
        "sample_rows": rows[:25],
        "official_clock_contract": {
            "filed_timestamp_is_primary_boundary": True,
            "online_posting_time_not_substituted": True,
            "publication_date_separate": True,
            "effective_date_separate": True,
            "corrections_and_withdrawals_must_fail_closed": True,
            "archive_snapshot_mutation_not_allowed": True,
        },
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

def parse_public_inspection(text: str) -> dict[str, object]:
    normalized = _normalize_source_text(text)
    page_match = re.search(
        r"(?:#\s+)?(\d{2})/(\d{2})/(\d{4}) Public Inspection Issue",
        normalized,
    )
    if not page_match:
        raise ValueError("missing public-inspection issue heading")
    page_date = _iso_date(page_match.group(3), page_match.group(1), page_match.group(2))

    lower = normalized.lower()
    filing_records = list(FILING_RE.finditer(normalized))
    same_day = 0
    rows: list[dict[str, str]] = []
    for match in filing_records:
        filed_date = _iso_date(
            match.group("filed_y"), match.group("filed_m"), match.group("filed_d")
        )
        pub_date = _iso_date(
            match.group("pub_y"), match.group("pub_m"), match.group("pub_d")
        )
        if filed_date == pub_date:
            same_day += 1
        hour = int(match.group("filed_h")) % 12
        if match.group("ampm").lower() == "pm":
            hour += 12
        rows.append(
            {
                "filed_date": filed_date,
                "filed_time_et": f"{hour:02d}:{match.group('filed_min')}",
                "scheduled_publication_date": pub_date,
            }
        )

    result = {
        "page_date": page_date,
        "regular_or_special_sections_present": {
            "regular": "Regular Filing" in normalized,
            "special": "Special Filing" in normalized,
        },
        "filing_records": len(rows),
        "records_with_filed_timestamp": sum(bool(x.get("filed_time_et")) for x in rows),
        "records_with_scheduled_publication_date": sum(
            bool(x.get("scheduled_publication_date")) for x in rows
        ),
        "same_day_clock_ambiguous_count": same_day,
        "sample_rows": rows[:25],
        "official_clock_contract": {
            "filed_timestamp_is_primary_boundary": True,
            "online_posting_time_not_substituted": True,
            "publication_date_separate": True,
            "effective_date_separate": True,
            "corrections_and_withdrawals_must_fail_closed": True,
            "archive_snapshot_mutation_not_allowed": True,
        },
        "source_text_controls": {
            "contains_federal_register": "federal register" in lower,
            "contains_filed_on": "filed on:" in lower,
            "contains_scheduled_pub_date": "scheduled pub. date:" in lower,
        },
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    pages: list[dict[str, object]] = []
    for date_path in FROZEN_DATES:
        issue_date = date_path.replace("/", "-")
        api_url = HISTORICAL_API_TEMPLATE.format(date=issue_date)
        status, body = fetch(api_url)
        text_body = body.decode("utf-8", errors="replace")
        item: dict[str, object] = {
            "requested_date": date_path,
            "api_url": api_url,
            "http_status": status,
            "content_sha256": hashlib.sha256(body).hexdigest(),
        }
        if status == 200:
            try:
                parsed_api = parse_public_inspection_api(text_body, issue_date)
                item["status"] = "API_PARSED"
                item["parsed"] = parsed_api
                pages.append(item)
                continue
            except (ValueError, json.JSONDecodeError) as exc:
                item["api_error"] = str(exc)
        normalized = _normalize_source_text(text_body)
        fallback_url = f"https://www.federalregister.gov/public-inspection/{date_path}"
        fallback_status, fallback_body = fetch(fallback_url)
        fallback_text = fallback_body.decode("utf-8", errors="replace")
        item["fallback_url"] = fallback_url
        item["fallback_http_status"] = fallback_status
        item["fallback_content_sha256"] = hashlib.sha256(fallback_body).hexdigest()
        if _is_access_blocked(_normalize_source_text(fallback_text)):
            item["status"] = "SOURCE_ACCESS_BLOCKED"
            item["access_block_reason"] = "official Federal Register automated-access challenge/request-access page"
        elif fallback_status == 200:
            try:
                parsed_html = parse_public_inspection(fallback_text)
                item["status"] = "PARSED"
                item["parsed"] = parsed_html
            except ValueError as exc:
                item["status"] = "PARSE_FAILED"
                item["error"] = str(exc)
        elif _is_access_blocked(normalized):
            item["status"] = "SOURCE_ACCESS_BLOCKED"
            item["access_block_reason"] = "official Federal Register automated-access challenge/request-access page"
        else:
            item["status"] = "SOURCE_UNAVAILABLE"
        pages.append(item)


    parsed = [x for x in pages if x.get("status") in ("API_PARSED", "PARSED")]
    api_parsed = [x for x in pages if x.get("status") == "API_PARSED"]
    blocked = [x for x in pages if x.get("status") == "SOURCE_ACCESS_BLOCKED"]
    if len(blocked) == len(pages):
        overall_status = "Q198_PIT_CLOCK_CENSUS_BLOCKED_SOURCE_ACCESS"
    elif len(parsed) >= 3:
        overall_status = "Q198_PIT_CLOCK_CENSUS_COMPLETED"
    else:
        overall_status = "Q198_PIT_CLOCK_CENSUS_INCOMPLETE_SOURCE_ACCESS"

    result = {
        "schema_version": "1.1",
        "task_id": "Q-2026-10-04-Q198-HISTORICAL-PIT-CLOCK-CENSUS",
        "status": overall_status,
        "frozen_dates": list(FROZEN_DATES),
        "pages": pages,
        "aggregate": {
            "pages_requested": len(pages),
            "pages_parsed": len(parsed),
            "pages_api_parsed": len(api_parsed),
            "pages_access_blocked": len(blocked),
            "all_pages_parsed": len(parsed) == len(pages),
            "all_pages_api_parsed": len(api_parsed) == len(pages),
            "all_pages_access_blocked": len(blocked) == len(pages),
            "all_have_filed_timestamps": all(
                int(x["parsed"]["records_with_filed_timestamp"]) > 0 for x in parsed
            ) if parsed else False,
            "all_have_scheduled_publication_dates": all(
                int(x["parsed"]["records_with_scheduled_publication_date"]) > 0
                for x in parsed
            ) if parsed else False,
            "same_day_ambiguous_total": sum(
                int(x["parsed"]["same_day_clock_ambiguous_count"]) for x in parsed
            ),
        },
        "next_gate": (
            "historical By-Date API coverage is now mechanically available; next establish candidate-specific "
            "correction/withdrawal lineage, frozen issuer/entity mapping, event classification, and independent PIT reproduction"
        ),
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "pages_parsed": result["aggregate"]["pages_parsed"],
                "pages_access_blocked": result["aggregate"]["pages_access_blocked"],
                "all_pages_parsed": result["aggregate"]["all_pages_parsed"],
                "same_day_ambiguous_total": result["aggregate"]["same_day_ambiguous_total"],
                "receipt_fingerprint": result["receipt_fingerprint"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
