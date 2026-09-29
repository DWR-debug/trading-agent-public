from __future__ import annotations

import hashlib
import html
import json
import re
import urllib.error
import urllib.request
import zipfile
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "research" / "frontier" / "candidate_inventory_2026_09_29.json"
TIMEOUT = 30
UA = "trading-agent-public/Q096-frontier-audit contact=research"

STATIC_PROBES = [
    ("LSEG_RUSSELL_RECON", "https://www.lseg.com/en/ftse-russell/russell-reconstitution", "html", ["reconstitution", "Russell"]),
    ("CBOE_VIX_HISTORY", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv", "csv", ["DATE,OPEN,HIGH,LOW,CLOSE"]),
    ("SEC_FTD_HISTORY", "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data", "html", ["February 2004", "August 2026"]),
    ("FINRA_SHORT_INTEREST", "https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest", "html", ["Short Interest Reporting", "2026 Short Interest Reporting Dates"]),
]

SEC_SAMPLE_CIKS = {
    "MSFT": "0000789019",
    "AAPL": "0000320193",
    # Existing Q075 sample manager CIK; used only as a source-contract probe.
    "SEC_13F_SAMPLE": "0001067983",
    # Current public EDGAR examples verified on 2026-09-29.
    "SEC_13D_G_SAMPLE": "0001490281",
    "SEC_FORM144_SAMPLE": "0001326801",
}


def get(url: str) -> tuple[int, bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return int(r.status), r.read(), r.headers.get("content-type")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), None


def fp(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def probe_static(item):
    ident, url, kind, checks = item
    status, data, ctype = get(url)
    row = {
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
        row["reason"] = f"HTTP_{status}"
        return row
    text = data.decode("utf-8", "replace")
    if kind == "html":
        row["checks"] = {c: c.lower() in text.lower() for c in checks}
    elif kind == "csv":
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        row["checks"] = {
            "has_header": bool(lines) and lines[0] == checks[0],
            "has_rows": len(lines) > 1,
            "five_columns": len(lines[1].split(",")) == 5 if len(lines) > 1 else False,
        }
    row["status"] = "VERIFIABLE" if row["checks"] and all(row["checks"].values()) else "SCHEMA_MISMATCH"
    return row


def json_get(url: str) -> tuple[int, dict | None, str | None]:
    status, data, ctype = get(url)
    if status != 200:
        return status, None, ctype
    try:
        return status, json.loads(data), ctype
    except json.JSONDecodeError:
        return status, None, ctype


def recent_filing_rows(payload: dict) -> list[dict]:
    recent = payload.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    acc = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", [])
    acceptance = recent.get("acceptanceDateTime", [])
    n = min(len(forms), len(dates), len(acc))
    return [
        {
            "form": forms[i],
            "filingDate": dates[i],
            "accessionNumber": acc[i],
            "primaryDocument": docs[i] if i < len(docs) else None,
            "acceptanceDateTime": acceptance[i] if i < len(acceptance) else None,
        }
        for i in range(n)
    ]


def filing_url(cik: str, accession: str, primary_document: str) -> str:
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession.replace('-', '')}/{primary_document}"
    )


def sec_submission_probe(label: str, cik: str, target_forms: set[str], text_checks: dict[str, list[str]] | None = None) -> dict:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    status, payload, ctype = json_get(url)
    row = {
        "id": f"SEC_SUBMISSIONS_{label}",
        "url": url,
        "http_status": status,
        "content_type": ctype,
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200 or payload is None:
        row["reason"] = f"HTTP_{status}" if status != 200 else "INVALID_JSON"
        return row

    rows = recent_filing_rows(payload)
    matched = [x for x in rows if x["form"] in target_forms]
    older_files = payload.get("filings", {}).get("files", [])
    row["checks"] = {
        "valid_json": True,
        "has_recent_filings": bool(rows),
        "has_accession_numbers": bool(rows) and all(
            x["accessionNumber"] for x in rows[: min(25, len(rows))]
        ),
        "target_forms_present": bool(matched),
        "historical_extension_metadata_present": bool(older_files) or len(rows) >= 1000,
    }
    row["submission_acceptance_field_present"] = any(
        x["acceptanceDateTime"] for x in matched[: min(10, len(matched))]
    )
    if not text_checks:
        row["checks"]["submission_acceptance_field_present"] = row["submission_acceptance_field_present"]
    row["target_form_counts"] = {form: sum(x["form"] == form for x in rows) for form in sorted(target_forms)}
    row["recent_range"] = {
        "min_filing_date": min((x["filingDate"] for x in rows), default=None),
        "max_filing_date": max((x["filingDate"] for x in rows), default=None),
    }

    if text_checks:
        for form, checks in text_checks.items():
            candidate = next((x for x in matched if x["form"] == form and x["primaryDocument"]), None)
            if not candidate:
                row["checks"][f"{form}_primary_document_found"] = False
                continue
            filing = filing_url(cik, candidate["accessionNumber"], candidate["primaryDocument"])
            s, data, c = get(filing)
            filing_text = data.decode("utf-8", "replace") if s == 200 else ""
            normalized_text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", filing_text))).strip()
            header = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                f"{candidate['accessionNumber'].replace('-', '')}/"
                f"{candidate['accessionNumber']}-index-headers.html"
            )
            hs, hdata, hc = get(header)
            header_text = hdata.decode("utf-8", "replace") if hs == 200 else ""
            row.setdefault("header_probes", []).append({
                "form": form,
                "url": header,
                "http_status": hs,
                "response_sha256": fp(hdata),
                "checks": {
                    "acceptance_datetime": "<ACCEPTANCE-DATETIME>" in header_text.upper(),
                    "accession_number": candidate["accessionNumber"] in header_text,
                    "conformed_submission_type": form.upper() in header_text.upper(),
                },
            })
            row["text_probe"] = {
                "form": form,
                "url": filing,
                "http_status": s,
                "response_sha256": fp(data),
                "checks": {check: check.lower() in normalized_text.lower() for check in checks},
            }
            row["checks"][f"{form}_primary_document_found"] = s == 200
            row["checks"][f"{form}_header_found"] = hs == 200
            row["checks"][f"{form}_acceptance_datetime"] = hs == 200 and "<ACCEPTANCE-DATETIME>" in header_text.upper()
            row["checks"].update({f"{form}_{check}": check.lower() in normalized_text.lower() for check in checks})

    row["status"] = "VERIFIABLE" if row["checks"] and all(row["checks"].values()) else "SCHEMA_MISMATCH"
    return row


def companyfacts_probe(cik: str) -> dict:
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    status, payload, ctype = json_get(url)
    row = {
        "id": f"SEC_COMPANYFACTS_{cik}",
        "url": url,
        "http_status": status,
        "content_type": ctype,
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200 or payload is None:
        row["reason"] = f"HTTP_{status}" if status != 200 else "INVALID_JSON"
        return row
    dei = payload.get("facts", {}).get("dei", {})
    shares = dei.get("EntityCommonStockSharesOutstanding", {})
    units = shares.get("units", {})
    row["checks"] = {
        "valid_json": True,
        "has_entity_name": bool(payload.get("entityName")),
        "has_dei_namespace": bool(dei),
        "has_shares_outstanding_fact": bool(units),
        "has_instant_values": any(bool(v) for v in units.values()),
    }
    row["status"] = "VERIFIABLE" if all(row["checks"].values()) else "SCHEMA_MISMATCH"
    return row


def gdelt_probe() -> dict:
    probe_date = date.today() - timedelta(days=1)
    stamp = probe_date.strftime("%Y%m%d")
    url = f"https://data.gdeltproject.org/events/{stamp}.export.CSV.zip"
    status, data, ctype = get(url)
    row = {
        "id": "GDELT_DAILY_ARCHIVE",
        "url": url,
        "probe_date": stamp,
        "http_status": status,
        "content_type": ctype,
        "response_bytes": len(data),
        "response_sha256": fp(data),
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200:
        row["reason"] = f"HTTP_{status}"
        return row
    try:
        with zipfile.ZipFile(BytesIO(data)) as z:
            names = z.namelist()
            row["checks"] = {
                "valid_zip": bool(names),
                "contains_csv": any(n.lower().endswith(".csv") for n in names),
            }
            row["zip_members"] = names[:5]
    except zipfile.BadZipFile:
        row["checks"] = {"valid_zip": False}
    row["status"] = "VERIFIABLE" if all(row["checks"].values()) else "SCHEMA_MISMATCH"
    return row


def candidate_gate_matrix(candidates):
    rows = []
    for code, name, source, existing_state in candidates:
        source_l = source.lower()
        if "option" in source_l:
            source_state = "BLOCKED_BY_ZERO_PAID_DATA_POLICY"
            archive_state = "NO_FREE_COMPLETE_HISTORICAL_OPTION_SOURCE_VERIFIED"
        elif any(k in source_l for k in (
            "sec form 4",
            "sec 13f",
            "sec 8-k",
            "sec filing",
            "shares outstanding",
            "sec +",
            "fails-to-deliver",
            "short interest",
            "schedule 13d",
            "schedule 13g",
            "form 144",
        )):

            source_state = "PUBLIC_SOURCE_CHANNEL_CONFIRMED"
            archive_state = "HISTORICAL_ARCHIVE_PIT_AUDIT_PENDING"
        elif "gdelt" in source_l or "public news" in source_l:
            source_state = "PUBLIC_SOURCE_CHANNEL_CONFIRMED"
            archive_state = "HISTORICAL_ENTITY_MAPPING_AND_PIT_PENDING"
        elif "scheduled benchmark" in source_l:
            source_state = "PUBLIC_SOURCE_CHANNEL_CONFIRMED"
            archive_state = "HISTORICAL_ANNOUNCEMENT_ARCHIVE_AND_MAPPING_PENDING"
        elif any(k in source_l for k in ("alfred", "cftc", "wikimedia", "finra", "cboe")):
            source_state = "PUBLIC_SOURCE_CHANNEL_CONFIRMED"
            archive_state = "HISTORICAL_COVERAGE_ALREADY_FEASIBLE_OR_ALREADY_PROBED"
        elif any(k in source_l for k in ("ohlcv", "daily close", "market +", "calendar")):
            source_state = "CANONICAL_PROJECT_DATA_OR_DETERMINISTIC_INPUT"
            archive_state = "NO_NEW_EXTERNAL_ARCHIVE_GATE"
        else:
            source_state = "DESIGN_REVIEW_REQUIRED"
            archive_state = "EXPLICIT_SOURCE_CONTRACT_REQUIRED"
        pit_state = "MACHINE_FEASIBILITY_PRESENT" if existing_state in {
            "MACHINE_FEASIBILITY_IMPLEMENTED",
            "FEASIBILITY_CHECK_COMPLETED_NO_PERFORMANCE",
        } else "PIT_CONTRACT_REVIEW_REQUIRED"
        rows.append({
            "candidate": code,
            "name": name,
            "source": source,
            "existing_state": existing_state,
            "source_state": source_state,
            "pit_state": pit_state,
            "archive_state": archive_state,
            "performance_authorized": False,
        })
    return rows


def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    candidates = [list(row) for row in inventory["candidates"]]

    live_probes = [
        *[probe_static(item) for item in STATIC_PROBES],
        sec_submission_probe(
            "MSFT_10K",
            SEC_SAMPLE_CIKS["MSFT"],
            {"10-K"},
            {
                "10-K": ["Item 1A", "Risk Factors"],
            },
        ),
        sec_submission_probe(
            "AAPL_10Q",
            SEC_SAMPLE_CIKS["AAPL"],
            {"10-Q"},
            {
                "10-Q": ["Management's Discussion and Analysis", "Item 2"],
            },
        ),
        sec_submission_probe("FORM4_SAMPLE", SEC_SAMPLE_CIKS["MSFT"], {"4", "4/A"}),
        sec_submission_probe("FORM13F_SAMPLE", SEC_SAMPLE_CIKS["SEC_13F_SAMPLE"], {"13F-HR", "13F-HR/A"}),
        sec_submission_probe(
            "BENEFICIAL_OWNERSHIP_SAMPLE",
            SEC_SAMPLE_CIKS["SEC_13D_G_SAMPLE"],
            {"SCHEDULE 13D", "SCHEDULE 13D/A", "SCHEDULE 13G", "SCHEDULE 13G/A"},
        ),
        sec_submission_probe("FORM144_SAMPLE", SEC_SAMPLE_CIKS["SEC_FORM144_SAMPLE"], {"144"}),
        companyfacts_probe(SEC_SAMPLE_CIKS["MSFT"]),
        gdelt_probe(),
    ]

    result = {
        "schema_version": "1.1",
        "task_id": "Q-2026-09-29-096-FRONTIER-SOURCE-PIT-AUDIT",
        "status": "SOURCE_AND_PIT_FEASIBILITY_ONLY",
        "inventory_count": len(candidates),
        "candidate_gate_matrix": candidate_gate_matrix(candidates),
        "live_source_probes": live_probes,
        "governance": {
            "performance_evaluation": False,
            "holdout_evaluation": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    out = ROOT / "research" / "runs" / "q096_frontier_source_pit_audit" / "result.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Q096_STATUS:", result["status"])
    print("Q096_INVENTORY_COUNT:", len(candidates))
    for row in live_probes:
        print(row["id"], row["status"], row.get("reason", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
