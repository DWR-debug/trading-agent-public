"""Q198 bounded historical Federal Register public-inspection PIT census.

This is archive/clock feasibility evidence only. It reads no market data and
does not authorize performance, selection, ranking, tuning, promotion, or live
execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


FROZEN_DATES = (
    "2020/01/10",
    "2020/04/22",
    "2020/12/16",
    "2026/10/02",
)

FILING_RE = re.compile(
    r"Filed on:(?P<filed_m>\\d{1,2})/(?P<filed_d>\\d{1,2})/(?P<filed_y>\\d{4})"
    r" at (?P<filed_h>\\d{1,2}):(?P<filed_min>\\d{2}) (?P<ampm>am|pm)"
    r"Scheduled Pub\\. Date:(?P<pub_m>\\d{1,2})/(?P<pub_d>\\d{1,2})/(?P<pub_y>\\d{4})",
    re.IGNORECASE,
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


def parse_public_inspection(text: str) -> dict[str, object]:
    page_match = re.search(
        r"#\s+(\d{2})/(\d{2})/(\d{4}) Public Inspection Issue",
        text,
    )
    if not page_match:
        raise ValueError("missing public-inspection issue heading")
    page_date = _iso_date(page_match.group(3), page_match.group(1), page_match.group(2))

    lower = text.lower()
    filing_records = list(FILING_RE.finditer(text))
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
            "regular": "# Regular Filing" in text,
            "special": "# Special Filing" in text,
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
        url = f"https://www.federalregister.gov/public-inspection/{date_path}"
        status, body = fetch(url)
        text = body.decode("utf-8", errors="replace")
        item: dict[str, object] = {
            "requested_date": date_path,
            "url": url,
            "http_status": status,
            "content_sha256": hashlib.sha256(body).hexdigest(),
        }
        if status == 200:
            try:
                parsed = parse_public_inspection(text)
                item["status"] = "PARSED"
                item["parsed"] = parsed
            except ValueError as exc:
                item["status"] = "PARSE_FAILED"
                item["error"] = str(exc)
        else:
            item["status"] = "SOURCE_UNAVAILABLE"
        pages.append(item)

    parsed = [x for x in pages if x.get("status") == "PARSED"]
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-04-Q198-HISTORICAL-PIT-CLOCK-CENSUS",
        "status": "Q198_PIT_CLOCK_CENSUS_COMPLETED",
        "frozen_dates": list(FROZEN_DATES),
        "pages": pages,
        "aggregate": {
            "pages_requested": len(pages),
            "pages_parsed": len(parsed),
            "all_pages_parsed": len(parsed) == len(pages),
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
            "candidate-specific correction/withdrawal lineage, immutable historical "
            "reconstruction, entity mapping, and independent PIT reproduction"
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
