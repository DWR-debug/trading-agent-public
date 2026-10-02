"""Q124 public-source feasibility probes.

Research-only. Verifies that the fixed Treasury and Cboe public source paths
are reachable and contain the minimum fields needed for the two quarantined
Q124 hypotheses. It never evaluates returns, selects candidates or authorizes
performance.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

TREASURY_API = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
    "v1/accounting/od/auctions_query"
)
TREASURY_URL = (
    TREASURY_API
    + "?fields=record_date,auction_date,security_type,security_term,"
      "bid_to_cover_ratio,high_yield,median_yield,low_yield"
      "&filter=security_type:eq:Note,security_term:eq:10-Year,"
      "record_date:gte:2024-01-01"
      "&page[size]=5&sort=-record_date"
)
CBOE_URL = "https://www.cboe.com/us/options/market_statistics/market/"


def fetch(url: str) -> tuple[int, str]:
    req = Request(url, headers={"User-Agent": "trading-agent-public/Q124-source-feasibility/1.0"})
    with urlopen(req, timeout=20) as response:
        return int(response.status), response.read().decode("utf-8", "replace")


def probe_treasury() -> dict:
    status, body = fetch(TREASURY_URL)
    payload = json.loads(body)
    data = payload.get("data", [])
    required = {
        "record_date", "auction_date", "security_type", "security_term",
        "bid_to_cover_ratio", "high_yield", "median_yield", "low_yield"
    }
    present = set(data[0]) if data else set()
    return {
        "status_code": status,
        "rows": len(data),
        "required_fields_present": required <= present,
        "source_status": "PUBLIC_SOURCE_VERIFIABLE" if data and required <= present else "DATA_INSUFFICIENT",
        "endpoint": TREASURY_API,
    }


def probe_cboe() -> dict:
    status, body = fetch(CBOE_URL)
    lower = body.lower()
    has_calls = "calls" in lower
    has_puts = "puts" in lower
    half_hour_rows = len(set(re.findall(r"\b\d{2}:30\b", body)))
    return {
        "status_code": status,
        "has_calls": has_calls,
        "has_puts": has_puts,
        "half_hour_markers": half_hour_rows,
        "current_public_market_stats": status == 200 and has_calls and has_puts and half_hour_rows >= 1,
        "historical_30m_archive_status": "UNPROVEN",
        "source_status": (
            "PUBLIC_CURRENT_SOURCE_VERIFIABLE"
            if status == 200 and has_calls and has_puts
            else "DATA_INSUFFICIENT"
        ),
        "endpoint": CBOE_URL,
    }


def build() -> dict:
    started = datetime.now(timezone.utc).isoformat()
    probes = {}
    errors = {}
    for name, fn in (("treasury", probe_treasury), ("cboe", probe_cboe)):
        try:
            probes[name] = fn()
        except Exception as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
            probes[name] = {"source_status": "PROBE_ERROR"}

    status = "Q124_SOURCE_FEASIBLE_PARTIAL"
    if errors:
        status = "Q124_SOURCE_FEASIBILITY_INCOMPLETE"
    if probes.get("treasury", {}).get("source_status") != "PUBLIC_SOURCE_VERIFIABLE":
        status = "Q124_TREASURY_SOURCE_INSUFFICIENT"
    result = {
        "schema_version": 1,
        "status": status,
        "generated_at_utc": started,
        "probes": probes,
        "errors": errors,
        "scientific_boundary": {
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "paper_only": True,
        "next_gate": "historical_archive_and_PIT_reconstruction",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q124_SOURCE_STATUS=" + result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
