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
CRAWL = "CC-MAIN-2025-43"
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


def query_index(url: str) -> dict[str, object]:
    endpoint = (
        f"https://index.commoncrawl.org/{CRAWL}-index?"
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
    status, body = fetch(endpoint)
    if status != 200:
        return {
            "status": "BLOCKED_INDEX_FETCH",
            "http_status": status,
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
        "crawl": CRAWL,
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

    results = {item["symbol"]: query_index(item["canonical_public_url"]) for item in symbols}
    status_counts: dict[str, int] = {}
    for result in results.values():
        status = str(result["status"])
        status_counts[status] = status_counts.get(status, 0) + 1

    payload = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-Q171-WEBSTATE-COVERAGE",
        "status": "Q171_WEBSTATE_SOURCE_COVERAGE_COMPLETED",
        "crawl": CRAWL,
        "url_map_path": str(MAP_PATH),
        "url_map_fingerprint": digest(mapping),
        "results": results,
        "summary": {
            "issuers": len(results),
            "status_counts": status_counts,
            "captures_found": status_counts.get("CAPTURE_FOUND", 0),
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
