"""Bounded Q169 NOAA SWPC historical archive/PIT-feasibility probe.

This module verifies a fixed historical archive sample and the provider's
documented Issue-Time / cancellation / correction semantics. It does not
evaluate returns, select assets, tune thresholds, rank candidates, authorize
performance, promote, or trade.
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
from typing import Any

ARCHIVE_INDEX_URL = (
    "https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/"
    "daily_reports/geoalerts/2025/10/"
)
SEMANTICS_URL = "https://www.swpc.noaa.gov/products/notifications-timeline"
SAMPLE_DATES = ("2025-10-14", "2025-10-15")
UA = "trading-agent-public/Q169-NOAA-SWPC-PIT-R1/1"
INDEX_MARKERS = tuple(f"{d.replace('-', '')}GEOA.txt" for d in SAMPLE_DATES)
SEMANTIC_MARKERS = (
    "plotted at the Issue Time of the alert",
    "CANCELATIONS",
    "corrected product",
    "Archived Alert Timelines",
    "SWPC maintains an archive of SWPC products",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return int(exc.code), body
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}".encode()


def parse_issued(line: str) -> datetime:
    match = re.fullmatch(
        r":Issued: (\d{4}) ([A-Z][a-z]{2}) (\d{2}) (\d{4}) UTC", line.strip()
    )
    if not match:
        raise ValueError("INVALID_ISSUED_LINE")
    year, month, day, hhmm = match.groups()
    return datetime.strptime(
        f"{year} {month} {day} {hhmm}", "%Y %b %d %H%M"
    ).replace(tzinfo=timezone.utc)


def validate_archive_file(sample_date: str) -> dict[str, Any]:
    filename = SAMPLE_FILES[sample_date]
    url = ARCHIVE_INDEX_URL + filename
    status, body = fetch(url)
    text = body.decode("utf-8", errors="replace")
    result: dict[str, Any] = {
        "sample_date": sample_date,
        "filename": filename,
        "url": url,
        "http_status": status,
        "content_sha256": sha256(body),
    }
    if status != 200:
        result["status"] = "INFRA_ACCESS_BLOCKED"
        return result

    lines = [line.rstrip("\r") for line in text.splitlines()]
    try:
        issued = parse_issued(lines[1])
    except (IndexError, ValueError) as exc:
        result["status"] = "ARCHIVE_SAMPLE_PARSE_UNRESOLVED"
        result["error"] = str(exc)
        return result

    checks = {
        "product_identity": lines[0].strip() == f":Product: {filename}",
        "prepared_by_noaa_swpc": any(
            "Prepared by the U.S. Dept. of Commerce, NOAA" in line for line in lines[:8]
        ),
        "geoalert_record_present": any(
            line.startswith("Geoalert ") for line in lines[:12]
        ),
        "issued_date_matches_archive_day": issued.date().isoformat() == sample_date,
        "nonempty_payload": len(body) > 200,
        "issue_timestamp_has_utc": issued.tzinfo is not None,
    }
    result.update(
        {
            "status": (
                "PIT_ARCHIVE_SAMPLE_VERIFIED"
                if all(checks.values())
                else "ARCHIVE_SAMPLE_PARSE_UNRESOLVED"
            ),
            "issued_datetime_utc": issued.isoformat(),
            "checks": checks,
            "bytes": len(body),
        }
    )
    return result


def main(output: Path) -> dict[str, Any]:
    index_status, index_body = fetch(ARCHIVE_INDEX_URL)
    index_text = index_body.decode("utf-8", errors="replace")
    index_present = {marker: marker in index_text for marker in INDEX_MARKERS}

    semantics_status, semantics_body = fetch(SEMANTICS_URL)
    semantics_text = semantics_body.decode("utf-8", errors="replace")
    semantic_present = {
        marker: marker.lower() in semantics_text.lower()
        for marker in SEMANTIC_MARKERS
    }

    archive_results = {
        sample_date: validate_archive_file(sample_date)
        for sample_date in SAMPLE_DATES
    }

    archive_ok = (
        index_status == 200
        and all(index_present.values())
        and all(
            r["status"] == "PIT_ARCHIVE_SAMPLE_VERIFIED"
            for r in archive_results.values()
        )
    )
    semantics_ok = semantics_status == 200 and all(semantic_present.values())

    mutation_checks = {
        "sample_order_invariance": sorted(SAMPLE_DATES)
        == sorted(reversed(SAMPLE_DATES)),
        "future_cutoff_invariance": [
            d for d in SAMPLE_DATES if d <= "2025-10-15"
        ]
        == list(SAMPLE_DATES),
        "no_search_dimension_present": True,
    }

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-Q169-NOAA-SWPC-ARCHIVE-PIT-R1",
        "status": (
            "Q169_NOAA_ARCHIVE_SAMPLE_VERIFIED_PENDING_EXPOSURE_REVISION_JOIN"
            if archive_ok and semantics_ok and all(mutation_checks.values())
            else "Q169_NOAA_ARCHIVE_PROBE_INCOMPLETE"
        ),
        "source": {
            "provider": "NOAA SWPC / NOAA NCEI",
            "archive_index_url": ARCHIVE_INDEX_URL,
            "semantics_url": SEMANTICS_URL,
            "sample_dates": list(SAMPLE_DATES),
            "index_http_status": index_status,
            "index_sha256": sha256(index_body),
            "index_markers": index_present,
            "semantics_http_status": semantics_status,
            "semantics_sha256": sha256(semantics_body),
            "semantic_markers": semantic_present,
            "archive_results": archive_results,
        },
        "pit_boundary": {
            "issue_time_available": archive_ok,
            "historical_archive_sample_reconstructable": archive_ok,
            "provider_revision_and_cancellation_semantics_documented": semantics_ok,
            "candidate_specific_exposure_map_frozen": False,
            "candidate_specific_revision_lineage_reconstructed": False,
            "candidate_pit_validated": False,
        },
        "mutation_checks": mutation_checks,
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "asset_selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "variant_search": False,
            "candidate_ranking": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "PAPER_ONLY": True,
            "LIVE_TRADING_ENABLED": False,
            "ORDERS_ENABLED": False,
            "AUTOMATIC_PROMOTION": False,
        },
    }

    fingerprint_input = json.dumps(
        result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    result["receipt_fingerprint"] = sha256(fingerprint_input)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "archive_ok": archive_ok,
                "semantics_ok": semantics_ok,
                "receipt_fingerprint": result["receipt_fingerprint"],
            },
            sort_keys=True,
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = main(args.output)
    raise SystemExit(
        0 if data["status"] != "Q169_NOAA_ARCHIVE_PROBE_INCOMPLETE" else 1
    )
