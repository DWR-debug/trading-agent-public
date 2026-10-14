"""Q127-R3: bounded Common Crawl index metadata for fixed FINRA daily files.

This is a distinct archive route from Internet Archive CDX. It queries only
index metadata for four frozen FINRA URLs; no WARC record or target data file
is downloaded. Capture time is an archive observation, not first-public time.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

R1_FP = "2cbe22c49d885f527ac523ed74ab1e13a843c23999916c674282de6977e9c33c"
R1_TASK = "Q-2026-10-03-127R1-FINRA-REGSHO-HISTORICAL-PIT"
R1_RUN_ID = 38455702686
FIXED_DATES = ("2024-02-05", "2024-07-01", "2025-01-02", "2025-09-24")
SYMBOLS = ("SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN")
URL_TEMPLATE = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{yyyymmdd}.txt"
INDEX_LIST_URL = "https://index.commoncrawl.org/collinfo.json"
COLLECTION_START_LOOKAHEAD_DAYS = 30
MAX_CAPTURE_LAG_DAYS = 45
MAX_REQUESTS = 5
MAX_RESPONSE_BYTES = 300_000
MAX_TOTAL_BYTES = 1_200_000
REQUEST_PATH = Path("research/run_requests/q127r3_finra_commoncrawl_metadata.trigger")
FROZEN = {
    "RUN_Q127R3_FINRA_COMMONCRAWL_METADATA": "true",
    "R1_SOURCE_RUN_ID": str(R1_RUN_ID),
    "R1_RECEIPT_FINGERPRINT": R1_FP,
    "R1_TASK_ID": R1_TASK,
    "FIXED_DATES": ",".join(FIXED_DATES),
    "FIXED_SYMBOLS": ",".join(SYMBOLS),
    "INDEX_LIST_URL": INDEX_LIST_URL,
    "COLLECTION_START_LOOKAHEAD_DAYS": str(COLLECTION_START_LOOKAHEAD_DAYS),
    "MAX_CAPTURE_LAG_DAYS": str(MAX_CAPTURE_LAG_DAYS),
    "MAX_REQUESTS": str(MAX_REQUESTS),
    "MAX_RESPONSE_BYTES": str(MAX_RESPONSE_BYTES),
    "MAX_TOTAL_BYTES": str(MAX_TOTAL_BYTES),
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}


class ProbeError(RuntimeError):
    pass


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw:
            continue
        if "=" not in raw:
            raise ProbeError(f"REQUEST_LINE_INVALID:{line_no}")
        key, value = raw.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or key in values:
            raise ProbeError(f"REQUEST_KEY_INVALID_OR_DUPLICATE:{line_no}")
        values[key] = value
    if set(values) != set(FROZEN) | {"REQUEST_SEQUENCE"}:
        raise ProbeError("REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN.items():
        if values.get(key) != expected:
            raise ProbeError(f"FROZEN_REQUEST_MISMATCH:{key}")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values.get("REQUEST_SEQUENCE", "")):
        raise ProbeError("REQUEST_SEQUENCE_INVALID")
    return values


def target_urls() -> dict[str, str]:
    return {
        value: URL_TEMPLATE.format(yyyymmdd=value.replace("-", ""))
        for value in FIXED_DATES
    }


def validate_r1(receipt: dict[str, Any]) -> None:
    if (
        receipt.get("task_id") != R1_TASK
        or receipt.get("status") != "Q127R1_SOURCE_PIT_FEASIBILITY_COMPLETED"
        or receipt.get("receipt_fingerprint") != R1_FP
        or set((receipt.get("observations") or {}).keys()) != set(FIXED_DATES)
        or receipt.get("pit", {}).get("same_day_pit_safe") is not False
        or receipt.get("pit", {}).get("revision_lineage_established") is not False
    ):
        raise ProbeError("Q127R1_UPSTREAM_RECEIPT_PIN_MISMATCH")
    for sample_date in FIXED_DATES:
        obs = receipt["observations"][sample_date]
        if obs.get("source_url") != target_urls()[sample_date] or obs.get("status") != "PASS":
            raise ProbeError(f"Q127R1_FIXED_OBSERVATION_MISMATCH:{sample_date}")
        if set((obs.get("rows_for_fixed_symbols") or {}).keys()) != set(SYMBOLS):
            raise ProbeError(f"Q127R1_FIXED_SYMBOL_COVERAGE_MISMATCH:{sample_date}")


def _iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def select_collection(collections: list[dict[str, Any]], target_date: str) -> dict[str, Any] | None:
    target = date.fromisoformat(target_date)
    latest_start = target + timedelta(days=COLLECTION_START_LOOKAHEAD_DAYS)
    eligible = []
    for item in collections:
        if not isinstance(item, dict):
            continue
        collection_id = str(item.get("id") or "")
        api_url = str(item.get("cdx-api") or "")
        start = _iso_date(item.get("from"))
        end = _iso_date(item.get("to"))
        if not re.fullmatch(r"CC-MAIN-\d{4}-\d{2}", collection_id):
            continue
        if not api_url.startswith("https://index.commoncrawl.org/"):
            continue
        if start is None or end is None or end < start:
            continue
        # A collection can begin before the report date and still capture
        # the exact URL after that date. Select the earliest collection whose
        # advertised interval intersects [target, target + lookahead]; the
        # actual per-URL timestamp is checked separately after the exact query.
        if end >= target and start <= latest_start:
            eligible.append((start, collection_id, item))
    if not eligible:
        return None
    return sorted(eligible, key=lambda x: (x[0], x[1]))[0][2]


def parse_cdx_jsonl(body: bytes, expected_url: str) -> list[dict[str, Any]]:
    if not body.strip():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(body.splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProbeError(f"COMMONCRAWL_INVALID_JSONL:{line_no}") from exc
        if not isinstance(item, dict):
            raise ProbeError(f"COMMONCRAWL_ROW_NOT_OBJECT:{line_no}")
        if item.get("url") != expected_url:
            raise ProbeError(f"COMMONCRAWL_EXACT_URL_MISMATCH:{line_no}")
        timestamp = item.get("timestamp")
        if not isinstance(timestamp, str) or not re.fullmatch(r"20\d{12}", timestamp):
            raise ProbeError(f"COMMONCRAWL_TIMESTAMP_INVALID:{line_no}")
        try:
            datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        except ValueError as exc:
            raise ProbeError(f"COMMONCRAWL_TIMESTAMP_INVALID:{line_no}") from exc
        for field in ("status", "digest", "length", "filename", "offset"):
            if item.get(field) is None:
                raise ProbeError(f"COMMONCRAWL_REQUIRED_INDEX_FIELD_MISSING:{line_no}:{field}")
        rows.append({
            "timestamp": timestamp,
            "url": item["url"],
            "status": str(item["status"]),
            "mime": item.get("mime"),
            "digest_sha1_base32": str(item["digest"]),
            "warc_record_length": str(item["length"]),
            "warc_filename": str(item["filename"]),
            "warc_offset": str(item["offset"]),
        })
    return sorted(rows, key=lambda x: x["timestamp"])


def fetch_bounded(url: str, max_bytes: int) -> tuple[int, bytes, dict[str, str], str, str | None]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DWR-debug/trading-agent-public/Q127R3-CommonCrawl-Metadata/1",
            "Accept": "application/json,application/x-ndjson,*/*",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            body = response.read(max_bytes)
            headers = {key.lower(): value for key, value in response.headers.items()}
            final_url = response.geturl()
            status = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as exc:
        body = exc.read(max_bytes)
        headers = {key.lower(): value for key, value in exc.headers.items()} if exc.headers else {}
        return int(exc.code), body, headers, url, "HTTP_ERROR"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, b"", {}, url, f"TRANSPORT_ERROR:{type(exc).__name__}"
    declared = headers.get("content-length")
    if len(body) >= max_bytes or (declared and declared.isdigit() and int(declared) > len(body)):
        return status, body, headers, final_url, "RESPONSE_LIMIT_REACHED_OR_TRUNCATED"
    return status, body, headers, final_url, None


def console_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Expose bounded failure details to Actions logs without dumping payloads or query URLs."""
    summary = result.get("summary", {})
    request_diagnostics = [
        {
            "label": item.get("label"),
            "http_status": item.get("http_status"),
            "response_bytes": item.get("response_bytes"),
            "error": item.get("error"),
        }
        for item in result.get("requests", [])
    ]
    target_diagnostics = {
        day: {
            "collection_selection_status": item.get("collection_selection_status"),
            "collection_id": item.get("collection_id"),
            "query_completed": item.get("query_completed"),
            "capture_count": item.get("capture_count", 0),
            "http_200_capture_within_max_lag_count": item.get("http_200_capture_within_max_lag_count", 0),
        }
        for day, item in result.get("observations", {}).items()
    }
    return {
        "status": result.get("status"),
        "captured_dates": summary.get("exact_file_dates_with_http_200_capture_within_max_lag", []),
        "requests": summary.get("request_count", 0),
        "download_bytes": summary.get("download_bytes", 0),
        "error_count": summary.get("error_count", 0),
        "errors": summary.get("errors", [])[:20],
        "request_diagnostics": request_diagnostics,
        "target_diagnostics": target_diagnostics,
        "receipt_fingerprint": result.get("receipt_fingerprint"),
    }


def run(
    request_path: Path,
    source_receipt_path: Path,
    output_path: Path,
    *,
    fetcher: Callable[[str, int], tuple[int, bytes, dict[str, str], str, str | None]] = fetch_bounded,
) -> dict[str, Any]:
    read_request(request_path)
    upstream = json.loads(source_receipt_path.read_text(encoding="utf-8"))
    validate_r1(upstream)
    state = {"request_count": 0, "download_bytes": 0}
    errors: list[str] = []
    requests: list[dict[str, Any]] = []
    observations: dict[str, dict[str, Any]] = {}
    index_rows: list[dict[str, Any]] = []

    def one(label: str, url: str) -> tuple[int, bytes]:
        if state["request_count"] >= MAX_REQUESTS:
            errors.append(f"{label}:REQUEST_BUDGET_EXHAUSTED")
            return 0, b""
        remaining = MAX_TOTAL_BYTES - state["download_bytes"]
        if remaining <= 0:
            errors.append(f"{label}:TOTAL_BYTE_BUDGET_EXHAUSTED")
            return 0, b""
        limit = min(MAX_RESPONSE_BYTES, remaining)
        state["request_count"] += 1
        status, body, headers, final_url, error = fetcher(url, limit)
        state["download_bytes"] += len(body)
        requests.append({
            "label": label,
            "requested_url": url,
            "final_url": final_url,
            "http_status": status,
            "response_bytes": len(body),
            "response_sha256": hashlib.sha256(body).hexdigest() if body else None,
            "content_type": headers.get("content-type"),
            "error": error,
        })
        if error or status != 200:
            errors.append(f"{label}:{error or 'HTTP_' + str(status)}")
        return status, body

    status, body = one("commoncrawl_collection_index", INDEX_LIST_URL)
    if status == 200 and body:
        try:
            payload = json.loads(body.decode("utf-8"))
            if not isinstance(payload, list):
                raise ProbeError("COMMONCRAWL_COLLECTION_INDEX_NOT_LIST")
            index_rows = [row for row in payload if isinstance(row, dict)]
            if not index_rows:
                raise ProbeError("COMMONCRAWL_COLLECTION_INDEX_EMPTY")
        except (UnicodeDecodeError, json.JSONDecodeError, ProbeError) as exc:
            errors.append("commoncrawl_collection_index:" + str(exc))
    else:
        errors.append("commoncrawl_collection_index:NO_VALID_COLLECTION_INDEX")

    index_receipt = requests[0] if requests else {}
    index_receipt["collection_count"] = len(index_rows)
    for target_date, source_url in target_urls().items():
        selected = select_collection(index_rows, target_date)
        if selected is None:
            observations[target_date] = {
                "source_url": source_url,
                "collection_selection_status": "NO_CRAWL_START_WITHIN_LOOKAHEAD_WINDOW",
                "collection_id": None,
                "collection_from": None,
                "collection_to": None,
                "query_completed": False,
                "captures": [],
                "capture_count": 0,
                "capture_within_max_lag_count": 0,
            }
            continue

        query_params = {
            "url": source_url,
            "matchType": "exact",
            "output": "json",
            "fl": "timestamp,url,status,mime,digest,length,filename,offset",
            "limit": "100",
        }
        query_url = str(selected["cdx-api"]) + "?" + urllib.parse.urlencode(query_params)
        query_status, query_body = one("target_url_cdx_" + target_date, query_url)
        captures: list[dict[str, Any]] = []
        query_completed = query_status == 200
        if query_completed:
            try:
                captures = parse_cdx_jsonl(query_body, source_url)
            except ProbeError as exc:
                errors.append("target_url_cdx_" + target_date + ":" + str(exc))
                query_completed = False

        target = date.fromisoformat(target_date)
        for capture in captures:
            capture_date = datetime.strptime(capture["timestamp"], "%Y%m%d%H%M%S").date()
            capture["capture_date"] = capture_date.isoformat()
            capture["capture_lag_days"] = (capture_date - target).days
            capture["within_max_capture_lag"] = 0 <= capture["capture_lag_days"] <= MAX_CAPTURE_LAG_DAYS
        observations[target_date] = {
            "source_url": source_url,
            "collection_selection_status": "COLLECTION_SELECTED",
            "collection_id": selected.get("id"),
            "collection_from": selected.get("from"),
            "collection_to": selected.get("to"),
            "query_url": query_url,
            "query_completed": query_completed,
            "captures": captures,
            "capture_count": len(captures),
            "capture_within_max_lag_count": sum(1 for row in captures if row["within_max_capture_lag"]),
            "http_200_capture_within_max_lag_count": sum(
                1 for row in captures if row["status"] == "200" and row["within_max_capture_lag"]
            ),
            "response_at_limit_may_be_truncated": any(
                item["label"] == "target_url_cdx_" + target_date and item.get("error") == "RESPONSE_LIMIT_REACHED_OR_TRUNCATED"
                for item in requests
            ),
        }

    captured_dates = [
        day for day, item in observations.items()
        if item.get("http_200_capture_within_max_lag_count", 0) > 0
    ]
    result: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q127r3_finra_commoncrawl_metadata_probe",
        "candidate_id": "Q127-R3",
        "task_id": "Q-2026-10-13-127R3-FINRA-COMMONCRAWL-METADATA",
        "status": "Q127R3_COMMONCRAWL_METADATA_COMPLETED" if not errors else "Q127R3_COMMONCRAWL_METADATA_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "upstream": {
            "run_id": R1_RUN_ID,
            "task_id": R1_TASK,
            "receipt_fingerprint": upstream["receipt_fingerprint"],
        },
        "fixed_population": {"dates": list(FIXED_DATES), "symbols": list(SYMBOLS), "target_file_count": len(FIXED_DATES)},
        "method": {
            "source": "Common Crawl monthly CDXJ/URL metadata index",
            "query_design": "one collection index list plus at most one exact-URL metadata query per frozen target date",
            "collection_start_lookahead_days": COLLECTION_START_LOOKAHEAD_DAYS,
            "max_capture_lag_days": MAX_CAPTURE_LAG_DAYS,
            "max_request_count": MAX_REQUESTS,
            "max_response_bytes": MAX_RESPONSE_BYTES,
            "max_total_metadata_bytes": MAX_TOTAL_BYTES,
            "target_files_downloaded": 0,
            "warc_records_downloaded": 0,
            "archived_payload_downloaded": False,
        },
        "index_list": index_receipt,
        "requests": requests,
        "observations": observations,
        "summary": {
            "request_count": state["request_count"],
            "download_bytes": state["download_bytes"],
            "exact_file_dates_with_http_200_capture_within_max_lag": captured_dates,
            "captured_date_count": len(captured_dates),
            "target_dates_without_selected_collection": [
                day for day, item in observations.items()
                if item.get("collection_selection_status") == "NO_CRAWL_START_WITHIN_LOOKAHEAD_WINDOW"
            ],
            "error_count": len(errors),
            "errors": errors,
        },
        "pit_interpretation": {
            "commoncrawl_capture_is_first_publication_time": False,
            "exact_first_publication_time_proven": False,
            "original_vs_updated_file_lineage_proven": False,
            "same_day_formal_use_allowed": False,
            "positive_capture_only_bounds_that_the_url_was_crawled_at_capture_time": True,
            "no_capture_is_proof_of_nonpublication": False,
        },
        "governance": {
            "performance": False,
            "performance_authorized": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
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
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(console_summary(result), sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.request, args.source_receipt, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
