"""Q127-R4: verify the official FINRA year-filtered listing for fixed daily files.

This workpack reads two small official listing pages only. It never downloads
FINRA target file bodies. Presence in today's listing is not a historical
capture and the official 6pm ET statement is an upper-bound contract, not an
observed first-publication timestamp. Same-day PIT and revision lineage remain
unproven.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request
from typing import Any, Callable

R1_FP = "2cbe22c49d885f527ac523ed74ab1e13a843c23999916c674282de6977e9c33c"
R1_TASK = "Q-2026-10-03-127R1-FINRA-REGSHO-HISTORICAL-PIT"
R1_RUN_ID = 38455702686
FIXED_DATES = ("2024-02-05", "2024-07-01", "2025-01-02", "2025-09-24")
SYMBOLS = ("SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN")
URL_TEMPLATE = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{yyyymmdd}.txt"
LISTING_BASE = "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files"
URL_2024 = LISTING_BASE + "?custom_month%5Bmonth%5D=any&custom_year%5Byear%5D=2"
URL_2025 = LISTING_BASE + "?custom_month%5Bmonth%5D=any&custom_year%5Byear%5D=1"
MAX_REQUESTS = 2
MAX_RESPONSE_BYTES = 500_000
MAX_TOTAL_BYTES = 1_000_000
FROZEN = {
    "RUN_Q127R4_FINRA_OFFICIAL_LISTING_METADATA": "true",
    "R1_SOURCE_RUN_ID": str(R1_RUN_ID),
    "R1_RECEIPT_FINGERPRINT": R1_FP,
    "R1_TASK_ID": R1_TASK,
    "FIXED_DATES": ",".join(FIXED_DATES),
    "FIXED_SYMBOLS": ",".join(SYMBOLS),
    "LISTING_2024_URL": URL_2024,
    "LISTING_2025_URL": URL_2025,
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


class ListingRows(HTMLParser):
    """Collect exact anchors and visible context from their containing list item."""

    def __init__(self, targets: set[str]) -> None:
        super().__init__(convert_charrefs=True)
        self.targets = targets
        self.stack: list[dict[str, Any]] = []
        self.current_anchor: str | None = None
        self.rows: dict[str, list[dict[str, Any]]] = {target: [] for target in targets}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = {str(k).lower(): v for k, v in attrs}
        if tag == "li":
            self.stack.append({"text": [], "hrefs": [], "anchor_text": {}})
        elif tag == "a" and self.stack:
            href = attributes.get("href")
            if href:
                href = str(href)
                self.stack[-1]["hrefs"].append(href)
                self.stack[-1]["anchor_text"].setdefault(href, [])
                self.current_anchor = href

    def handle_data(self, data: str) -> None:
        if self.stack:
            self.stack[-1]["text"].append(data)
            if self.current_anchor:
                self.stack[-1]["anchor_text"].setdefault(self.current_anchor, []).append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a":
            self.current_anchor = None
        elif tag == "li" and self.stack:
            item = self.stack.pop()
            row_text = " ".join("".join(item["text"]).split())
            for href in item["hrefs"]:
                if href not in self.targets:
                    continue
                anchor_text = " ".join("".join(item["anchor_text"].get(href, [])).split())
                size = re.search(r"\bTXT\s+([0-9]+(?:\.[0-9]+)?\s*(?:KB|MB|Bytes))\b", row_text, re.IGNORECASE)
                self.rows[href].append({
                    "target_url": href,
                    "anchor_label": anchor_text,
                    "visible_row_text": row_text,
                    "file_size_label": size.group(1) if size else None,
                    "updated_label_visible_in_row": bool(re.search(r"\bUpdated\b", row_text, re.IGNORECASE)),
                })


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


def target_urls() -> dict[str, str]:
    return {
        value: URL_TEMPLATE.format(yyyymmdd=value.replace("-", ""))
        for value in FIXED_DATES
    }


def validate_r1(receipt: dict[str, Any]) -> None:
    if (
        receipt.get("task_id") != R1_TASK
        or receipt.get("status") != "Q127R1_SOURCE_PIT_FEASIBILITY_COMPLETED"
        or receipt.get("receipt_fingerprint") != R1_FP
        or set((receipt.get("observations") or {}).keys()) != set(FIXED_DATES)
        or receipt.get("pit", {}).get("same_day_pit_safe") is not False
        or receipt.get("pit", {}).get("revision_lineage_established") is not False
    ):
        raise ProbeError("Q127R1_UPSTREAM_RECEIPT_PIN_MISMATCH")
    urls = target_urls()
    for sample_date in FIXED_DATES:
        obs = receipt["observations"][sample_date]
        if obs.get("source_url") != urls[sample_date] or obs.get("status") != "PASS":
            raise ProbeError(f"Q127R1_FIXED_OBSERVATION_MISMATCH:{sample_date}")
        if set((obs.get("rows_for_fixed_symbols") or {}).keys()) != set(SYMBOLS):
            raise ProbeError(f"Q127R1_FIXED_SYMBOL_COVERAGE_MISMATCH:{sample_date}")


def year_filter_present(html: str, year: int) -> bool:
    value = {2024: "2", 2025: "1"}.get(year)
    if value is None:
        return False
    pattern = rf'<option\b(?=[^>]*\bvalue="{value}")(?=[^>]*\bselected)[^>]*>\s*{year}\s*</option>'
    return re.search(pattern, html, re.IGNORECASE | re.DOTALL) is not None


def page_markers(html: str) -> dict[str, bool]:
    plain = unescape(re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>|<[^>]+>", " ", html))
    plain = " ".join(plain.split()).casefold()
    return {
        "by_1800_et_same_trade_date": "no later than 6:00:00pm et of the same day on the relevant trade date" in plain,
        "later_update_possible": "in rare instances, finra may need to update a file on a subsequent day" in plain,
        "original_and_updated_both_listed": "finra will reflect both the original and updated files on this page" in plain,
        "updated_variant_is_labelled": 'identify the updated file as "updated"' in plain,
    }


def parse_listing_page(html: str, year: int, dates: tuple[str, ...]) -> dict[str, Any]:
    if not year_filter_present(html, year):
        raise ProbeError(f"YEAR_FILTER_NOT_CONFIRMED:{year}")
    targets = target_urls()
    selected = {day: targets[day] for day in dates}
    parser = ListingRows(set(selected.values()))
    parser.feed(html)
    result: dict[str, Any] = {}
    for day, url in selected.items():
        rows = parser.rows[url]
        result[day] = {
            "source_url": url,
            "exact_url_listing_count": len(rows),
            "listing_rows": rows,
            "exact_url_listed_once": len(rows) == 1,
        }
    return {
        "selected_year": year,
        "selected_year_filter_verified": True,
        "publication_policy_markers": page_markers(html),
        "target_observations": result,
    }


def fetch_page(url: str, max_bytes: int) -> tuple[int, bytes, dict[str, str], str, str | None]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DWR-debug/trading-agent-public/Q127R4-FINRA-Official-Listing/1",
            "Accept": "text/html",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(max_bytes + 1)
            headers = {key.lower(): value for key, value in response.headers.items()}
            final_url = response.geturl()
            status = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as exc:
        body = exc.read(max_bytes + 1)
        headers = {key.lower(): value for key, value in exc.headers.items()} if exc.headers else {}
        return int(exc.code), body[:max_bytes], headers, url, "HTTP_ERROR"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, b"", {}, url, f"TRANSPORT_ERROR:{type(exc).__name__}"
    if len(body) > max_bytes:
        return status, body[:max_bytes], headers, final_url, "RESPONSE_BYTE_LIMIT_EXCEEDED"
    declared = headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > len(body):
        return status, body, headers, final_url, "RESPONSE_TRUNCATED_BY_LIMIT"
    return status, body, headers, final_url, None


def run(
    request_path: Path,
    source_receipt_path: Path,
    output_path: Path,
    *,
    fetcher: Callable[[str, int], tuple[int, bytes, dict[str, str], str, str | None]] = fetch_page,
) -> dict[str, Any]:
    read_request(request_path)
    upstream = json.loads(source_receipt_path.read_text(encoding="utf-8"))
    validate_r1(upstream)
    request_records: list[dict[str, Any]] = []
    errors: list[str] = []
    downloaded_bytes = 0
    observations: dict[str, Any] = {}
    overall_policy_markers: dict[str, bool] = {}

    pages = (
        (2024, URL_2024, ("2024-02-05", "2024-07-01")),
        (2025, URL_2025, ("2025-01-02", "2025-09-24")),
    )
    for year, url, dates in pages:
        remaining = MAX_TOTAL_BYTES - downloaded_bytes
        if len(request_records) >= MAX_REQUESTS or remaining <= 0:
            errors.append(f"{year}:REQUEST_OR_TOTAL_BYTE_BUDGET_EXHAUSTED")
            continue
        limit = min(MAX_RESPONSE_BYTES, remaining)
        status, body, headers, final_url, error = fetcher(url, limit)
        downloaded_bytes += len(body)
        request_records.append({
            "year": year,
            "requested_url": url,
            "final_url": final_url,
            "http_status": status,
            "response_bytes": len(body),
            "response_sha256": hashlib.sha256(body).hexdigest() if body else None,
            "content_type": headers.get("content-type"),
            "last_modified": headers.get("last-modified"),
            "error": error,
        })
        if error or status != 200:
            errors.append(f"{year}:{error or 'HTTP_' + str(status)}")
            continue
        try:
            parsed = parse_listing_page(body.decode("utf-8", errors="replace"), year, dates)
        except ProbeError as exc:
            errors.append(f"{year}:{exc}")
            continue
        observations.update(parsed["target_observations"])
        for key, value in parsed["publication_policy_markers"].items():
            overall_policy_markers[key] = overall_policy_markers.get(key, True) and value

    missing_dates = [day for day in FIXED_DATES if day not in observations]
    duplicate_or_missing = [
        day for day, item in observations.items()
        if not item["exact_url_listed_once"]
    ]
    required_markers = (
        "by_1800_et_same_trade_date",
        "later_update_possible",
        "original_and_updated_both_listed",
        "updated_variant_is_labelled",
    )
    for marker in required_markers:
        if overall_policy_markers.get(marker) is not True:
            errors.append("OFFICIAL_PUBLICATION_POLICY_MARKER_MISSING:" + marker)
    if missing_dates:
        errors.append("TARGET_DATE_EVIDENCE_MISSING:" + ",".join(missing_dates))
    if duplicate_or_missing:
        errors.append("TARGET_URL_NOT_LISTED_EXACTLY_ONCE:" + ",".join(sorted(duplicate_or_missing)))

    updated_dates = [
        day for day, item in observations.items()
        if item["listing_rows"] and item["listing_rows"][0]["updated_label_visible_in_row"]
    ]
    result: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q127r4_finra_official_listing_metadata",
        "candidate_id": "Q127-R4",
        "task_id": "Q-2026-10-14-127R4-FINRA-OFFICIAL-LISTING-METADATA",
        "status": "Q127R4_OFFICIAL_LISTING_METADATA_COMPLETED" if not errors else "Q127R4_OFFICIAL_LISTING_METADATA_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "upstream": {
            "run_id": R1_RUN_ID,
            "task_id": R1_TASK,
            "receipt_fingerprint": upstream["receipt_fingerprint"],
        },
        "fixed_population": {
            "dates": list(FIXED_DATES),
            "symbols": list(SYMBOLS),
            "target_url_count": len(FIXED_DATES),
        },
        "method": {
            "source": "FINRA official Daily Short Sale Volume Files year-filtered catalogue",
            "requests": 2,
            "max_response_bytes": MAX_RESPONSE_BYTES,
            "max_total_download_bytes": MAX_TOTAL_BYTES,
            "target_file_downloads": 0,
            "historical_archive_or_page_snapshot": False,
            "response_bodies_persisted": False,
        },
        "requests": request_records,
        "observations": observations,
        "summary": {
            "request_count": len(request_records),
            "download_bytes": downloaded_bytes,
            "target_urls_present_exactly_once": len(observations) == len(FIXED_DATES) and not duplicate_or_missing,
            "dates_with_updated_badge_in_current_listing": updated_dates,
            "errors": errors,
        },
        "pit_interpretation": {
            "official_nominal_publication_upper_bound_stated": overall_policy_markers.get("by_1800_et_same_trade_date", False),
            "later_update_possible_stated": overall_policy_markers.get("later_update_possible", False),
            "exact_first_publication_time_proven": False,
            "historical_listing_snapshot_proven": False,
            "original_version_bytes_preserved": False,
            "revision_lineage_established": False,
            "same_day_formal_use_allowed": False,
            "current_listing_presence_proves_historical_publication_time": False,
            "no_updated_badge_proves_no_historical_revision": False,
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
    console = {
        "status": result["status"],
        "request_count": len(request_records),
        "download_bytes": downloaded_bytes,
        "target_listing_counts": {day: item["exact_url_listing_count"] for day, item in observations.items()},
        "updated_badge_dates": updated_dates,
        "errors": errors[:20],
        "receipt_fingerprint": result["receipt_fingerprint"],
    }
    print(json.dumps(console, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.request, args.source_receipt, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
