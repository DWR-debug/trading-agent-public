"""Q120-R2: bounded inventory of official CFTC COT release-date exceptions.

The receipt preserves exception-table dates as reported by CFTC. It deliberately
does not claim a complete historical release calendar or an exact first-public
timestamp. Source/PIT feasibility only; no performance or trading authority.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
from typing import Any, Callable

RELEASE_SCHEDULE_URL = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm"
SPECIAL_ANNOUNCEMENTS_URL = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm"
UPSTREAM_RUN_ID = 38456880720
UPSTREAM_TASK_ID = "Q-2026-10-01-120-CFTC-POSITIONING-SOURCE-FEASIBILITY"
UPSTREAM_RECEIPT_FINGERPRINT = "9e79abc9fac1b9d1599b35e111e82e19f8b365d99e06a447638d0c0135321445"
MAX_REQUESTS = 2
MAX_RESPONSE_BYTES = 350_000
MAX_TOTAL_BYTES = 700_000
REQUEST_PATH = Path("research/run_requests/q120r2_cftc_release_exception_inventory.trigger")
FROZEN = {
    "RUN_Q120R2_CFTC_RELEASE_EXCEPTION_INVENTORY": "true",
    "UPSTREAM_RUN_ID": str(UPSTREAM_RUN_ID),
    "UPSTREAM_TASK_ID": UPSTREAM_TASK_ID,
    "UPSTREAM_RECEIPT_FINGERPRINT": UPSTREAM_RECEIPT_FINGERPRINT,
    "RELEASE_SCHEDULE_URL": RELEASE_SCHEDULE_URL,
    "SPECIAL_ANNOUNCEMENTS_URL": SPECIAL_ANNOUNCEMENTS_URL,
    "MAX_REQUESTS": str(MAX_REQUESTS),
    "MAX_RESPONSE_BYTES": str(MAX_RESPONSE_BYTES),
    "MAX_TOTAL_BYTES": str(MAX_TOTAL_BYTES),
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}


class ProbeError(RuntimeError):
    pass


class HtmlTables(HTMLParser):
    """Extract simple HTML tables while retaining their cell text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.table_depth = 0
        self.current_table: list[list[str]] | None = None
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            if self.table_depth == 0:
                self.current_table = []
            self.table_depth += 1
        elif self.table_depth and tag == "tr":
            self.current_row = []
        elif self.table_depth and self.current_row is not None and tag in {"th", "td"}:
            self.current_cell = []

    def handle_data(self, data: str) -> None:
        if self.current_cell is not None:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.table_depth and tag in {"th", "td"} and self.current_cell is not None:
            value = " ".join("".join(self.current_cell).split())
            if self.current_row is not None:
                self.current_row.append(value)
            self.current_cell = None
        elif self.table_depth and tag == "tr" and self.current_row is not None:
            if self.current_table is not None:
                self.current_table.append(self.current_row)
            self.current_row = None
            self.current_cell = None
        elif tag == "table" and self.table_depth:
            self.table_depth -= 1
            if self.table_depth == 0 and self.current_table is not None:
                self.tables.append(self.current_table)
                self.current_table = None
                self.current_row = None
                self.current_cell = None


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw:
            continue
        if "=" not in raw:
            raise ProbeError(f"REQUEST_LINE_INVALID:{line_no}")
        key, value = raw.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or key in values:
            raise ProbeError(f"REQUEST_KEY_INVALID_OR_DUPLICATE:{line_no}")
        values[key] = value
    if set(values) != set(FROZEN) | {"REQUEST_SEQUENCE"}:
        raise ProbeError("REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN.items():
        if values.get(key) != expected:
            raise ProbeError(f"FROZEN_REQUEST_MISMATCH:{key}")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values.get("REQUEST_SEQUENCE", "")):
        raise ProbeError("REQUEST_SEQUENCE_INVALID")
    return values


def validate_upstream(receipt: dict[str, Any]) -> None:
    if (
        receipt.get("task_id") != UPSTREAM_TASK_ID
        or receipt.get("status") != "Q120_SOURCE_ARCHIVE_AND_RELEASE_SCHEDULE_FEASIBILITY_COMPLETED"
        or receipt.get("receipt_fingerprint") != UPSTREAM_RECEIPT_FINGERPRINT
        or receipt.get("release_dates_recovered") is not False
        or receipt.get("safety", {}).get("paper_only") is not True
        or receipt.get("safety", {}).get("live_trading_enabled") is not False
    ):
        raise ProbeError("Q120R1_UPSTREAM_RECEIPT_PIN_MISMATCH")


def _date_cell(value: str) -> str | None:
    match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", value)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%m/%d/%Y").date().isoformat()
    except ValueError:
        return None


def _header_key(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def parse_exception_rows(html: str) -> list[dict[str, Any]]:
    parser = HtmlTables()
    parser.feed(html)
    required = {"cotreportdate", "originalpublishdate", "newpublishdate"}
    matches: list[dict[str, Any]] = []
    header_found = False

    for table in parser.tables:
        for header_index, row in enumerate(table):
            headers = [_header_key(cell) for cell in row]
            if not required.issubset(set(headers)):
                continue
            header_found = True
            positions = {
                "report": headers.index("cotreportdate"),
                "original": headers.index("originalpublishdate"),
                "new": headers.index("newpublishdate"),
            }
            for source_row in table[header_index + 1 :]:
                if len(source_row) <= max(positions.values()):
                    continue
                report_raw = source_row[positions["report"]]
                original_raw = source_row[positions["original"]]
                new_raw = source_row[positions["new"]]
                report_date = _date_cell(report_raw)
                original_date = _date_cell(original_raw)
                new_date = _date_cell(new_raw)
                if report_date is None and original_date is None and new_date is None:
                    continue
                if not (report_date and original_date and new_date):
                    raise ProbeError("Q120R2_EXCEPTION_ROW_DATE_PARSE_FAILED:" + "|".join(source_row[:6]))
                if original_date < report_date or new_date < report_date:
                    raise ProbeError("Q120R2_EXCEPTION_DATE_ORDER_INVALID:" + report_date)
                matches.append({
                    "report_date": report_date,
                    "official_original_publish_date": original_date,
                    "official_new_publish_date": new_date,
                    "publish_date_changed": original_date != new_date,
                    "report_date_cell": report_raw,
                    "original_publish_date_cell": original_raw,
                    "new_publish_date_cell": new_raw,
                    "source": "CFTC Historical Special Announcements table",
                })
            break

    if not header_found:
        raise ProbeError("Q120R2_EXCEPTION_TABLE_HEADER_NOT_FOUND")
    if not matches:
        raise ProbeError("Q120R2_EXCEPTION_TABLE_HAS_NO_PARSEABLE_ROWS")

    unique: dict[str, dict[str, Any]] = {}
    for row in matches:
        key = row["report_date"]
        prior = unique.get(key)
        if prior is not None and (
            prior["official_original_publish_date"] != row["official_original_publish_date"]
            or prior["official_new_publish_date"] != row["official_new_publish_date"]
        ):
            raise ProbeError("Q120R2_CONFLICTING_EXCEPTION_ROWS:" + key)
        unique[key] = row
    return [unique[key] for key in sorted(unique)]


def fetch_page(url: str, max_bytes: int) -> tuple[int, bytes, dict[str, str], str, str | None]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DWR-debug/trading-agent-public/Q120R2-release-exception-inventory/1",
            "Accept": "text/html",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(max_bytes)
            headers = {key.lower(): value for key, value in response.headers.items()}
            final_url = response.geturl()
            status = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as exc:
        body = exc.read(max_bytes)
        headers = {key.lower(): value for key, value in exc.headers.items()} if exc.headers else {}
        return int(exc.code), body, headers, url, "HTTP_ERROR"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, b"", {}, url, f"TRANSPORT_ERROR:{type(exc).__name__}"
    declared = headers.get("content-length")
    if len(body) >= max_bytes or (declared and declared.isdigit() and int(declared) > len(body)):
        return status, body, headers, final_url, "RESPONSE_LIMIT_REACHED_OR_TRUNCATED"
    return status, body, headers, final_url, None


def run(
    request_path: Path,
    upstream_receipt_path: Path,
    output_path: Path,
    *,
    fetcher: Callable[[str, int], tuple[int, bytes, dict[str, str], str, str | None]] = fetch_page,
) -> dict[str, Any]:
    request = read_request(request_path)
    upstream = json.loads(upstream_receipt_path.read_text(encoding="utf-8"))
    validate_upstream(upstream)
    requests: list[dict[str, Any]] = []
    errors: list[str] = []
    downloaded_bytes = 0
    exceptions: list[dict[str, Any]] = []
    schedule_markers: dict[str, bool] = {}

    for label, url in (
        ("release_schedule", RELEASE_SCHEDULE_URL),
        ("historical_special_announcements", SPECIAL_ANNOUNCEMENTS_URL),
    ):
        remaining = MAX_TOTAL_BYTES - downloaded_bytes
        if len(requests) >= MAX_REQUESTS or remaining <= 0:
            errors.append(f"{label}:REQUEST_OR_TOTAL_BYTE_BUDGET_EXHAUSTED")
            continue
        limit = min(MAX_RESPONSE_BYTES, remaining)
        status, body, headers, final_url, error = fetcher(url, limit)
        downloaded_bytes += len(body)
        record = {
            "label": label,
            "requested_url": url,
            "final_url": final_url,
            "http_status": status,
            "response_bytes": len(body),
            "response_sha256": hashlib.sha256(body).hexdigest() if body else None,
            "content_type": headers.get("content-type"),
            "last_modified": headers.get("last-modified"),
            "error": error,
        }
        requests.append(record)
        if error or status != 200:
            errors.append(f"{label}:{error or 'HTTP_' + str(status)}")
            continue
        text = body.decode("utf-8", errors="replace")
        if label == "release_schedule":
            schedule_markers = {
                "release_time_1530_et": "3:30 p.m. Eastern time" in text,
                "2026_schedule_present": "2026 Release Schedule" in text,
            }
            if not all(schedule_markers.values()):
                errors.append("release_schedule:REQUIRED_OFFICIAL_MARKERS_MISSING")
        else:
            try:
                exceptions = parse_exception_rows(text)
            except ProbeError as exc:
                errors.append("historical_special_announcements:" + str(exc))

    changed = [row for row in exceptions if row["publish_date_changed"]]
    result: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q120r2_cftc_release_exception_inventory",
        "candidate_id": "Q120-R2",
        "task_id": "Q-2026-10-13-120R2-CFTC-RELEASE-EXCEPTION-INVENTORY",
        "status": "Q120R2_CFTC_RELEASE_EXCEPTION_INVENTORY_COMPLETED" if not errors else "Q120R2_CFTC_RELEASE_EXCEPTION_INVENTORY_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": __import__("os").environ.get("GITHUB_SHA"),
        "upstream": {
            "run_id": UPSTREAM_RUN_ID,
            "task_id": UPSTREAM_TASK_ID,
            "receipt_fingerprint": upstream["receipt_fingerprint"],
        },
        "method": {
            "official_sources_only": True,
            "metadata_or_small_html_only": True,
            "max_request_count": MAX_REQUESTS,
            "max_response_bytes": MAX_RESPONSE_BYTES,
            "max_total_download_bytes": MAX_TOTAL_BYTES,
            "response_bodies_persisted": False,
            "special_announcements_parsed_as_official_exception_rows": True,
        },
        "requests": requests,
        "summary": {
            "request_count": len(requests),
            "download_bytes": downloaded_bytes,
            "official_exception_rows_parsed": len(exceptions),
            "rows_with_changed_publish_date": len(changed),
            "rows_with_same_original_and_new_date": len(exceptions) - len(changed),
            "exception_report_years": sorted({row["report_date"][:4] for row in exceptions}),
            "errors": errors,
        },
        "official_exception_rows": exceptions,
        "release_schedule_markers": schedule_markers,
        "pit_interpretation": {
            "official_listed_exception_dates_recovered": bool(exceptions),
            "complete_historical_release_calendar_recovered": False,
            "unlisted_dates_assumed_to_follow_normal_schedule": False,
            "exact_first_publication_time_proven": False,
            "report_date_equals_release_date_assumed": False,
            "same_day_formal_use_allowed": False,
            "known_exception_rows_may_be_auto_applied": False,
        },
        "governance": {
            "performance": False,
            "performance_authorized": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
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
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "exception_rows": len(exceptions),
        "changed_dates": len(changed),
        "request_count": len(requests),
        "download_bytes": downloaded_bytes,
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--upstream-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.request, args.upstream_receipt, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
