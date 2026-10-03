"""Q171-Q177 conservative PIT-readiness audit.

This module does not evaluate returns, select assets, tune parameters, or rank
candidates. It only verifies source-specific timestamp/revision prerequisites
and classifies what remains to be proven before a formal PIT receipt exists.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path


UA = "trading-agent-public/Q171-Q177-PIT-readiness/1"


def fetch(url: str, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    req_headers = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return int(getattr(response, "status", 200)), response.read()
    except Exception as exc:
        code = getattr(exc, "code", 599)
        try:
            body = exc.read()
        except Exception:
            body = f"FETCH_ERROR:{type(exc).__name__}:{exc}".encode()
        return int(code), body


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def common_crawl_sample() -> dict[str, object]:
    fixed_url = "commoncrawl.org/get-started"
    index_url = (
        "https://index.commoncrawl.org/CC-MAIN-2025-43-index?"
        + urllib.parse.urlencode(
            {
                "url": fixed_url,
                "output": "json",
                "filter": "status:200",
                "collapse": "digest",
                "limit": "3",
            }
        )
    )
    status, body = fetch(index_url)
    if status != 200:
        return {"status": "BLOCKED_INDEX_FETCH", "http_status": status, "index_sha256": digest(body)}

    rows = []
    for line in body.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            return {"status": "BLOCKED_INDEX_PARSE", "http_status": status, "index_sha256": digest(body)}

    required = {"timestamp", "digest", "filename", "offset", "length"}
    if not rows or not all(required.issubset(row) for row in rows):
        return {
            "status": "BLOCKED_INDEX_SCHEMA",
            "http_status": status,
            "rows": len(rows),
            "index_sha256": digest(body),
        }

    timestamps = [str(row["timestamp"]) for row in rows]
    monotonic = timestamps == sorted(timestamps)
    unique = len(timestamps) == len(set(timestamps))
    first = rows[0]
    try:
        offset = int(first["offset"])
        length = int(first["length"])
    except (TypeError, ValueError):
        return {"status": "BLOCKED_RANGE_METADATA", "rows": len(rows), "index_sha256": digest(body)}

    if offset < 0 or length <= 0 or length > 20_000_000:
        return {"status": "BLOCKED_RANGE_METADATA", "offset": offset, "length": length}

    range_url = "https://data.commoncrawl.org/" + str(first["filename"])
    range_headers = {"Range": f"bytes={offset}-{offset + length - 1}"}
    rstatus, record = fetch(range_url, range_headers)
    if rstatus != 206 or len(record) != length:
        return {
            "status": "BLOCKED_WARC_RANGE_FETCH",
            "index_sha256": digest(body),
            "warc_http_status": rstatus,
            "warc_bytes": len(record),
            "expected_warc_bytes": length,
        }
    try:
        decompressed = gzip.decompress(record)
    except (OSError, EOFError):
        return {
            "status": "BLOCKED_WARC_GZIP",
            "index_sha256": digest(body),
            "warc_http_status": rstatus,
            "warc_sha256": digest(record),
        }

    header_blob = decompressed.split(b"\r\n\r\n", 1)[0]
    header_text = header_blob.decode("utf-8", errors="replace")
    required_headers = ["WARC/1.0", "WARC-Date:", "WARC-Target-URI:"]
    if not all(marker in header_text for marker in required_headers):
        return {
            "status": "BLOCKED_WARC_SCHEMA",
            "index_sha256": digest(body),
            "warc_sha256": digest(record),
        }

    return {
        "status": "PIT_SAMPLE_RECONSTRUCTABLE",
        "fixed_url": fixed_url,
        "crawl": "CC-MAIN-2025-43",
        "rows": len(rows),
        "timestamps_monotonic": monotonic,
        "timestamps_unique": unique,
        "capture_timestamp": first["timestamp"],
        "capture_digest": first["digest"],
        "warc_http_status": rstatus,
        "warc_sha256": digest(record),
        "index_sha256": digest(body),
        "notes": "This proves historical capture addressing for one fixed URL; an issuer URL map and candidate-specific state compiler remain required.",
    }


def text_probe(url: str, markers: list[str], block_status: str, ok_status: str) -> dict[str, object]:
    status, body = fetch(url)
    text = body.decode("utf-8", errors="replace")
    missing = [m for m in markers if m.lower() not in text.lower()]
    return {
        "http_status": status,
        "markers_present": not missing and status == 200,
        "missing_markers": missing,
        "content_sha256": digest(body),
        "status": ok_status if status == 200 and not missing else block_status,
    }


def run(output: Path) -> dict[str, object]:
    results = {
        "Q171": common_crawl_sample(),
        "Q174": text_probe(
            "https://erddap.gml.noaa.gov/erddap/rest.html",
            ["RESTful web service", ".json"],
            "PIT_UNRESOLVED_DATASET_VINTAGE",
            "SOURCE_CLOCK_ACCESS_CONFIRMED",
        ),
        "Q175": text_probe(
            "https://earthquake.usgs.gov/data/catalog/products.php",
            ["Update time", "supersedes", "version"],
            "PIT_VERSION_CONTRACT_UNRESOLVED",
            "VERSIONED_PRODUCT_SEMANTICS_CONFIRMED",
        ),
        "Q176": text_probe(
            "https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/",
            ["from-created-date", "from-update-date", "from-index-date"],
            "PIT_RECORD_VINTAGE_UNRESOLVED",
            "MULTIPLE_DEPOSIT_CLOCKS_CONFIRMED",
        ),
        "Q177": text_probe(
            "https://www.swpc.noaa.gov/products/notifications-timeline",
            ["Issue Time", "CANCELATIONS", "Archived Alert Timelines"],
            "PIT_ARCHIVE_RETRIEVAL_UNRESOLVED",
            "ARCHIVE_AND_REVISION_SEMANTICS_CONFIRMED",
        ),
    }
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-Q171-Q177-PIT-READINESS",
        "status": "PIT_READINESS_COMPLETED_NO_PERFORMANCE",
        "results": results,
        "scientific_boundary": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
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
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/runs/deep_frontier/q171_q177_pit_readiness.json"),
    )
    args = parser.parse_args()
    result = run(args.output)
    return 0 if result["status"] == "PIT_READINESS_COMPLETED_NO_PERFORMANCE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
