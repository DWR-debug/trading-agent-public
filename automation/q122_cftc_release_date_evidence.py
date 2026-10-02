"""Q122 deterministic CFTC release-date evidence compiler.

Only release dates explicitly published by CFTC are classified as documented.
Regular cadence information is retained as schedule metadata but is never used
to fabricate a historical report-date -> release-date mapping.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

SPECIAL_URL = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm"
SCHEDULE_URL = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm"
UA = "trading-agent-public/Q122-release-date-evidence/1"
REPORT_RELEASE_RE = re.compile(
    r"(?P<report>\d{2}/\d{2}/\d{4})\s*\|\s*"
    r"(?P<original>\d{2}/\d{2}/\d{4})\s*\|\s*"
    r"(?P<new>\d{2}/\d{2}/\d{4})"
)

def fetch(url: str) -> tuple[str, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=45) as response:
        body = response.read()
        return response.geturl(), body

def md(date_text: str) -> str:
    return datetime.strptime(date_text, "%m/%d/%Y").date().isoformat()

def extract_documented_backlog(html: bytes) -> list[dict[str, str]]:
    text = html.decode("utf-8", errors="replace")
    rows = []
    seen: set[str] = set()
    for match in REPORT_RELEASE_RE.finditer(text):
        report = md(match.group("report"))
        original = md(match.group("original"))
        new = md(match.group("new"))
        key = (report, original, new)
        if report in seen:
            continue
        seen.add(report)
        rows.append({
            "report_date": report,
            "original_publish_date": original,
            "documented_new_publish_date": new,
            "evidence_type": "DOCUMENTED_SPECIAL_ANNOUNCEMENT",
        })
    return rows

def extract_schedule_metadata(html: bytes) -> dict[str, Any]:
    text = html.decode("utf-8", errors="replace")
    return {
        "release_time_et_documented": "3:30 p.m. Eastern time" in text,
        "2026_schedule_documented": "2026 Release Schedule" in text,
        "schedule_only_not_historical_mapping": True,
    }

def classify(report_date: str, documented: dict[str, dict[str, str]]) -> dict[str, str]:
    row = documented.get(report_date)
    if row:
        return {
            "report_date": report_date,
            "release_date": row["documented_new_publish_date"],
            "release_evidence_type": row["evidence_type"],
        }
    return {
        "report_date": report_date,
        "release_date": "",
        "release_evidence_type": "UNKNOWN",
    }

def build(rows: list[dict[str, str]], special_meta: dict[str, Any], schedule_meta: dict[str, Any]) -> dict[str, Any]:
    documented = {row["report_date"]: row for row in rows}
    test_dates = [
        "2025-09-30",
        "2025-10-07",
        "2025-11-18",
        "2025-12-30",
        "2026-01-06",
        "2019-01-08",
    ]
    classifications = [classify(d, documented) for d in test_dates]
    return {
        "schema_version": 1,
        "task_id": "Q-2026-10-02-122-CFTC-RELEASE-DATE-EVIDENCE",
        "status": "Q122_RELEASE_DATE_EVIDENCE_COMPILED",
        "documented_mapping_count": len(rows),
        "documented_mappings": rows,
        "test_classifications": classifications,
        "source_metadata": {
            "special_announcements": special_meta,
            "release_schedule": schedule_meta,
        },
        "rules": {
            "documented_release_dates_are_formalizable": True,
            "schedule_only_dates_are_formalizable": False,
            "unknown_release_dates_are_formalizable": False,
            "report_date_is_never_treated_as_release_date": True,
            "undocumented_friday_inference_used": False,
        },
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
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

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/q122_cftc_release_date_evidence/result.json"))
    args = parser.parse_args()

    special_url, special_body = fetch(SPECIAL_URL)
    schedule_url, schedule_body = fetch(SCHEDULE_URL)
    rows = extract_documented_backlog(special_body)
    if len(rows) < 10:
        raise RuntimeError(f"Q122_TOO_FEW_DOCUMENTED_MAPPINGS:{len(rows)}")
    result = build(
        rows,
        {
            "url": special_url,
            "sha256": hashlib.sha256(special_body).hexdigest(),
            "bytes": len(special_body),
        },
        {
            "url": schedule_url,
            "sha256": hashlib.sha256(schedule_body).hexdigest(),
            "bytes": len(schedule_body),
        },
    )
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q122_STATUS=" + result["status"])
    print("Q122_DOCUMENTED_MAPPINGS=" + str(result["documented_mapping_count"]))
    print("Q122_UNKNOWN_TESTS=" + str(sum(x["release_evidence_type"] == "UNKNOWN" for x in result["test_classifications"])))
    print("Q122_RECEIPT=" + result["receipt_fingerprint"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
