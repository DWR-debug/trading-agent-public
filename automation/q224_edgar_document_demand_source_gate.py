from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

UA = "TradingAgent-Public-Q224-Source-Gate/1.0"
CONTROLS = {
    "2020-05-19": "https://www.sec.gov/dera/data/Public-EDGAR-log-file-data/2020/Qtr2/log20200519.zip",
    "2022-12-30": "https://www.sec.gov/dera/data/Public-EDGAR-log-file-data/2022/Qtr4/log20221230.zip",
    "2025-06-30": "https://www.sec.gov/dera/data/Public-EDGAR-log-file-data/2025/Qtr2/log20250630.zip",
}
URI_RE = re.compile(r"/Archives/edgar/data/(\d+)/(\d{18})(?:/|$)", re.I)
EXPECTED = {"_time", "uri_path"}


def fetch(url: str, *, range_header: str | None = None) -> bytes:
    headers = {
        "User-Agent": UA,
        "Accept": "application/zip,application/octet-stream,*/*",
    }
    if range_header:
        headers["Range"] = range_header
    req = Request(url, headers=headers)
    with urlopen(req, timeout=90) as resp:
        return resp.read()


def inspect_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        members = [n for n in zf.namelist() if not n.endswith("/")]
        if not members:
            raise ValueError("ZIP contains no files")
        csv_members = [n for n in members if n.lower().endswith(".csv")]
        if not csv_members:
            raise ValueError("ZIP contains no CSV member")
        target = csv_members[0]
        with zf.open(target, "r") as raw:
            wrapper = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
            reader = csv.reader(wrapper)
            header = next(reader)
            first_rows = []
            uri_matches = 0
            rows_seen = 0
            for row in reader:
                if len(first_rows) < 25:
                    first_rows.append(row)
                rows_seen += 1
                if len(row) == len(header):
                    rec = dict(zip(header, row))
                    uri = rec.get("uri_path", "")
                    if URI_RE.search(uri):
                        uri_matches += 1
                if rows_seen >= 250:
                    break
    cols = {c.strip() for c in header}
    return {
        "member": target,
        "member_count": len(members),
        "header": header,
        "expected_columns_present": EXPECTED.issubset(cols),
        "traffic_quality_columns_present": sorted(cols.intersection({"ip", "crawler", "browser", "find", "code", "noagent", "norefer"})),
        "traffic_quality_fields_absent_in_modern_schema": not bool(cols.intersection({"ip", "crawler", "browser", "find", "code", "noagent", "norefer"})),
        "sample_rows_read": rows_seen,
        "sample_uri_regex_matches": uri_matches,
        "sample_uri_match_rate": (uri_matches / rows_seen) if rows_seen else 0.0,
        "first_rows_sha256": hashlib.sha256(json.dumps(first_rows, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ns = ap.parse_args()
    results = []
    for label, url in CONTROLS.items():
        rec = {
            "control_date": label,
            "url": url,
            "reachable": False,
            "http_status": None,
            "content_length": None,
            "content_type": None,
            "accept_ranges": None,
            "etag": None,
            "sha256": None,
            "zip_valid": False,
            "schema": None,
            "error": None,
        }
        try:
            req = Request(url, method="HEAD", headers={"User-Agent": UA, "Accept": "*/*"})
            with urlopen(req, timeout=30) as resp:
                rec.update(
                    reachable=True,
                    http_status=getattr(resp, "status", 200),
                    content_length=resp.headers.get("Content-Length"),
                    content_type=resp.headers.get("Content-Type"),
                    accept_ranges=resp.headers.get("Accept-Ranges"),
                    etag=resp.headers.get("ETag"),
                )
            with tempfile.TemporaryDirectory() as td:
                p = Path(td) / Path(url).name
                body = fetch(url)
                p.write_bytes(body)
                rec["sha256"] = hashlib.sha256(body).hexdigest()
                rec["download_bytes"] = len(body)
                rec["zip_valid"] = zipfile.is_zipfile(p)
                if rec["zip_valid"]:
                    rec["schema"] = inspect_zip(p)
        except (HTTPError, URLError, OSError, ValueError, zipfile.BadZipFile, TimeoutError) as exc:
            rec["error"] = f"{type(exc).__name__}:{exc}"
        results.append(rec)

    successful = [r for r in results if r["zip_valid"]]
    payload = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-06-Q224-EDGAR-MODERN-WINDOW-SOURCE-GATE",
        "status": "SOURCE_ARCHIVE_INTEGRITY_COMPLETED_NO_PERFORMANCE" if successful else "SOURCE_ARCHIVE_GATE_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "Q224",
        "source_contract": {
            "official_dataset": "SEC EDGAR Log File Data Sets",
            "modern_window": "2020-05-19 through 2025-06-30",
            "historical_gap_excluded": True,
            "legacy_modern_splice_attempted": False,
            "fixed_controls": list(CONTROLS.keys()),
        },
        "results": results,
        "request_quality": {
            "modern_schema_has_request_time_and_uri": all(
                bool(r.get("schema", {}).get("expected_columns_present")) for r in successful
            ),
            "modern_schema_exposes_legacy_crawler_fields": False,
            "traffic_contamination_fully_resolvable_from_modern_schema": False,
            "policy": "Do not infer latent investor identity or sophistication; contamination remains an explicit unresolved limitation.",
        },
        "pit_contract": {
            "request_time_field": "_time",
            "filing_identity_recovery": "Deterministic CIK/accession recovery from uri_path is required.",
            "same_session_use": False,
            "filing_public_boundary_join_completed": False,
        },
        "scientific_boundary": {
            "performance_authorized": False,
            "holdout_selection_allowed": False,
            "ranking_allowed": False,
            "tuning_allowed": False,
            "promotion_allowed": False,
            "live_execution_allowed": False,
        },
        "next_gate": "request-quality-contamination-bounds + filing-acceptance/public-boundary join + mutation/PIT checks + independent reproduction",
        "negative_evidence": {
            "continuous_2003_2025_panel": False,
            "2017_07_01_to_2020_05_18_available": False,
            "legacy_modern_schema_splice_allowed": False,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["receipt_fingerprint"] = hashlib.sha256(canonical.encode()).hexdigest()
    out = Path(ns.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "successful_controls": len(successful),
        "receipt_fingerprint": payload["receipt_fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
