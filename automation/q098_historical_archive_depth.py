from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 30
UA = "trading-agent-public/Q098-historical-archive-depth contact=research"

SAMPLES = {
    "MSFT": ("0000789019", {"10-K", "10-Q", "4", "4/A"}),
    "13F_MANAGER": ("0001067983", {"13F-HR", "13F-HR/A"}),
    "13D_G": ("0001490281", {"SCHEDULE 13D", "SCHEDULE 13D/A", "SCHEDULE 13G", "SCHEDULE 13G/A"}),
    "FORM144": ("0001326801", {"144"}),
}

GDELT_DATES = ("20130401", "20190101", "20210101")

HISTORICAL_EDGAR_ANCHORS = {
    "13D_G": {
        "url": "https://www.sec.gov/Archives/edgar/data/1020066/000102006611000014/0001020066-11-000014-index.html",
        "forms": {"SC 13G", "SC 13G/A", "SCHEDULE 13G", "SCHEDULE 13G/A"},
        "study_date": "2011-06-09",
    },
    "FORM144": {
        "url": "https://www.sec.gov/Archives/edgar/data/1326801/000192109423000806/0001921094-23-000806-index.htm",
        "forms": {"144"},
        "study_date": "2023-11-06",
    },
}


def get(url: str) -> tuple[int, bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return int(r.status), r.read(), r.headers.get("content-type")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), None


def head(url: str) -> tuple[int, int | None, str | None]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            length = r.headers.get("content-length")
            return int(r.status), int(length) if length and length.isdigit() else None, r.headers.get("content-type")
    except urllib.error.HTTPError as exc:
        return int(exc.code), None, None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def recent_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    recent = payload.get("filings", {}).get("recent", {})
    keys = {k: recent.get(k, []) for k in ("form", "filingDate", "accessionNumber", "acceptanceDateTime", "primaryDocument")}
    n = min(len(keys["form"]), len(keys["filingDate"]), len(keys["accessionNumber"]))
    return [
        {
            "form": keys["form"][i],
            "filingDate": keys["filingDate"][i],
            "accessionNumber": keys["accessionNumber"][i],
            "acceptanceDateTime": keys["acceptanceDateTime"][i] if i < len(keys["acceptanceDateTime"]) else None,
            "primaryDocument": keys["primaryDocument"][i] if i < len(keys["primaryDocument"]) else None,
        }
        for i in range(n)
    ]

def submission_rows(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        nested = payload.get("filings", {}).get("recent", {})
        if isinstance(nested, dict) and nested.get("form") is not None:
            return recent_rows(payload)
        if all(k in payload for k in ("form", "filingDate", "accessionNumber")):
            forms = payload.get("form", [])
            dates = payload.get("filingDate", [])
            acc = payload.get("accessionNumber", [])
            acceptance = payload.get("acceptanceDateTime", [])
            docs = payload.get("primaryDocument", [])
            n = min(len(forms), len(dates), len(acc))
            return [
                {
                    "form": forms[i],
                    "filingDate": dates[i],
                    "accessionNumber": acc[i],
                    "acceptanceDateTime": acceptance[i] if i < len(acceptance) else None,
                    "primaryDocument": docs[i] if i < len(docs) else None,
                }
                for i in range(n)
            ]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def submission_archive_probe(label: str, cik: str, target_forms: set[str]) -> dict[str, Any]:
    base = f"https://data.sec.gov/submissions/CIK{cik}.json"
    status, data, ctype = get(base)
    result: dict[str, Any] = {
        "id": f"SEC_ARCHIVE_{label}",
        "url": base,
        "http_status": status,
        "content_type": ctype,
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200:
        result["reason"] = f"HTTP_{status}"
        return result
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        result["reason"] = "INVALID_JSON"
        return result

    files = payload.get("filings", {}).get("files", [])
    rows = recent_rows(payload)
    matching_recent = [r for r in rows if r["form"] in target_forms]
    result["checks"]["valid_json"] = True
    result["checks"]["recent_target_form_present"] = bool(matching_recent)
    result["checks"]["extension_file_metadata_present"] = bool(files)
    result["extension_count"] = len(files)
    result["extension_samples"] = files[:5]

    if not files:
        result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
        return result

    # Prefer the oldest extension by filingFrom for an actual historical-depth probe.
    def file_from(item: dict[str, Any]) -> str:
        return str(item.get("filingFrom") or item.get("from") or "")

    selected = sorted(files, key=file_from)[0]
    name = selected.get("name")
    if not name:
        result["checks"]["extension_name_present"] = False
    else:
        result["checks"]["extension_name_present"] = True
        url = f"https://data.sec.gov/submissions/{name}"
        s, body, ct = get(url)
        result["oldest_extension"] = {
            "name": name,
            "filingFrom": selected.get("filingFrom"),
            "filingTo": selected.get("filingTo"),
            "url": url,
            "http_status": s,
            "content_type": ct,
            "response_sha256": sha256(body),
        }
        if s == 200:
            try:
                old_payload = json.loads(body)
                old_rows = submission_rows(old_payload)
                if isinstance(old_rows, list):
                    forms = [r.get("form") for r in old_rows if isinstance(r, dict)]
                    result["oldest_extension"]["target_form_hits"] = sorted(set(forms).intersection(target_forms))
                    result["oldest_extension"]["row_count"] = len(old_rows)
                    result["checks"]["oldest_extension_readable"] = True
                    result["checks"]["oldest_extension_contains_target_form"] = bool(
                        set(forms).intersection(target_forms)
                    )
                else:
                    result["checks"]["oldest_extension_readable"] = False
                    result["checks"]["oldest_extension_contains_target_form"] = False
            except json.JSONDecodeError:
                result["checks"]["oldest_extension_readable"] = False
                result["checks"]["oldest_extension_contains_target_form"] = False
        else:
            result["checks"]["oldest_extension_readable"] = False
            result["checks"]["oldest_extension_contains_target_form"] = False

    result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
    return result


def gdelt_archive_probe() -> dict[str, Any]:
    rows = []
    for stamp in GDELT_DATES + ((date.today() - timedelta(days=1)).strftime("%Y%m%d"),):
        url = f"https://data.gdeltproject.org/events/{stamp}.export.CSV.zip"
        s, length, ct = head(url)
        rows.append({
            "date": stamp,
            "url": url,
            "http_status": s,
            "content_length": length,
            "content_type": ct,
            "exists": s == 200,
        })
    return {
        "id": "GDELT_HISTORICAL_DEPTH",
        "status": "VERIFIABLE" if all(r["exists"] for r in rows) else "PARTIAL",
        "checks": {"all_requested_archives_exist": all(r["exists"] for r in rows)},
        "rows": rows,
    }



def historical_edgar_anchor_probe(label: str, spec: dict[str, Any]) -> dict[str, Any]:
    status, body, ct = get(spec["url"])
    text = body.decode("utf-8", "replace") if status == 200 else ""
    upper = text.upper()
    result = {
        "id": f"SEC_HISTORICAL_ANCHOR_{label}",
        "url": spec["url"],
        "study_date": spec["study_date"],
        "http_status": status,
        "content_type": ct,
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200:
        result["reason"] = f"HTTP_{status}"
        return result
    result["checks"] = {
        "page_readable": True,
        "form_marker_present": any(form.upper() in upper for form in spec["forms"]),
        "accepted_timestamp_present": "ACCEPTED" in upper and "20" in text,
        "accession_marker_present": re.search(r"000\\d{6,}-\\d{2}-\\d{6}", text) is not None,
    }
    result["response_sha256"] = sha256(body)
    result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
    return result


def sec_ftd_archive_probe() -> dict[str, Any]:
    page = "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data"
    status, body, ct = get(page)
    result: dict[str, Any] = {
        "id": "SEC_FTD_HISTORICAL_DEPTH",
        "url": page,
        "http_status": status,
        "content_type": ct,
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200:
        result["reason"] = f"HTTP_{status}"
        return result
    text = body.decode("utf-8", "replace")
    hrefs = re.findall(r"""href=["']([^"']+)["']""", text, flags=re.I)
    archives = [h for h in hrefs if any(k in h.lower() for k in (".zip", "fails-to-deliver", "ftd"))]
    years = sorted(set(re.findall(r"\b(2004|2008|2009|2024|2025|2026)\b", text)))
    result["checks"] = {
        "page_readable": True,
        "download_links_present": bool(archives),
        "historical_year_markers_present": len(years) >= 4,
    }
    result["historical_year_markers"] = years
    result["download_link_samples"] = archives[:12]
    result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
    return result


def main() -> int:
    probes = [
        submission_archive_probe(label, cik, forms)
        for label, (cik, forms) in SAMPLES.items()
    ]
    probes.extend(
        historical_edgar_anchor_probe(label, spec)
        for label, spec in HISTORICAL_EDGAR_ANCHORS.items()
    )
    probes.extend([gdelt_archive_probe(), sec_ftd_archive_probe()])
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-09-29-098-HISTORICAL-ARCHIVE-DEPTH",
        "status": "HISTORICAL_SOURCE_DEPTH_ONLY",
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "candidate_ranking": False,
        "candidate_selection": False,
        "parameter_search": False,
        "performance_authorized": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "probes": probes,
    }
    out = ROOT / "research" / "runs" / "q098_historical_archive_depth" / "result.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q098_STATUS:", result["status"])
    for row in probes:
        print(row["id"], row["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
