"""Q188-Q192 historical/PIT census R2.

Discovery/PIT only. This compiler tests whether each candidate's public source
surface exposes the structural fields needed for a historical public-state
reconstruction. It deliberately does not treat current-state APIs as historical
snapshots and never reads market returns.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


UA = "trading-agent-public/Q188-Q192-PIT-census-R2/2"


def fetch(url: str, *, limit: int = 2_000_000) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            return (
                int(getattr(response, "status", 200)),
                {k.lower(): v for k, v in response.headers.items()},
                response.read(limit),
            )
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(limit)
        except Exception:
            body = b""
        return int(exc.code), {k.lower(): v for k, v in exc.headers.items()}, body
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, {}, f"FETCH_ERROR:{type(exc).__name__}:{exc}".encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_probe(url: str, markers: list[str]) -> dict[str, Any]:
    status, headers, body = fetch(url)
    text = body.decode("utf-8", errors="replace")
    lowered = text.lower()
    missing = [m for m in markers if m.lower() not in lowered]
    dates = sorted(set(re.findall(r"20\d{2}-\d{2}-\d{2}", text)))
    return {
        "url": url,
        "http_status": status,
        "markers_present": status == 200 and not missing,
        "missing_markers": missing,
        "date_tokens": dates[:25],
        "content_sha256": digest(body),
        "content_length": len(body),
        "last_modified": headers.get("last-modified"),
        "content_type": headers.get("content-type"),
    }


def json_probe(
    url: str,
    *,
    required_keys: list[str],
) -> dict[str, Any]:
    status, headers, body = fetch(
        url,
        limit=2_500_000,
    )
    result: dict[str, Any] = {
        "url": url,
        "http_status": status,
        "content_sha256": digest(body),
        "content_length": len(body),
        "content_type": headers.get("content-type"),
    }
    if status != 200:
        result["json_parse_ok"] = False
        result["required_keys_present"] = False
        return result

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        result["json_parse_ok"] = False
        result["required_keys_present"] = False
        return result

    result["json_parse_ok"] = True
    if isinstance(payload, list):
        results = payload
    elif isinstance(payload, dict):
        results = payload.get("results", [])
    else:
        results = []
    if isinstance(results, list) and results:
        row = results[0]
        if isinstance(row, dict):
            result["result_keys"] = sorted(row.keys())
            result["required_keys_present"] = all(key in row for key in required_keys)
        else:
            result["result_keys"] = []
            result["required_keys_present"] = False
    else:
        result["result_keys"] = []
        result["required_keys_present"] = False
        result["empty_result_set"] = True
    return result


def q188_probe() -> dict[str, Any]:
    overview = text_probe(
        "https://www.fda.gov/drugs/drug-safety-and-availability/drug-safety-related-labeling-changes-srlc-database-overview-updates-safety-information-fda-approved",
        [
            "January 2016",
            "Search Labeling by Drug Name",
            "Search Labeling by Date Range",
        ],
    )
    landing = text_probe(
        "https://www.fda.gov/safety/medical-product-safety-information/drug-safety-related-labeling-changes",
        [
            "Drug Safety-related Labeling Changes",
            "January 2016",
        ],
    )
    return {
        "overview": overview,
        "landing": landing,
        "historical_source_boundary": "database states since January 2016 are available, but immutable historical snapshots and first-public-observation time are not proven by the current page alone",
        "next_gate": [
            "freeze a dated historical export or archived page state",
            "prove first-public-observation boundary",
            "freeze NDA/BLA/application-to-issuer mapping",
            "reconstruct supplement/correction lineage",
        ],
    }


def q189_probe() -> dict[str, Any]:
    docs = text_probe(
        "https://www.cpsc.gov/Recalls/CPSC-Recalls-Application-Program-Interface-API-Information",
        [
            "machine readable",
            "JSON",
            "Recall API",
        ],
    )
    api = json_probe(
        "https://www.saferproducts.gov/RestWebServices/Recall?ProductName=Toddler&format=json",
        required_keys=[
            "RecallDate",
            "Manufacturers",
        ],
    )
    return {
        "documentation": docs,
        "api_sample": api,
        "historical_source_boundary": "CPSC API is a machine-readable public recall surface with record dates, but the current API does not itself establish immutable historical versions or first-public observation timing",
        "next_gate": [
            "freeze dated recall payloads or authoritative archived captures",
            "prove public publication boundary",
            "freeze product/manufacturer-to-issuer mapping",
            "reconstruct amendment/withdrawal history",
        ],
    }


def q190_probe() -> dict[str, Any]:
    downloads = text_probe(
        "https://echo.epa.gov/tools/data-downloads",
        [
            "updated weekly",
            "Enforcement and Compliance History Online",
            "RCRA Evaluations",
            "weekly run date",
        ],
    )
    about = text_probe(
        "https://echo.epa.gov/resources/echo-data/about-the-data",
        [
            "Date Data Extracted",
            "Expected Next Extract",
            "updated on a weekly schedule",
        ],
    )
    return {
        "downloads": downloads,
        "about": about,
        "historical_source_boundary": "ECHO publishes explicit refresh/extraction dates and weekly download cycles; this is stronger than a current-state-only API but historical candidate prefixes still require a reproducible dated-download inventory",
        "next_gate": [
            "inventory dated historical ECHO download artifacts for a fixed sample",
            "freeze facility-to-issuer mapping",
            "reconstruct enforcement revision lineage",
            "prove the exact refresh boundary used in the decision prefix",
        ],
    }


def q191_probe() -> dict[str, Any]:
    cr_status, cr_headers, cr_body = fetch("https://api.crossref.org/works?rows=1")
    crossref = {
        "url": "https://api.crossref.org/works?rows=1",
        "http_status": cr_status,
        "content_sha256": digest(cr_body),
        "content_length": len(cr_body),
        "content_type": cr_headers.get("content-type"),
    }
    if cr_status == 200:
        try:
            cr = json.loads(cr_body)
            message = cr.get("message", {})
            items = message.get("items", []) if isinstance(message, dict) else []
            crossref["json_parse_ok"] = True
            crossref["items_present"] = isinstance(items, list) and bool(items)
            if items and isinstance(items[0], dict):
                crossref["result_keys"] = sorted(items[0].keys())
                crossref["required_keys_present"] = all(
                    key in items[0] for key in ("title", "published")
                )
            else:
                crossref["result_keys"] = []
                crossref["required_keys_present"] = False
        except json.JSONDecodeError:
            crossref["json_parse_ok"] = False
            crossref["items_present"] = False
            crossref["required_keys_present"] = False
    else:
        crossref["json_parse_ok"] = False
        crossref["items_present"] = False
        crossref["required_keys_present"] = False
    uspto = text_probe(
        "https://www.uspto.gov/learning-and-resources/xml-resources",
        [
            "Patent Grant Full Text Data",
            "XML",
        ],
    )
    return {
        "crossref": crossref,
        "uspto": uspto,
        "historical_source_boundary": "Crossref exposes publication metadata and USPTO exposes historical patent grant XML, but exact public-ordering between science and patent disclosures and frozen patent-paper linkage remain unproven",
        "next_gate": [
            "build a fixed patent-paper linkage census",
            "prove science publication public boundary",
            "prove patent publication/grant boundary",
            "exclude same-day ambiguous ordering",
            "freeze issuer mapping",
        ],
    }


def q192_probe() -> dict[str, Any]:
    docs = text_probe(
        "https://open.fda.gov/apis/drug/drugshortages/",
        [
            "Drug Shortages",
            "initial_posting_date",
            "update_date",
            "change_date",
        ],
    )
    api = json_probe(
        "https://api.fda.gov/drug/shortages.json?limit=1",
        required_keys=[
            "initial_posting_date",
            "update_date",
            "company_name",
        ],
    )
    return {
        "documentation": docs,
        "api_sample": api,
        "historical_source_boundary": "openFDA exposes date/version-like record fields and a public API, but the current endpoint is not an immutable historical snapshot and first-public-observation lineage still requires reconstruction",
        "next_gate": [
            "inventory dated historical shortage exports/captures",
            "prove first-public-observation boundary",
            "freeze manufacturer/product-to-issuer mapping",
            "reconstruct resolution/discontinuation lineage",
        ],
    }


def run(output: Path) -> dict[str, Any]:
    candidate_details = {
        "Q188": q188_probe(),
        "Q189": q189_probe(),
        "Q190": q190_probe(),
        "Q191": q191_probe(),
        "Q192": q192_probe(),
    }
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "receipt_type": "q188_q192_pit_census_r2",
        "wave_id": "Q188-Q192-PIT-CENSUS-R2-2026-10-04",
        "status": "PIT_HISTORICAL_CENSUS_COMPLETED_NO_PERFORMANCE",
        "candidate_results": {
            key: {
                "status": "STRUCTURAL_SOURCE_CLOCK_CENSUS_COMPLETE",
                "details": value,
                "performance_authorized": False,
                "holdout_selection_allowed": False,
                "selection_allowed": False,
                "ranking_allowed": False,
                "parameter_search_allowed": False,
            }
            for key, value in candidate_details.items()
        },
        "cross_wave_checks": {
            "performance_evaluated": False,
            "holdout_used": False,
            "candidate_ranked_by_returns": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
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
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output)
