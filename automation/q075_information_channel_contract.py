from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

TIMEOUT = 30
UA = "trading-agent-public/Q075-information-channel-feasibility contact=research"

PROBES = [
    ("I1_FINRA", "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files", "html", ["Daily Short Sale Volume Files"]),
    ("I2_SEC_FORM4", "https://www.sec.gov/Archives/edgar/data/1111741/000119312526385370/0001193125-26-385370-index-headers.html", "html", ["<ACCEPTANCE-DATETIME>", "CONFORMED SUBMISSION TYPE:"]),
    ("I3_ALFRED", "https://alfred.stlouisfed.org/series/downloaddata?seid=M1SL", "html", ["vintage dates"]),
    ("I4_CFTC", "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm", "html", ["2025", "Disaggregated Futures Only Reports"]),
    ("I5_WIKIMEDIA", "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Apple/daily/2026092300/2026092400", "json", []),
    ("I6_GDELT", "https://data.gdeltproject.org/events/20260924.export.CSV.zip", "zip", []),
    ("I7_SEC_13F_HEADER", "https://www.sec.gov/Archives/edgar/data/1418814/000141881426000002/0001418814-26-000002-index-headers.html", "html", ["<ACCEPTANCE-DATETIME>", "13F-HR"]),
    ("I8_SEC_8K_HEADER", "https://www.sec.gov/Archives/edgar/data/1130464/000119312526226896/0001193125-26-226896-index-headers.html", "html", ["<ACCEPTANCE-DATETIME>", "8-K"]),
    ("I9_CBOE_VIX", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv", "csv", ["DATE,OPEN,HIGH,LOW,CLOSE"]),
    ("I9_CBOE_VVIX", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv", "csv_vvix", ["DATE,VVIX"]),
    ("SEC_SUBMISSIONS", "https://data.sec.gov/submissions/CIK0000320193.json", "json", []),
    ("SEC_COMPANYFACTS", "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json", "json", []),
]


def get(url: str) -> tuple[int, bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return int(r.status), r.read(), r.headers.get("content-type")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), None


def fp(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def probe(item):
    ident, url, kind, checks = item
    status, data, ctype = get(url)
    out = {
        "id": ident,
        "url": url,
        "http_status": status,
        "content_type": ctype,
        "response_bytes": len(data),
        "response_sha256": fp(data),
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200:
        out["reason"] = f"HTTP_{status}"
        return out

    text = data.decode("utf-8", "replace")
    if kind == "html":
        out["checks"] = {c: c.lower() in text.lower() for c in checks}
    elif kind == "json":
        try:
            payload = json.loads(data)
            out["checks"] = {"valid_json": True}
            if ident == "I5_WIKIMEDIA":
                items = payload.get("items", [])
                out["checks"].update({
                    "has_items": bool(items),
                    "has_timestamp": bool(items and items[0].get("timestamp")),
                    "has_views": bool(items and "views" in items[0]),
                })
            elif ident == "SEC_SUBMISSIONS":
                out["checks"].update({
                    "has_name": bool(payload.get("name")),
                    "has_tickers": bool(payload.get("tickers")),
                    "has_recent_filings": bool(payload.get("filings", {}).get("recent")),
                })
            elif ident == "SEC_COMPANYFACTS":
                out["checks"].update({
                    "has_entity_name": bool(payload.get("entityName")),
                    "has_facts": isinstance(payload.get("facts"), dict) and bool(payload["facts"]),
                })
        except json.JSONDecodeError:
            out["checks"] = {"valid_json": False}
    elif kind == "zip":
        try:
            with zipfile.ZipFile(BytesIO(data)) as z:
                names = z.namelist()
                out["checks"] = {
                    "valid_zip": bool(names),
                    "contains_csv": any(n.lower().endswith(".csv") for n in names),
                }
                out["zip_members"] = names[:5]
        except zipfile.BadZipFile:
            out["checks"] = {"valid_zip": False}
    elif kind == "csv":
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        out["checks"] = {
            "has_header": bool(lines) and lines[0] == checks[0],
            "has_rows": len(lines) > 1,
            "five_columns": len(lines[1].split(",")) == 5 if len(lines) > 1 else False,
        }
        out["sample_first_data_row"] = lines[1] if len(lines) > 1 else None
    elif kind == "csv_vvix":
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        out["checks"] = {
            "has_header": bool(lines) and lines[0] == checks[0],
            "has_rows": len(lines) > 1,
            "two_columns": len(lines[1].split(",")) == 2 if len(lines) > 1 else False,
        }
        out["sample_first_data_row"] = lines[1] if len(lines) > 1 else None

    out["status"] = "VERIFIABLE" if out["checks"] and all(out["checks"].values()) else "SCHEMA_MISMATCH"
    return out


def main():
    results = [probe(x) for x in PROBES]
    summary = {
        "schema_version": "1.0",
        "task_id": "Q-2026-09-28-075-INFORMATION-CHANNEL-CONTRACT",
        "status": "SOURCE_CONTRACT_FEASIBILITY_ONLY",
        "results": results,
        "selection_used": False,
        "performance_evaluation": False,
        "oos_evaluation": False,
        "holdout_used_for_selection": False,
        "governance": {
            "no_parameter_search": True,
            "no_asset_search": True,
            "no_family_ranking": True,
            "coverage_before_pit": True,
            "pit_before_performance": True,
            "fresh_disjoint_validation_required": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    out = Path("research/runs/q075_information_channel_contract/result.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Q075_STATUS:", summary["status"])
    for row in results:
        print(row["id"], row["status"], row.get("reason", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
