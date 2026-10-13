"""Bounded HTTP metadata primitives for Wayback CDX feasibility probes.

This module never retrieves the archived target payload itself. Callers query
only CDX metadata or explicitly pinned, small source-index captures.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

CDX_BASE = "https://web.archive.org/cdx/search/cdx"
USER_AGENT = "DWR-debug/trading-agent-public/archival-metadata-feasibility/1"


class MetadataProbeError(RuntimeError):
    """A bounded archive metadata request violated its contract."""


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_fingerprint(value: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    payload = {key: item for key, item in value.items() if key != field}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def build_cdx_url(original_url: str, *, from_year: int, to_year: int, limit: int = 100) -> str:
    if not original_url.startswith(("https://", "http://")):
        raise MetadataProbeError("CDX_ORIGINAL_URL_INVALID")
    if from_year < 1996 or to_year < from_year or limit < 1 or limit > 100:
        raise MetadataProbeError("CDX_QUERY_BOUNDS_INVALID")
    params = {
        "url": original_url,
        "output": "json",
        "filter": "statuscode:200",
        "matchType": "exact",
        "fl": "timestamp,original,statuscode,digest,length",
        "from": str(from_year),
        "to": str(to_year),
        "limit": str(limit),
    }
    return CDX_BASE + "?" + urllib.parse.urlencode(params)


def parse_cdx_rows(body: bytes, expected_original: str | None = None) -> list[dict[str, str]]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MetadataProbeError("CDX_RESPONSE_NOT_JSON") from exc
    if payload == []:
        return []
    if not isinstance(payload, list) or not payload or not all(isinstance(row, list) for row in payload):
        raise MetadataProbeError("CDX_RESPONSE_SHAPE_INVALID")
    header = payload[0]
    required = ("timestamp", "original", "statuscode", "digest", "length")
    if not isinstance(header, list) or not set(required).issubset({str(x) for x in header}):
        raise MetadataProbeError("CDX_HEADER_INVALID")
    indexes = {str(name): header.index(name) for name in required}
    output: list[dict[str, str]] = []
    for row in payload[1:]:
        if len(row) != len(header):
            raise MetadataProbeError("CDX_ROW_WIDTH_INVALID")
        item = {name: str(row[index]) for name, index in indexes.items()}
        if not re.fullmatch(r"\d{14}", item["timestamp"]):
            raise MetadataProbeError("CDX_TIMESTAMP_INVALID")
        if not item["original"] or item["statuscode"] != "200":
            raise MetadataProbeError("CDX_CAPTURE_IDENTITY_INVALID")
        if not item["digest"] or not item["length"].isdigit():
            raise MetadataProbeError("CDX_CAPTURE_METADATA_INVALID")
        if expected_original is not None and item["original"] != expected_original:
            raise MetadataProbeError("CDX_CAPTURE_URL_MISMATCH")
        output.append(item)
    return output


def fetch_bounded(
    url: str,
    *,
    max_requests: int,
    max_response_bytes: int,
    max_total_bytes: int,
    state: dict[str, Any],
    opener: Callable[..., Any] | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    """Fetch one response under explicit request and byte caps; no automatic retry."""
    if state.get("request_count", 0) >= max_requests:
        raise MetadataProbeError("REQUEST_COUNT_CAP_EXCEEDED")
    if not url.startswith("https://web.archive.org/"):
        raise MetadataProbeError("NON_ARCHIVE_URL_FORBIDDEN")
    state["request_count"] = int(state.get("request_count", 0)) + 1
    open_url = opener or urllib.request.urlopen
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/html,*/*", "Accept-Encoding": "identity"},
    )
    status = 200
    headers: dict[str, str] = {}
    try:
        with open_url(request, timeout=20) as response:
            status = int(getattr(response, "status", 200))
            headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
            body = response.read(max_response_bytes + 1)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        headers = {str(k).lower(): str(v) for k, v in (exc.headers or {}).items()}
        body = exc.read(max_response_bytes + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        state.setdefault("transport_errors", []).append(f"{type(exc).__name__}:{exc}")
        raise MetadataProbeError(f"ARCHIVE_TRANSPORT_ERROR:{type(exc).__name__}") from exc
    state["metadata_download_bytes"] = int(state.get("metadata_download_bytes", 0)) + len(body)
    if len(body) > max_response_bytes:
        raise MetadataProbeError("PER_RESPONSE_BYTE_CAP_EXCEEDED")
    if state["metadata_download_bytes"] > max_total_bytes:
        raise MetadataProbeError("TOTAL_METADATA_BYTE_CAP_EXCEEDED")
    return status, body, headers
