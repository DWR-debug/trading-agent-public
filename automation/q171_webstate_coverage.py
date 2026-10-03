"""Conservative Q171 Common Crawl coverage probe for a frozen issuer URL map.

This is a source/PIT-feasibility check only. It does not inspect returns,
label events, choose outcomes, rank issuers, or tune any parameter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path


UA = "trading-agent-public/Q171-webstate-coverage/1"
CRAWLS = ("CC-MAIN-2025-13", "CC-MAIN-2025-26", "CC-MAIN-2025-38", "CC-MAIN-2025-51")
REQUEST_GAP_SECONDS = 3
MAP_PATH = Path("research/governance/q171_issuer_web_url_map_2026_10_03.json")


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json,text/plain,*/*",
        },
    )
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



def fetch_with_fixed_retries(url: str, attempts: int = 3) -> tuple[int, bytes, int]:
    import time
    last_status = 599
    last_body = b''
    for attempt in range(1, attempts + 1):
        last_status, last_body = fetch(url)
        if last_status < 500 or attempt == attempts:
            return last_status, last_body, attempt
        time.sleep(2 ** (attempt - 1))
    return last_status, last_body, attempts

def query_index(crawl: str, url: str) -> dict[str, object]:
    import time
    endpoint = (
        f"https://index.commoncrawl.org/{crawl}-index?"
        + urllib.parse.urlencode(
            {
                "url": url,
                "matchType": "exact",
                "output": "json",
                "filter": "status:200",
                "collapse": "digest",
                "limit": "20",
            }
        )
    )
    status, body, attempts = fetch_with_fixed_retries(endpoint, attempts=3)
    time.sleep(REQUEST_GAP_SECONDS)
    if status != 200:
        return {
            "status": "BLOCKED_INDEX_FETCH",
            "http_status": status,
            "attempts": attempts,
            "error_body_excerpt": body.decode("utf-8", errors="replace")[:500],
            "index_sha256": hashlib.sha256(body).hexdigest(),
        }

    rows: list[dict[str, object]] = []
    malformed = 0
    for line in body.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if isinstance(row, dict):
            rows.append(row)

    timestamps = sorted({str(row["timestamp"]) for row in rows if row.get("timestamp")})
    fields_ok = all(
        {"timestamp", "digest", "filename", "offset", "length"}.issubset(row)
        for row in rows
    )
    if rows and not fields_ok:
        return {
            "status": "BLOCKED_INDEX_SCHEMA",
            "rows": len(rows),
            "malformed_lines": malformed,
            "index_sha256": hashlib.sha256(body).hexdigest(),
        }

    return {
        "status": "CAPTURE_FOUND" if rows else "NO_CAPTURE_FOUND",
        "crawl": crawl,
        "attempts": attempts,
        "requested_url": url,
        "rows": len(rows),
        "malformed_lines": malformed,
        "unique_capture_timestamps": timestamps,
        "first_capture_timestamp": timestamps[0] if timestamps else None,
        "last_capture_timestamp": timestamps[-1] if timestamps else None,
        "capture_rows": [
            {
                "timestamp": str(row["timestamp"]),
                "digest": str(row["digest"]),
                "filename": str(row["filename"]),
                "offset": int(row["offset"]),
                "length": int(row["length"]),
                "status": str(row.get("status", "")),
                "mime": str(row.get("mime", "")),
                "indexed_url": str(row.get("url", "")),
            }
            for row in rows
        ],
        "index_sha256": hashlib.sha256(body).hexdigest(),
    }


def run(output: Path) -> dict[str, object]:
    mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    symbols = mapping["symbols"]
    expected = ["SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN"]
    actual = [item["symbol"] for item in symbols]
    if actual != expected:
        raise RuntimeError(f"Q171 frozen universe mismatch: {actual!r}")

    results: dict[str, dict[str, object]] = {}
    status_counts: dict[str, int] = {}
    total_captures = 0
    for item in symbols:
        symbol = item["symbol"]
        per_crawl: dict[str, dict[str, object]] = {}
        aggregate_rows: list[dict[str, object]] = []
        for crawl in CRAWLS:
            result = query_index(crawl, item["canonical_public_url"])
            per_crawl[crawl] = result
            aggregate_rows.extend(result.get("capture_rows", []))
            status = str(result["status"])
            status_counts[status] = status_counts.get(status, 0) + 1
        aggregate_rows.sort(key=lambda row: (
            str(row["timestamp"]),
            str(row["crawl"]),
            str(row["digest"]),
            int(row["offset"]),
            int(row["length"]),
        ))
        if aggregate_rows:
            results[symbol] = {
                "status": "CAPTURE_FOUND",
                "crawl_results": per_crawl,
                "capture_count": len(aggregate_rows),
                "capture_rows": aggregate_rows,
            }
            total_captures += len(aggregate_rows)
        else:
            results[symbol] = {
                "status": "NO_CAPTURE_FOUND",
                "crawl_results": per_crawl,
                "capture_count": 0,
                "capture_rows": [],
            }

    payload = {
        "schema_version": "1.1",
        "task_id": "Q-2026-10-03-Q171-WEBSTATE-COVERAGE",
        "status": "Q171_WEBSTATE_SOURCE_COVERAGE_COMPLETED",
        "crawls": list(CRAWLS),
        "url_map_path": str(MAP_PATH),
        "url_map_fingerprint": digest(mapping),
        "results": results,
        "summary": {
            "issuers": len(results),
            "fixed_crawls": len(CRAWLS),
            "status_counts": status_counts,
            "issuers_with_any_capture": sum(1 for result in results.values() if result["status"] == "CAPTURE_FOUND"),
            "captures_found": total_captures,
            "infra_blocked": sum(
                1
                for result in results.values()
                for crawl_result in result["crawl_results"].values()
                if crawl_result["status"] == "BLOCKED_INDEX_FETCH"
            ),
        },
        "scientific_boundary": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
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
    payload["receipt_fingerprint"] = digest(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/runs/deep_frontier/q171_webstate_coverage.json"),
    )
    args = parser.parse_args()
    result = run(args.output)
    return 0 if result["status"] == "Q171_WEBSTATE_SOURCE_COVERAGE_COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
