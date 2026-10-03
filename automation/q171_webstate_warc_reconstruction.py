"""Q171 WARC reconstruction gate for captures already returned by the frozen URL probe.

No returns, outcomes, rankings, asset selection, parameter tuning, or live
execution are performed here. The gate only verifies that an indexed capture
can be retrieved and that its WARC metadata/payload digest is internally
consistent.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


UA = "trading-agent-public/Q171-WARC-reconstruction/1"
REQUEST_GAP_SECONDS = 5


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_range(url: str, start: int, length: int) -> tuple[int, bytes]:
    end = start + length - 1
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "*/*",
            "Range": f"bytes={start}-{end}",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return int(getattr(response, "status", 200)), response.read()


def parse_headers(blob: bytes) -> dict[str, str]:
    lines = blob.decode("utf-8", errors="replace").split("\r\n")
    out: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def header_value(headers: dict[str, str], name: str) -> str | None:
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return None


def parse_positive_content_length(headers: dict[str, str], name: str) -> int | None:
    raw = header_value(headers, name)
    if raw is None:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"INVALID_{name.upper().replace('-', '_')}") from exc
    if value < 0:
        raise ValueError(f"NEGATIVE_{name.upper().replace('-', '_')}")
    return value

def reconstruct(symbol: str, item: dict[str, object]) -> dict[str, object]:
    rows = item.get("capture_rows") or []
    if not rows:
        return {"symbol": symbol, "status": "NO_CAPTURE_TO_RECONSTRUCT"}

    row = rows[0]
    filename = str(row["filename"])
    offset = int(row["offset"])
    length = int(row["length"])
    url = "https://data.commoncrawl.org/" + filename

    try:
        status, compressed = fetch_range(url, offset, length)
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return {
            "symbol": symbol,
            "status": "INFRA_ACCESS_BLOCKED",
            "http_status": int(exc.code),
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
            "error_body_excerpt": body.decode("utf-8", errors="replace")[:500],
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "symbol": symbol,
            "status": "INFRA_ACCESS_BLOCKED",
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
        }

    time.sleep(REQUEST_GAP_SECONDS)

    if status != 206 or len(compressed) != length:
        return {
            "symbol": symbol,
            "status": "INFRA_ACCESS_BLOCKED",
            "http_status": status,
            "received_bytes": len(compressed),
            "expected_bytes": length,
            "compressed_sha256": sha256(compressed),
            "reason": "HTTP Range response did not satisfy the indexed byte-range contract",
        }

    compressed_digest = sha256(compressed)
    try:
        record = gzip.decompress(compressed)
    except (OSError, EOFError) as exc:
        return {
            "symbol": symbol,
            "status": "BLOCKED_WARC_GZIP",
            "compressed_sha256": compressed_digest,
            "error": str(exc)[:500],
        }

    first_boundary = record.find(b"\r\n\r\n")
    if first_boundary < 0:
        return {
            "symbol": symbol,
            "status": "BLOCKED_WARC_SCHEMA",
            "compressed_sha256": compressed_digest,
            "record_sha256": sha256(record),
            "reason": "missing WARC header terminator",
        }

    warc_header_blob = record[:first_boundary]
    remainder = record[first_boundary + 4:]
    warc_headers = parse_headers(warc_header_blob)

    try:
        warc_content_length = parse_positive_content_length(warc_headers, "Content-Length")
    except ValueError as exc:
        return {
            "symbol": symbol,
            "status": "BLOCKED_WARC_SCHEMA",
            "compressed_sha256": compressed_digest,
            "record_sha256": sha256(record),
            "reason": str(exc),
        }

    if warc_content_length is None or len(remainder) < warc_content_length:
        return {
            "symbol": symbol,
            "status": "BLOCKED_WARC_SCHEMA",
            "compressed_sha256": compressed_digest,
            "record_sha256": sha256(record),
            "warc_content_length": warc_content_length,
            "available_record_block_bytes": len(remainder),
            "reason": "WARC Content-Length does not delimit a complete record block",
        }

    warc_block = remainder[:warc_content_length]
    warc_trailer = remainder[warc_content_length:]
    if warc_trailer not in (b"", b"\r\n\r\n"):
        return {
            "symbol": symbol,
            "status": "BLOCKED_WARC_SCHEMA",
            "compressed_sha256": compressed_digest,
            "record_sha256": sha256(record),
            "warc_content_length": warc_content_length,
            "warc_trailer_bytes": len(warc_trailer),
            "reason": "unexpected bytes after WARC record block",
        }

    second_boundary = warc_block.find(b"\r\n\r\n")
    if second_boundary < 0:
        return {
            "symbol": symbol,
            "status": "BLOCKED_WARC_SCHEMA",
            "compressed_sha256": compressed_digest,
            "record_sha256": sha256(record),
            "warc_content_length": warc_content_length,
            "reason": "missing HTTP header terminator inside WARC record",
        }

    http_header_blob = warc_block[:second_boundary]
    http_remainder = warc_block[second_boundary + 4:]
    http_headers = parse_headers(http_header_blob)

    http_content_length = None
    try:
        http_content_length = parse_positive_content_length(http_headers, "Content-Length")
    except ValueError as exc:
        return {
            "symbol": symbol,
            "status": "BLOCKED_WARC_SCHEMA",
            "compressed_sha256": compressed_digest,
            "record_sha256": sha256(record),
            "warc_content_length": warc_content_length,
            "reason": str(exc),
        }

    if http_content_length is not None:
        if len(http_remainder) < http_content_length:
            return {
                "symbol": symbol,
                "status": "BLOCKED_WARC_SCHEMA",
                "compressed_sha256": compressed_digest,
                "record_sha256": sha256(record),
                "warc_content_length": warc_content_length,
                "http_content_length": http_content_length,
                "available_http_body_bytes": len(http_remainder),
                "reason": "HTTP Content-Length exceeds bytes inside WARC record block",
            }
        payload = http_remainder[:http_content_length]
        http_trailer_bytes = http_remainder[http_content_length:]
    else:
        payload = http_remainder
        http_trailer_bytes = b""

    warc_payload_digest = header_value(warc_headers, "WARC-Payload-Digest")
    payload_digest = hashlib.sha1(payload).digest()
    import base64
    digest_b32 = base64.b32encode(payload_digest).decode("ascii").rstrip("=")

    expected_digest = str(row["digest"])
    target = header_value(warc_headers, "WARC-Target-URI")
    warc_date = header_value(warc_headers, "WARC-Date")
    indexed_timestamp = str(row["timestamp"])
    http_status = http_header_blob.split(b"\r\n", 1)[0].decode("utf-8", errors="replace")

    checks = {
        "warc_version_present": record.startswith(b"WARC/"),
        "warc_date_present": bool(warc_date),
        "target_uri_present": bool(target),
        "http_status_line_present": http_status.startswith("HTTP/"),
        "payload_digest_matches_index": digest_b32 == expected_digest,
        "warc_payload_digest_present": bool(warc_payload_digest),
        "payload_digest_matches_warc_header": bool(warc_payload_digest)
        and warc_payload_digest.split(":", 1)[-1] == digest_b32,
        "target_matches_index_url": bool(target)
        and bool(row.get("indexed_url"))
        and str(row.get("indexed_url")) == target,
        "http_content_length_boundary_exact": http_content_length is not None
        and not http_trailer_bytes,
    }


    return {
        "symbol": symbol,
        "status": "WARC_RECONSTRUCTED" if all(checks.values()) else "BLOCKED_WARC_SEMANTIC_CHECK",
        "indexed_timestamp": indexed_timestamp,
        "warc_date": warc_date,
        "target_uri": target,
        "http_status_line": http_status,
        "warc_record_sha256": sha256(record),
        "compressed_sha256": compressed_digest,
        "payload_sha1_base32": digest_b32,
        "index_digest": expected_digest,
        "payload_bytes": len(payload),
        "checks": checks,
    }


def run(coverage_path: Path, output: Path) -> dict[str, object]:
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    results = {
        symbol: reconstruct(symbol, item)
        for symbol, item in coverage.get("results", {}).items()
        if item.get("status") == "CAPTURE_FOUND"
    }
    payload = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-Q171-WARC-RECONSTRUCTION",
        "coverage_receipt_path": str(coverage_path),
        "coverage_receipt_fingerprint": coverage.get("receipt_fingerprint"),
        "results": results,
        "summary": {
            "capture_candidates": len(results),
            "warc_reconstructed": sum(r["status"] == "WARC_RECONSTRUCTED" for r in results.values()),
            "infra_blocked": sum(r["status"] == "INFRA_ACCESS_BLOCKED" for r in results.values()),
            "blocked": sum(r["status"] != "WARC_RECONSTRUCTED" for r in results.values()),
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
    fingerprint_input = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["receipt_fingerprint"] = sha256(fingerprint_input)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("coverage_path", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.coverage_path, args.output)
    non_infra_blocked = [
        item for item in result["results"].values()
        if item["status"] not in {"WARC_RECONSTRUCTED", "INFRA_ACCESS_BLOCKED"}
    ]
    return 0 if not non_infra_blocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
