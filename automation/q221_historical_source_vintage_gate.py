"""Audit archived USAspending public-clock documentation vintages for Q221.

This is a bounded source-history test, not proof of an award's first public
observation time. It uses the Internet Archive CDX index to retrieve
timestamped captures of the official USAspending About-the-Data PDF, preserves
content fingerprints, and checks whether the documented clock/exceptions stayed
consistent across fixed sample boundaries. All downstream event-level PIT,
transaction applicability, entity mapping, and performance gates remain closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ORIGINAL_URL = "https://www.usaspending.gov/data/about-the-data-download.pdf"
CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"
CAPTURE_BASE = "https://web.archive.org/web"
TARGETS = (
    ("2025-01-01", "20250101000000"),
    ("2025-07-01", "20250701000000"),
    ("2026-01-01", "20260101000000"),
    ("2026-07-01", "20260701000000"),
    ("2026-10-05", "20261005000000"),
)
MAX_CAPTURE_AGE_DAYS = 180
MAX_CDX_BYTES = 5_000_000
MAX_PDF_BYTES = 25_000_000

MARKERS = {
    "within_five_days": "WITHIN FIVE DAYS",
    "three_business_days": "THREE BUSINESS DAYS",
    "following_morning": "FOLLOWING MORNING",
    "website_day_after": "DAY AFTER THAT",
    "dod_usace_90_day_exception": "90 DAYS",
    "far_30_day_exception": "WITHIN 30 DAYS",
}


def fetch(url: str, limit: int) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TradingAgent-Public-Q221-Historical-Clock/1.0"},
    )
    with urllib.request.urlopen(request, timeout=35) as response:
        body = response.read(limit + 1)
        if len(body) > limit:
            raise ValueError(f"response exceeded bounded byte limit ({limit})")
        return int(getattr(response, "status", 200)), response.headers.get("Content-Type", ""), body


def extract_pdf_text(body: bytes) -> str:
    from pypdf import PdfReader
    import io

    return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(body)).pages)


def _timestamp_to_datetime(value: str) -> datetime | None:
    if len(value) < 8 or not value[:8].isdigit():
        return None
    try:
        return datetime.strptime(value[:14].ljust(14, "0"), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _cdx_url() -> str:
    query = urllib.parse.urlencode({
        "url": ORIGINAL_URL,
        "output": "json",
        "from": "2024",
        "to": "2026",
        "filter": ["statuscode:200", "mimetype:application/pdf"],
        "fl": "timestamp,original,mimetype,statuscode,digest,length",
        "limit": "1000",
        "gzip": "false",
    }, doseq=True)
    return CDX_ENDPOINT + "?" + query


def parse_cdx(body: bytes) -> list[dict[str, str]]:
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, list) or not payload:
        return []
    header = payload[0]
    if not isinstance(header, list) or not all(isinstance(x, str) for x in header):
        return []
    rows = []
    for row in payload[1:]:
        if not isinstance(row, list) or len(row) != len(header):
            continue
        entry = {header[i]: str(row[i]) for i in range(len(header))}
        ts = entry.get("timestamp", "")
        if (
            len(ts) == 14 and ts.isdigit()
            and entry.get("statuscode") == "200"
            and entry.get("original", "").rstrip("/") == ORIGINAL_URL.rstrip("/")
        ):
            rows.append(entry)
    return sorted(rows, key=lambda x: x["timestamp"])


def run(output: Path) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q221_historical_source_vintage_gate",
        "candidate_id": "Q221",
        "generated_at_utc": started,
        "official_source_url": ORIGINAL_URL,
        "archive_index_url": CDX_ENDPOINT,
        "fixed_target_windows": [x[0] for x in TARGETS],
        "max_capture_age_days": MAX_CAPTURE_AGE_DAYS,
        "marker_contract": MARKERS,
        "capture_rows": [],
        "all_target_windows_covered": False,
        "policy_markers_consistent_across_vintages": False,
        "historical_policy_vintages_reconstructed": False,
        "historical_applicability_proven": False,
        "award_level_public_boundary_proven": False,
        "transaction_semantics_frozen": False,
        "agency_exceptions_classified": False,
        "recipient_to_issuer_mapping_frozen": False,
        "lookahead_used": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    }

    try:
        code, content_type, body = fetch(_cdx_url(), MAX_CDX_BYTES)
        receipt["cdx_status"] = code
        receipt["cdx_content_type"] = content_type
        receipt["cdx_sha256"] = hashlib.sha256(body).hexdigest()
        captures = parse_cdx(body)
    except Exception as exc:
        receipt.update({
            "status": "Q221_CDX_ARCHIVE_INDEX_UNAVAILABLE",
            "error": f"{type(exc).__name__}: {exc}"[:700],
            "next_gate": "retry the bounded source-history lookup only after diagnosing archive transport; do not infer historical clock readiness",
        })
        _write(output, receipt)
        return receipt

    receipt["cdx_capture_count"] = len(captures)
    selected = []
    for target_label, target_value in TARGETS:
        target_dt = _timestamp_to_datetime(target_value)
        possible = []
        for capture in captures:
            stamp = capture.get("timestamp", "")
            capture_dt = _timestamp_to_datetime(stamp)
            if capture_dt and target_dt and capture_dt <= target_dt:
                age = (target_dt - capture_dt).days
                if age <= MAX_CAPTURE_AGE_DAYS:
                    possible.append((capture_dt, age, capture))
        if not possible:
            receipt["capture_rows"].append({
                "target_window": target_label,
                "status": "NO_CAPTURE_WITHIN_BOUND",
                "max_capture_age_days": MAX_CAPTURE_AGE_DAYS,
                "marker_results": {},
            })
            continue
        capture_dt, age, capture = max(possible, key=lambda row: row[0])
        timestamp = capture["timestamp"]
        replay_url = f"{CAPTURE_BASE}/{timestamp}id_/{ORIGINAL_URL}"
        row: dict[str, Any] = {
            "target_window": target_label,
            "capture_timestamp_utc": capture_dt.isoformat(),
            "capture_age_days": age,
            "archive_digest": capture.get("digest"),
            "archive_length": capture.get("length"),
            "archive_original_url": capture.get("original"),
            "replay_url": replay_url,
            "status": "CAPTURE_SELECTED",
            "marker_results": {},
        }
        try:
            status, mime, pdf = fetch(replay_url, MAX_PDF_BYTES)
            text = " ".join(extract_pdf_text(pdf).upper().split())
            marker_results = {name: token in text for name, token in MARKERS.items()}
            row.update({
                "http_status": status,
                "content_type": mime,
                "content_bytes": len(pdf),
                "content_sha256": hashlib.sha256(pdf).hexdigest(),
                "marker_results": marker_results,
                "required_marker_count": sum(marker_results.values()),
                "required_marker_total": len(MARKERS),
                "status": "CAPTURE_PARSED",
            })
        except Exception as exc:
            row.update({
                "status": "CAPTURE_FETCH_OR_PARSE_FAILED",
                "error": f"{type(exc).__name__}: {exc}"[:500],
            })
        selected.append(row)
        receipt["capture_rows"].append(row)

    parsed = [x for x in selected if x.get("status") == "CAPTURE_PARSED"]
    all_windows = (
        len(receipt["capture_rows"]) == len(TARGETS)
        and all(x.get("status") == "CAPTURE_PARSED" for x in receipt["capture_rows"])
    )
    marker_sets = {
        tuple(sorted((k, bool(v)) for k, v in x.get("marker_results", {}).items()))
        for x in parsed
    }
    markers_consistent = (
        bool(parsed)
        and len(marker_sets) == 1
        and all(all(x.get("marker_results", {}).values()) and len(x.get("marker_results", {})) == len(MARKERS) for x in parsed)
    )
    timestamps = sorted({x.get("capture_timestamp_utc") for x in parsed if x.get("capture_timestamp_utc")})
    years = {value[:4] for value in timestamps}
    vintage_ok = all_windows and markers_consistent and {"2025", "2026"}.issubset(years)

    receipt.update({
        "unique_parsed_capture_count": len({x.get("content_sha256") for x in parsed if x.get("content_sha256")}),
        "captured_vintage_years": sorted(years),
        "all_target_windows_covered": all_windows,
        "policy_markers_consistent_across_vintages": markers_consistent,
        "historical_policy_vintages_reconstructed": vintage_ok,
        "status": (
            "Q221_HISTORICAL_POLICY_VINTAGES_RECONSTRUCTED"
            if vintage_ok else "Q221_HISTORICAL_POLICY_VINTAGE_COVERAGE_INCOMPLETE_OR_SEMANTICS_DRIFT"
        ),
        "next_gate": (
            "reconstruct event-level public-observation boundary, confirm exact transaction-class applicability, freeze agency exceptions and recipient-to-issuer mapping"
            if vintage_ok else
            "obtain bounded historical captures for missing target windows and inspect the clock/exceptions for semantic drift"
        ),
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    })
    _write(output, receipt)
    return receipt


def _write(path: Path, receipt: dict[str, Any]) -> None:
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    receipt["receipt_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
