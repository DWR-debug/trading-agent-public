"""Q130-R2: cheap Wayback metadata feasibility for fixed Wikimedia Pageviews API URLs.

Only queries Internet Archive CDX index metadata for the eight original R1 URLs.
It does not re-fetch pageview values or retrieve archived API response payloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

from automation.wayback_cdx_metadata import (
    MetadataProbeError,
    build_cdx_url,
    canonical_fingerprint,
    fetch_bounded,
    parse_cdx_rows,
)

R1_FP = "4334be29ff2387813ea9586ba12c6899979e0e43125aeaf0585b073063876568"
R1_TASK = "Q-2026-10-03-130R1-WIKIMEDIA-ATTENTION-SOURCE"
ARTICLES = {
    "SPGI": "S&P Global",
    "NDAQ": "Nasdaq",
    "AMP": "Ameriprise Financial",
    "RJF": "Raymond James",
    "WMB": "Williams Companies",
    "VLO": "Valero Energy",
    "DVN": "Devon Energy",
    "EMN": "Eastman Chemical",
}
START = "20250920"
END = "20250924"
API_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"
MAX_REQUESTS = 8
MAX_RESPONSE_BYTES = 200_000
MAX_TOTAL_BYTES = 1_600_000
R1_RUN_RECEIPT = "q130r1-wikimedia-attention-source-38455993358"
FROZEN = {
    "RUN_Q130R2_WIKIMEDIA_WAYBACK_METADATA": "true",
    "R1_SOURCE_RUN_ID": "38455993358",
    "R1_ARTIFACT_NAME": R1_RUN_RECEIPT,
    "R1_RECEIPT_FINGERPRINT": R1_FP,
    "R1_TASK_ID": R1_TASK,
    "FIXED_ARTICLES": "SPGI:S&P Global,NDAQ:Nasdaq,AMP:Ameriprise Financial,RJF:Raymond James,WMB:Williams Companies,VLO:Valero Energy,DVN:Devon Energy,EMN:Eastman Chemical",
    "START": START,
    "END": END,
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


def article_url(title: str) -> str:
    encoded = quote(title.replace(" ", "_"), safe="_")
    return f"{API_BASE}/{encoded}/daily/{START}/{END}"


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw:
            continue
        if not re.fullmatch(r"[A-Z0-9_]+=[A-Za-z0-9._,:/%& -]*", raw):
            raise MetadataProbeError(f"REQUEST_LINE_INVALID:{line_no}")
        key, value = raw.split("=", 1)
        if key in values:
            raise MetadataProbeError(f"REQUEST_DUPLICATE_KEY:{key}")
        values[key] = value
    if set(values) != set(FROZEN) | {"REQUEST_SEQUENCE"}:
        raise MetadataProbeError("REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN.items():
        if values.get(key) != expected:
            raise MetadataProbeError(f"FROZEN_REQUEST_MISMATCH:{key}")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values.get("REQUEST_SEQUENCE", "")):
        raise MetadataProbeError("REQUEST_SEQUENCE_INVALID")
    return values


def validate_r1(receipt: dict[str, Any]) -> None:
    if (
        receipt.get("task_id") != R1_TASK
        or receipt.get("status") != "Q130R1_SOURCE_FEASIBILITY_COMPLETED"
        or receipt.get("receipt_fingerprint") != R1_FP
        or receipt.get("fixed_articles") != ARTICLES
        or receipt.get("feasibility_window") != {"start": "20250920", "end": "20250924"}
        or receipt.get("pit", {}).get("exact_first_publication_time_proven") is not False
        or receipt.get("pit", {}).get("revision_lineage_proven") is not False
        or receipt.get("pit", {}).get("same_day_formal_use_allowed") is not False
        or set((receipt.get("observations") or {}).keys()) != set(ARTICLES)
    ):
        raise MetadataProbeError("Q130R1_UPSTREAM_RECEIPT_PIN_MISMATCH")
    for symbol, title in ARTICLES.items():
        observation = receipt["observations"][symbol]
        if observation.get("article") != title or observation.get("source_url") != article_url(title):
            raise MetadataProbeError(f"Q130R1_FIXED_ARTICLE_OBSERVATION_MISMATCH:{symbol}")


def run(
    request_path: Path,
    source_receipt_path: Path,
    output_path: Path,
    *,
    fetcher: Callable[..., tuple[int, bytes, dict[str, str]]] = fetch_bounded,
) -> dict[str, Any]:
    read_request(request_path)
    source = json.loads(source_receipt_path.read_text(encoding="utf-8"))
    validate_r1(source)
    budget: dict[str, Any] = {"request_count": 0, "metadata_download_bytes": 0, "transport_errors": []}
    observations: dict[str, Any] = {}
    errors: list[str] = []
    for symbol, title in ARTICLES.items():
        original_url = article_url(title)
        cdx_url = build_cdx_url(original_url, from_year=2015, to_year=2026, limit=50)
        try:
            status, body, headers = fetcher(
                cdx_url,
                max_requests=MAX_REQUESTS,
                max_response_bytes=MAX_RESPONSE_BYTES,
                max_total_bytes=MAX_TOTAL_BYTES,
                state=budget,
            )
            query_error = None
            captures = None
            if status == 200:
                try:
                    captures = parse_cdx_rows(body, expected_original=original_url)
                except Exception as exc:
                    query_error = f"{type(exc).__name__}:{exc}"
            else:
                query_error = f"HTTP_{status}"
        except Exception as exc:
            status, body, headers = 0, b"", {}
            captures = None
            query_error = f"{type(exc).__name__}:{exc}"
        if query_error is not None:
            errors.append(f"{symbol}:{query_error}")
        observations[symbol] = {
            "article": title,
            "original_api_url": original_url,
            "cdx_query_http_status": status,
            "cdx_query_response_bytes": len(body),
            "cdx_query_response_sha256": hashlib.sha256(body).hexdigest() if body else None,
            "capture_count": len(captures) if captures is not None else None,
            "captures": captures or [],
            "query_completed": captures is not None,
            "error": query_error,
        }

    result: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q130r2_wikimedia_wayback_metadata_probe",
        "candidate_id": "Q130-R2",
        "task_id": "Q-2026-10-13-130R2-WIKIMEDIA-WAYBACK-METADATA",
        "status": "Q130R2_WAYBACK_METADATA_COMPLETE" if not errors and budget["request_count"] == MAX_REQUESTS else "Q130R2_WAYBACK_METADATA_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": __import__("os").environ.get("GITHUB_SHA"),
        "upstream": {"run_id": 38455993358, "artifact_name": R1_RUN_RECEIPT, "receipt_fingerprint": source["receipt_fingerprint"], "task_id": source["task_id"]},
        "fixed_population": {"articles": ARTICLES, "start": START, "end": END, "article_count": len(ARTICLES)},
        "method": {
            "source": "Internet Archive CDX metadata for exact R1 Wikimedia Pageviews API request URLs",
            "request_count_cap": MAX_REQUESTS,
            "response_byte_cap": MAX_RESPONSE_BYTES,
            "total_metadata_byte_cap": MAX_TOTAL_BYTES,
            "pageview_api_requests_made": 0,
            "archived_api_response_payloads_downloaded": 0,
            "metadata_only": True,
        },
        "observations": observations,
        "summary": {
            "article_count": len(ARTICLES),
            "completed_queries": sum(1 for x in observations.values() if x["query_completed"]),
            "captured_api_responses_found": sum(x["capture_count"] or 0 for x in observations.values()),
            "metadata_request_count": budget["request_count"],
            "metadata_download_bytes": budget["metadata_download_bytes"],
            "error_count": len(errors),
        },
        "errors": errors,
        "pit": {
            "historical_values_reused_from_frozen_r1_only": True,
            "historical_api_capture_metadata_found": sum(x["capture_count"] or 0 for x in observations.values()) > 0,
            "exact_first_publication_time_proven": False,
            "revision_lineage_proven": False,
            "same_day_formal_use_allowed": False,
        },
        "scientific_boundary": {
            "performance": False, "holdout": False, "ranking": False, "selection": False,
            "parameter_search": False, "threshold_search": False, "horizon_search": False,
            "asset_search": False, "variant_search": False, "performance_authorized": False,
            "promotion": False, "live_execution": False,
        },
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
        "interpretation": (
            "CDX captures are archive metadata only. A listed capture identifies a potentially recoverable dated response but does not establish the original observation's first-publication time or revision completeness. No CDX hit is not proof that a response was never public."
        ),
    }
    result["receipt_fingerprint"] = canonical_fingerprint(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.request, args.source_receipt, args.output)
    print(json.dumps({
        "status": result["status"],
        "metadata_request_count": result["summary"]["metadata_request_count"],
        "captured_api_responses_found": result["summary"]["captured_api_responses_found"],
        "metadata_download_bytes": result["summary"]["metadata_download_bytes"],
        "gate_positive": False,
        "performance_authorized": False,
        "live_execution": False,
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
