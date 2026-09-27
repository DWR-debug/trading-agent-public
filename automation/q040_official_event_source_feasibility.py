"""Q040 fixed official-source access and PIT feasibility probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

PROBES = (
    ("SEC", "https://data.sec.gov/submissions/CIK0000320193.json", ("acceptanceDateTime", "filings")),
    ("BLS", "https://www.bls.gov/schedule/news_release/empsit.htm", ("Release Date", "Release Time", "08:30")),
    ("BEA", "https://www.bea.gov/news/schedule/", ("Release", "8:30", "2026")),
    ("CFTC", "https://publicreporting.cftc.gov/stories/s/r4w3-av2u", ("Report_Date_as_YYYY_MM_DD", "Public Reporting Environment")),
    ("TREASURY", "https://www.treasurydirect.gov/auctions/announcements-data-results/announcement-results-press-releases/previous-announcements-and-results/", ("Previous Announcements and Results", "1998")),
)

PIT_CLASS = {
    "SEC": "ACCEPTANCE_BOUND_PENDING_PUBLIC_AVAILABILITY_GAP",
    "BLS": "SCHEDULE_ONLY",
    "BEA": "SCHEDULE_ONLY",
    "CFTC": "SCHEDULE_ONLY_UNLESS_HISTORICAL_RELEASE_TIME_REPRODUCED",
    "TREASURY": "SOURCE_ACCESSIBLE_TIMESTAMP_FEASIBILITY_REQUIRES_Q023_Q024_CHAIN",
}

def _fingerprint(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _probe(source: str, url: str, markers: tuple[str, ...]) -> dict:
    started = time.monotonic()
    headers = {"User-Agent": "trading-agent-research/1.0", "Accept": "application/json,text/html;q=0.9,*/*;q=0.5"}
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read(2_000_000)
            text = payload.decode("utf-8", "replace")
            return {
                "source": source,
                "url": url,
                "http_status": response.getcode(),
                "content_type": response.headers.get("Content-Type"),
                "bytes_read": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "markers": {marker: marker in text for marker in markers},
                "access_status": "ACCESSIBLE",
                "error": None,
                "pit_status": PIT_CLASS[source],
            }
    except urllib.error.HTTPError as exc:
        return {
            "source": source,
            "url": url,
            "http_status": exc.code,
            "content_type": None,
            "bytes_read": 0,
            "sha256": None,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "markers": {marker: False for marker in markers},
            "access_status": "HTTP_ERROR",
            "error": f"HTTP {exc.code}: {exc.reason}",
            "pit_status": PIT_CLASS[source],
        }
    except (urllib.error.URLError, TimeoutError) as exc:
        return {
            "source": source,
            "url": url,
            "http_status": None,
            "content_type": None,
            "bytes_read": 0,
            "sha256": None,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "markers": {marker: False for marker in markers},
            "access_status": "NETWORK_ERROR",
            "error": str(exc),
            "pit_status": PIT_CLASS[source],
        }

def run(output: Path) -> dict:
    results = [_probe(*probe) for probe in PROBES]
    result = {
        "schema_version": "1.0",
        "trial_id": "T-2026-09-27-062",
        "status": "COMPLETED_SOURCE_FEASIBILITY",
        "fixed_probe_count_per_source": 1,
        "results": results,
        "performance_evaluation": False,
        "oos_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "governance": {
            "performance_trial_authorized": False,
            "automatic_promotion": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "family_search": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["result_fingerprint"] = _fingerprint(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print("Q040_STATUS:", result["status"])
    for row in results:
        print(row["source"], row["access_status"], row["pit_status"])
    print("Q040_FINGERPRINT:", result["result_fingerprint"])
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(Path(args.output))
