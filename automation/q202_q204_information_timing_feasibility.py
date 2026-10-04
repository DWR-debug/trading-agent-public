"""Bounded Q202-Q204 information-timing source feasibility.

Discovery/source contract only. No market returns, ranking, tuning, holdout
selection, performance authorization, promotion, or live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}

BOUNDARY = {
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
}

FIXED = {
    "Q202_CT_STUDY": "https://clinicaltrials.gov/api/v2/studies/NCT00125528",
    "Q202_CT_HISTORY": "https://clinicaltrials.gov/study/NCT00125528?a=2&tab=history",
    "Q203_SEC_SUBMISSIONS": "https://data.sec.gov/submissions/CIK0000789019.json",
    "Q203_SEC_COMPANYFACTS": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json",
    "Q204_FR_20200110": "https://www.federalregister.gov/api/v1/public-inspection-documents.json?conditions%5Bavailable_on%5D=2020-01-10&per_page=1000",
    "Q204_FR_20201216": "https://www.federalregister.gov/api/v1/public-inspection-documents.json?conditions%5Bavailable_on%5D=2020-12-16&per_page=1000",
}

MARKERS = {
    "Q202_CT_STUDY": ["studyFirstPostDateStruct", "resultsFirstPostDateStruct", "lastUpdatePostDateStruct"],
    "Q203_SEC_SUBMISSIONS": ["filings", "recent"],
    "Q203_SEC_COMPANYFACTS": ["Assets", "Liabilities", "CashAndCashEquivalentsAtCarryingValue"],
}

def fetch(url: str, user_agent: str) -> tuple[int, bytes]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept": "application/json,text/html,*/*"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}".encode()

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def probe_markers(label: str, url: str, markers: list[str], user_agent: str) -> dict:
    status, body = fetch(url, user_agent)
    text = body.decode("utf-8", errors="replace")
    missing = [m for m in markers if m.lower() not in text.lower()]
    return {
        "url": url,
        "http_status": status,
        "reachable": status == 200,
        "missing_markers": missing,
        "content_sha256": digest(body),
        "scientific_boundary": BOUNDARY,
    }

def parse_fr_by_date(url: str) -> dict:
    status, body = fetch(url, "DWR-debug/trading-agent-public/Q204-information-timing/1")
    payload = json.loads(body.decode("utf-8", errors="replace"))
    results = payload.get("results")
    count = payload.get("count")
    if status != 200 or not isinstance(results, list) or not isinstance(count, int) or count != len(results):
        raise ValueError("invalid Federal Register By-Date payload")
    missing_filed = 0
    missing_publication = 0
    corrections = 0
    for row in results:
        if not isinstance(row, dict):
            raise ValueError("invalid Federal Register row")
        if row.get("filed_at") is None:
            missing_filed += 1
        if row.get("publication_date") is None:
            missing_publication += 1
        note = str(row.get("editorial_note") or "").lower()
        if any(x in note for x in ("correction", "withdrawal", "withdrawn")):
            corrections += 1
    return {
        "url": url,
        "http_status": status,
        "api_count": count,
        "records": len(results),
        "records_with_filed_timestamp": count - missing_filed,
        "records_with_publication_date": count - missing_publication,
        "missing_filed_timestamp_count": missing_filed,
        "missing_publication_date_count": missing_publication,
        "correction_or_withdrawal_note_count": corrections,
        "content_sha256": digest(body),
        "scientific_boundary": BOUNDARY,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    ua_ct = "DWR-debug/trading-agent-public/Q202/1"
    ua_sec = "DWR-debug/trading-agent-public/Q203/1 contact=research@localhost"

    sources = {
        "Q202": {
            "study": probe_markers("Q202_CT_STUDY", FIXED["Q202_CT_STUDY"], MARKERS["Q202_CT_STUDY"], ua_ct),
            "history_route": probe_markers("Q202_CT_HISTORY", FIXED["Q202_CT_HISTORY"], ["Study Record Versions"], ua_ct),
        },
        "Q203": {
            "submissions": probe_markers("Q203_SEC_SUBMISSIONS", FIXED["Q203_SEC_SUBMISSIONS"], MARKERS["Q203_SEC_SUBMISSIONS"], ua_sec),
            "companyfacts": probe_markers("Q203_SEC_COMPANYFACTS", FIXED["Q203_SEC_COMPANYFACTS"], MARKERS["Q203_SEC_COMPANYFACTS"], ua_sec),
        },
        "Q204": {
            "2020-01-10": parse_fr_by_date(FIXED["Q204_FR_20200110"]),
            "2020-12-16": parse_fr_by_date(FIXED["Q204_FR_20201216"]),
        },
    }

    candidate_status = {
        "Q202": "SOURCE_COMPONENT_READY" if sources["Q202"]["study"]["reachable"] else "BLOCKED_SOURCE_COMPONENT",
        "Q203": "SOURCE_COMPONENT_READY"
        if sources["Q203"]["submissions"]["reachable"] and sources["Q203"]["companyfacts"]["reachable"]
        else "BLOCKED_SOURCE_COMPONENT",
        "Q204": "SOURCE_COMPONENT_READY"
        if all(v["http_status"] == 200 for v in sources["Q204"].values())
        else "INCOMPLETE_SOURCE_COMPONENT",
    }

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-04-Q202-Q204-INFORMATION-TIMING-FEASIBILITY",
        "status": "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED",
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "fixed_routes": FIXED,
        "source_results": sources,
        "candidate_results": [{"candidate_id": k, "status": v} for k, v in candidate_status.items()],
        "governance": {
            "historical_pit_validated": False,
            "performance_authorized": False,
            "promotion_authorized": False,
            "live_execution": False,
        },
        "scientific_boundary": BOUNDARY,
        "safety": SAFETY,
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    result["receipt_fingerprint"] = hashlib.sha256(canonical).hexdigest()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "candidate_results": result["candidate_results"],
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
