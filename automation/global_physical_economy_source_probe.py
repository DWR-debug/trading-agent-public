"""Bounded international physical-economy source probe.

Captures small JSON metadata/row samples from PortWatch and Copernicus STAC.
It does not download satellite imagery, query UN Comtrade, infer issuer links,
calculate returns, or validate a historical point-in-time (PIT) signal.
All raw response bodies are retained only when the complete response is within
the fixed byte ceiling. Successful retrieval is explicitly not PIT approval.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PORTWATCH_LAYER_URL = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
    "Daily_Chokepoints_Data/FeatureServer/0?f=pjson"
)
PORTWATCH_QUERY_BASE = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
    "Daily_Chokepoints_Data/FeatureServer/0/query"
)
COPERNICUS_COLLECTION_URL = (
    "https://stac.dataspace.copernicus.eu/v1/collections/sentinel-2-l2a"
)
COPERNICUS_SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"

# Fixed, small, internationally distributed sample windows. This is a source
# access probe, not a representative performance sample or a port ranking.
STAC_WINDOWS = (
    {"id": "rotterdam", "bbox": "3.8,51.7,4.6,52.2"},
    {"id": "singapore", "bbox": "103.5,1.0,104.5,1.8"},
    {"id": "ningbo", "bbox": "121.3,29.2,122.0,30.2"},
)
STAC_DATETIME = "2025-10-01T00:00:00Z/2025-10-15T23:59:59Z"
MAX_RESPONSE_BYTES = 1_000_000
REQUEST_TIMEOUT_SECONDS = 20
USER_AGENT = "DWR-debug/trading-agent-public-global-physical-source-probe/1.0"
CAPTURED_HEADERS = (
    "content-type",
    "content-length",
    "date",
    "etag",
    "last-modified",
    "cache-control",
    "age",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _headers_map(headers: Any) -> dict[str, str]:
    return {
        key: str(headers.get(key, ""))
        for key in CAPTURED_HEADERS
        if headers is not None and headers.get(key) is not None
    }


def fetch_bounded_json(source_id: str, url: str) -> dict[str, Any]:
    """Fetch a bounded JSON response and preserve exact body bytes if complete."""
    started_at = utc_now()
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        method="GET",
    )
    record: dict[str, Any] = {
        "source_id": source_id,
        "url": url,
        "method": "GET",
        "started_at_utc": started_at,
        "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "max_response_bytes": MAX_RESPONSE_BYTES,
        "http_status": None,
        "response_headers": {},
        "capture_state": "FETCH_ERROR",
        "raw_body_base64": None,
        "raw_body_sha256": None,
        "raw_body_bytes": None,
        "parsed_json": None,
        "error": None,
    }
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            record["http_status"] = int(getattr(response, "status", 200))
            record["response_headers"] = _headers_map(response.headers)
            declared = record["response_headers"].get("content-length")
            record["declared_content_length"] = (
                int(declared) if declared and declared.isdigit() else None
            )
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        record["http_status"] = int(exc.code)
        record["response_headers"] = _headers_map(exc.headers)
        record["error"] = f"HTTP_ERROR:{exc.code}"
        try:
            body = exc.read(MAX_RESPONSE_BYTES + 1)
        except Exception:
            body = b""
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        record["error"] = f"FETCH_ERROR:{type(exc).__name__}:{str(exc)[:240]}"
        record["completed_at_utc"] = utc_now()
        return record

    record["completed_at_utc"] = utc_now()
    if len(body) > MAX_RESPONSE_BYTES:
        record["capture_state"] = "RESPONSE_OVER_BYTE_LIMIT"
        record["partial_prefix_bytes"] = MAX_RESPONSE_BYTES
        record["partial_prefix_sha256"] = sha256_hex(body[:MAX_RESPONSE_BYTES])
        record["raw_body_bytes"] = None
        record["raw_body_sha256"] = None
        return record

    record["raw_body_bytes"] = len(body)
    record["raw_body_sha256"] = sha256_hex(body)
    record["raw_body_base64"] = base64.b64encode(body).decode("ascii")
    try:
        record["parsed_json"] = json.loads(body.decode("utf-8"))
        record["capture_state"] = (
            "COMPLETE_JSON_HTTP_200"
            if record["http_status"] == 200
            else "COMPLETE_JSON_NON_200"
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        record["capture_state"] = "COMPLETE_BODY_NOT_VALID_JSON"
        record["error"] = f"JSON_PARSE_ERROR:{type(exc).__name__}:{str(exc)[:160]}"
    return record


def _build_portwatch_query_url(object_id_field: str) -> str:
    # The object-ID field comes from the just-captured layer metadata. It is
    # URL-escaped and used only as a deterministic sample ordering key.
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "false",
        "resultRecordCount": "3",
        "orderByFields": f"{object_id_field} ASC",
        "f": "json",
    }
    return PORTWATCH_QUERY_BASE + "?" + urllib.parse.urlencode(params)


def build_receipt() -> dict[str, Any]:
    """Capture a small fixed source sample; never emits a performance result."""
    started_at = utc_now()
    requests: list[dict[str, Any]] = []
    requests.append(fetch_bounded_json("portwatch_layer_metadata", PORTWATCH_LAYER_URL))
    requests.append(
        fetch_bounded_json("copernicus_collection_metadata", COPERNICUS_COLLECTION_URL)
    )

    layer_json = requests[0].get("parsed_json")
    object_id_field = (
        layer_json.get("objectIdField")
        or layer_json.get("objectIdFieldName")
        or layer_json.get("objectIdFieldNameAlias")
        if isinstance(layer_json, dict)
        else None
    )
    # Do not run a nondeterministically ordered row query when the stable
    # object-ID field cannot be established from metadata.
    if isinstance(object_id_field, str) and object_id_field.strip():
        requests.append(
            fetch_bounded_json(
                "portwatch_bounded_first_three_rows",
                _build_portwatch_query_url(object_id_field.strip()),
            )
        )
        portwatch_query_state = "REQUESTED_WITH_METADATA_OBJECT_ID_ORDER"
    else:
        portwatch_query_state = "BLOCKED_OBJECT_ID_FIELD_UNRESOLVED"

    stac_states: list[dict[str, Any]] = []
    for window in STAC_WINDOWS:
        params = {
            "collections": "sentinel-2-l2a",
            "bbox": window["bbox"],
            "datetime": STAC_DATETIME,
            "limit": "2",
        }
        url = COPERNICUS_SEARCH_URL + "?" + urllib.parse.urlencode(params)
        request_record = fetch_bounded_json(f"copernicus_stac_{window['id']}", url)
        requests.append(request_record)
        payload = request_record.get("parsed_json")
        features = payload.get("features", []) if isinstance(payload, dict) else []
        stac_states.append({
            "window_id": window["id"],
            "bbox": window["bbox"],
            "datetime_filter": STAC_DATETIME,
            "limit": 2,
            "http_status": request_record.get("http_status"),
            "capture_state": request_record.get("capture_state"),
            "feature_count_returned": len(features) if isinstance(features, list) else None,
            "items": [
                {
                    "id": feature.get("id"),
                    "collection": feature.get("collection"),
                    "properties": {
                        key: feature.get("properties", {}).get(key)
                        for key in (
                            "datetime", "created", "updated", "platform",
                            "processing:level", "product:type", "eo:cloud_cover"
                        )
                    },
                }
                for feature in features[:2]
                if isinstance(feature, dict)
            ],
        })

    successful_json_responses = sum(
        record.get("capture_state") == "COMPLETE_JSON_HTTP_200" for record in requests
    )
    all_requested_succeeded = successful_json_responses == len(requests)
    layer_json = layer_json if isinstance(layer_json, dict) else {}
    collection_json = requests[1].get("parsed_json")
    collection_json = collection_json if isinstance(collection_json, dict) else {}
    extent = collection_json.get("extent", {})
    temporal = extent.get("temporal", {}) if isinstance(extent, dict) else {}

    return {
        "schema_version": "1.0",
        "task_id": "GLOBAL-PHYSICAL-ECONOMY-SOURCE-PROBE-2026-10-23",
        "generated_at_utc": utc_now(),
        "probe_started_at_utc": started_at,
        "status": (
            "BOUNDED_SOURCES_CAPTURED_PIT_UNPROVEN"
            if all_requested_succeeded and portwatch_query_state.startswith("REQUESTED")
            else "SOURCE_FETCH_INCOMPLETE_OR_QUERY_BLOCKED"
        ),
        "scope": {
            "purpose": "bounded public source/metadata feasibility only",
            "portwatch_row_limit": 3,
            "copernicus_items_per_fixed_window_limit": 2,
            "copernicus_fixed_windows": [dict(row) for row in STAC_WINDOWS],
            "copernicus_datetime_filter": STAC_DATETIME,
            "max_response_bytes": MAX_RESPONSE_BYTES,
            "satellite_imagery_downloaded": False,
            "un_comtrade_queried": False,
            "prices_or_returns_requested": False,
        },
        "source_summary": {
            "portwatch": {
                "http_status": requests[0].get("http_status"),
                "capture_state": requests[0].get("capture_state"),
                "is_data_versioned": layer_json.get("isDataVersioned"),
                "data_last_edit_date_epoch_ms": (
                    layer_json.get("editingInfo", {}).get("dataLastEditDate")
                    if isinstance(layer_json.get("editingInfo"), dict)
                    else None
                ),
                "object_id_field": object_id_field,
                "row_query_state": portwatch_query_state,
            },
            "copernicus": {
                "collection_http_status": requests[1].get("http_status"),
                "collection_capture_state": requests[1].get("capture_state"),
                "collection_temporal_extent": temporal.get("interval"),
                "collection_license": collection_json.get("license"),
                "items": stac_states,
            },
        },
        "requests": requests,
        "historical_pit_gate": {
            "status": "NOT_PROVEN",
            "portwatch_historical_versions_retrievable": False,
            "copernicus_product_first_public_availability_proven": False,
            "contemporaneous_asset_to_issuer_map_frozen": False,
            "un_comtrade_historical_vintages_available_via_current_api": False,
            "gate_pass": False,
            "note": (
                "A successful current metadata or item response does not establish "
                "historical source vintages, first public availability, or issuer exposure."
            ),
        },
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
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


def main(output: Path, fail_on_fetch_error: bool = False) -> int:
    receipt = build_receipt()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replace prevents an interrupted write from appearing as a complete receipt.
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, output)
    print(json.dumps({
        "status": receipt["status"],
        "output": str(output),
        "request_count": len(receipt["requests"]),
        "successful_json_http_200": sum(
            r.get("capture_state") == "COMPLETE_JSON_HTTP_200"
            for r in receipt["requests"]
        ),
        "historical_pit_gate": receipt["historical_pit_gate"]["status"],
        "gate_pass": receipt["historical_pit_gate"]["gate_pass"],
    }, sort_keys=True))
    if fail_on_fetch_error and receipt["status"] != "BOUNDED_SOURCES_CAPTURED_PIT_UNPROVEN":
        return 2
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/runs/global_physical_economy_source_probe/latest.json"),
    )
    parser.add_argument("--fail-on-fetch-error", action="store_true")
    args = parser.parse_args()
    raise SystemExit(main(args.output, fail_on_fetch_error=args.fail_on_fetch_error))
