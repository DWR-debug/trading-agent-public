from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path


TIMEOUT = 25
USER_AGENT = "trading-agent-public/Q071 source-feasibility research contact=research"

PROBES = [
    {
        "id": "I1",
        "family": "FINRA_REG_SHO_SHORT_SALE_FLOW_SHOCK",
        "kind": "html",
        "url": "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files",
        "checks": ["Daily Short Sale Volume Files", "Consolidated TRF/ADF Daily Short Sale Volume Files"],
        "pit_semantics": "FINRA states files are posted no later than 18:00 ET on the trade date.",
    },
    {
        "id": "I2",
        "family": "SEC_FORM4_INSIDER_FLOW",
        "kind": "sec_header",
        "url": "https://www.sec.gov/Archives/edgar/data/1111741/000119312526385370/0001193125-26-385370-index-headers.html",
        "checks": ["<ACCEPTANCE-DATETIME>", "CONFORMED SUBMISSION TYPE:"],
        "pit_semantics": "EDGAR acceptance timestamp is the primary public-availability anchor.",
    },
    {
        "id": "I3",
        "family": "ALFRED_MACRO_VINTAGE_SURPRISE_STATE",
        "kind": "html",
        "url": "https://alfred.stlouisfed.org/series/downloaddata?seid=M1SL",
        "checks": ["vintage dates", "actually existed on those past dates"],
        "pit_semantics": "Vintage date explicitly represents data as it existed on that past date.",
    },
    {
        "id": "I4",
        "family": "CFTC_COT_CROWDING_DECROWDING",
        "kind": "html",
        "url": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm",
        "checks": ["2026", "2025", "Disaggregated Futures Only Reports"],
        "pit_semantics": "Historical files exist by report year; report date must not be confused with release date.",
    },
    {
        "id": "I5",
        "family": "WIKIMEDIA_FIRM_ATTENTION_SHOCK",
        "kind": "json",
        "url": "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Apple/daily/2026092300/2026092400",
        "checks": [],
        "pit_semantics": "Only completed daily observations are eligible; use next-session action.",
    },
    {
        "id": "I6",
        "family": "GDELT_MEDIA_TONE_ATTENTION_SHOCK",
        "kind": "zip",
        "url": "https://data.gdeltproject.org/events/20260924.export.CSV.zip",
        "checks": [],
        "pit_semantics": "Archived daily export is the immutable source object; later versions must be fingerprinted.",
    },
]


def _fetch(url: str) -> tuple[int, bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            return int(response.status), response.read(), response.headers.get("content-type")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), None
    except Exception as exc:
        raise RuntimeError(f"{type(exc).__name__}: {exc}") from exc


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _probe(item: dict) -> dict:
    status, data, content_type = _fetch(item["url"])
    text = data.decode("utf-8", "replace")
    result = {
        "id": item["id"],
        "family": item["family"],
        "url": item["url"],
        "http_status": status,
        "content_type": content_type,
        "response_bytes": len(data),
        "response_sha256": _sha256(data),
        "pit_semantics": item["pit_semantics"],
        "status": "BLOCKED",
        "checks": {},
    }
    if status != 200:
        result["reason"] = f"HTTP_{status}"
        return result
    if item["kind"] == "html" or item["kind"] == "sec_header":
        result["checks"] = {needle: needle.lower() in text.lower() for needle in item["checks"]}
        result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
        if result["status"] != "VERIFIABLE":
            result["reason"] = "required text markers missing"
    elif item["kind"] == "json":
        try:
            payload = json.loads(data)
            items = payload.get("items", [])
            result["item_count"] = len(items)
            result["checks"] = {
                "has_items": bool(items),
                "has_timestamp": bool(items and items[0].get("timestamp")),
                "has_views": bool(items and "views" in items[0]),
            }
            result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
        except json.JSONDecodeError:
            result["status"] = "SCHEMA_MISMATCH"
            result["reason"] = "invalid JSON"
    elif item["kind"] == "zip":
        try:
            with zipfile.ZipFile(BytesIO(data)) as zf:
                names = zf.namelist()
                result["zip_members"] = names[:5]
                result["checks"] = {
                    "zip_valid": bool(names),
                    "contains_csv": any(name.lower().endswith(".csv") for name in names),
                }
                result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
        except zipfile.BadZipFile:
            result["status"] = "SCHEMA_MISMATCH"
            result["reason"] = "invalid ZIP archive"
    return result


def main() -> int:
    results = []
    for probe in PROBES:
        try:
            results.append(_probe(probe))
        except Exception as exc:
            results.append(
                {
                    "id": probe["id"],
                    "family": probe["family"],
                    "url": probe["url"],
                    "status": "ACCESS_ERROR",
                    "reason": f"{type(exc).__name__}: {exc}",
                }
            )

    summary = {
        "schema_version": "1.0",
        "task_id": "Q-2026-09-28-071-INFORMATION-SOURCE-FEASIBILITY",
        "status": "SOURCE_FEASIBILITY_ONLY",
        "selection_used": False,
        "performance_evaluation": False,
        "holdout_used_for_selection": False,
        "results": results,
        "governance": {
            "performance_trial_authorized": False,
            "no_parameter_search": True,
            "no_asset_search": True,
            "no_family_ranking": True,
            "fresh_disjoint_validation_required": True,
            "coverage_before_pit": True,
            "pit_before_performance": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    out = Path("research/runs/q071_source_feasibility/source_feasibility.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Q071_STATUS:", summary["status"])
    for item in results:
        print(item["id"], item["status"], item.get("reason", ""))
    # Source availability is a diagnostic result; individual blocked sources do not invalidate the sweep itself.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
