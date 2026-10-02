"""Q120 CFTC TFF archive/release feasibility probe.

This is a source/PIT-preparation stage only. It verifies that the official
CFTC TFF futures-only dataset exposes the fixed E-mini S&P 500 contract and
that official release-schedule / special-announcement pages are reachable.
It does not manufacture historical release timestamps and never evaluates
performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
CONTRACT_NAME = "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"
CFTC_CODE = "13874A"

def normalize_contract_name(value: object) -> str:
    """Normalize harmless upstream whitespace/case variation without broadening identity."""
    return " ".join(str(value or "").split()).upper()

START = "2011-01-01"
END = "2026-09-30"
UA = "trading-agent-public/Q120-source-feasibility"
FIELDS = ",".join([
    "market_and_exchange_names",
    "report_date_as_yyyy_mm_dd",
    "cftc_contract_market_code",
    "open_interest_all",
    "asset_mgr_positions_long",
    "asset_mgr_positions_short",
    "lev_money_positions_long",
    "lev_money_positions_short",
])

RELEASE_SCHEDULE = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm"
SPECIAL_ANNOUNCEMENTS = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm"


def fetch_rows() -> tuple[str, bytes, list[dict]]:
    params = {
        "$select": FIELDS,
        "$where": (
            f"cftc_contract_market_code='{CFTC_CODE}' "
            f"AND report_date_as_yyyy_mm_dd >= '{START}' "
            f"AND report_date_as_yyyy_mm_dd <= '{END}'"
        ),
        "$order": "report_date_as_yyyy_mm_dd ASC",
        "$limit": 5000,
    }
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        body = response.read()
    payload = json.loads(body.decode("utf-8"))
    rows = payload if isinstance(payload, list) else payload.get("data")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Q120_EMPTY_CFTC_POPULATION")
    return url, body, rows


def validate(rows: list[dict]) -> dict:
    required = {
        "market_and_exchange_names",
        "report_date_as_yyyy_mm_dd",
        "cftc_contract_market_code",
        "open_interest_all",
        "asset_mgr_positions_long",
        "asset_mgr_positions_short",
        "lev_money_positions_long",
        "lev_money_positions_short",
    }
    for row in rows:
        if not required.issubset(row):
            raise RuntimeError("Q120_REQUIRED_FIELD_MISSING")
        if normalize_contract_name(row["market_and_exchange_names"]) != normalize_contract_name(CONTRACT_NAME):
            raise RuntimeError("Q120_UNEXPECTED_CONTRACT")
        if str(row["cftc_contract_market_code"]).strip().upper() != CFTC_CODE:
            raise RuntimeError("Q120_UNEXPECTED_CONTRACT_CODE")
        if any(row.get(field) in (None, "") for field in required):
            raise RuntimeError("Q120_REQUIRED_FIELD_EMPTY")
        try:
            if float(row["open_interest_all"]) <= 0:
                raise RuntimeError("Q120_NONPOSITIVE_OPEN_INTEREST")
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Q120_INVALID_OPEN_INTEREST") from exc
    dates = [str(row["report_date_as_yyyy_mm_dd"]) for row in rows]
    if dates != sorted(dates):
        raise RuntimeError("Q120_REPORT_DATES_NOT_SORTED")
    return {
        "row_count": len(rows),
        "first_report_date": dates[0],
        "last_report_date": dates[-1],
        "contract_identity": CONTRACT_NAME,
        "contract_code": CFTC_CODE,
        "required_fields_complete": True,
        "report_dates_sorted": True,
    }


def fetch_page(url: str) -> tuple[str, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=45) as response:
        body = response.read()
        final_url = response.geturl()
    return final_url, body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/q120_cftc/q120_source_feasibility.json"))
    args = parser.parse_args()

    api_url, api_body, rows = fetch_rows()
    validation = validate(rows)
    schedule_url, schedule_body = fetch_page(RELEASE_SCHEDULE)
    special_url, special_body = fetch_page(SPECIAL_ANNOUNCEMENTS)

    schedule_text = schedule_body.decode("utf-8", errors="replace")
    special_text = special_body.decode("utf-8", errors="replace")
    schedule_markers = {
        "release_time_1530_et": "3:30 p.m. Eastern time" in schedule_text,
        "2026_schedule_present": "2026 Release Schedule" in schedule_text,
        "2025_interruption_documented": "October 1" in special_text and "November 12" in special_text,
        "backlog_schedule_documented": "11/19/2025" in special_text,
    }
    if not all(schedule_markers.values()):
        raise RuntimeError("Q120_OFFICIAL_RELEASE_SCHEDULE_MARKERS_MISSING")

    result = {
        "schema_version": 1,
        "task_id": "Q-2026-10-01-120-CFTC-POSITIONING-SOURCE-FEASIBILITY",
        "status": "Q120_SOURCE_ARCHIVE_AND_RELEASE_SCHEDULE_FEASIBILITY_COMPLETED",
        "source_url": api_url,
        "source_response_sha256": hashlib.sha256(api_body).hexdigest(),
        "official_release_schedule_url": schedule_url,
        "official_release_schedule_sha256": hashlib.sha256(schedule_body).hexdigest(),
        "official_special_announcements_url": special_url,
        "official_special_announcements_sha256": hashlib.sha256(special_body).hexdigest(),
        "study_window": {"start": START, "end": END},
        "validation": validation,
        "release_schedule_markers": schedule_markers,
        "release_dates_recovered": False,
        "governance": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "performance_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q120_STATUS=" + result["status"])
    print("Q120_ROWS=" + str(validation["row_count"]))
    print("Q120_FIRST_REPORT=" + validation["first_report_date"])
    print("Q120_LAST_REPORT=" + validation["last_report_date"])
    print("Q120_RECEIPT_FINGERPRINT=" + result["receipt_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
