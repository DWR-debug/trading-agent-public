"""Q232 SEC confidential-treatment order source/PIT feasibility census.

Discovery/source only. No prices, returns, holdouts, ranking, tuning,
promotion or live execution.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

START = date(2015, 1, 1)
END = date(2025, 12, 31)
REQUEST_GAP_SECONDS = 0.35
UA = "DWR-debug-trading-agent-public/Q232-sec-ct-source-census/1"
TRANSPORTS = ("form.zip", "form.gz", "form.idx")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def quarter_list() -> list[tuple[int, int]]:
    return [(year, quarter) for year in range(START.year, END.year + 1) for quarter in range(1, 5)]


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/plain,application/zip,application/gzip,*/*",
            "Accept-Encoding": "gzip, deflate",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"SEC_TRANSPORT_ERROR:{url}:{exc}") from exc


def fetch_form_index(year: int, quarter: int) -> tuple[bytes, dict[str, object]]:
    attempts: list[dict[str, object]] = []
    for transport in TRANSPORTS:
        url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/{transport}"
        time.sleep(REQUEST_GAP_SECONDS)
        status, body = fetch(url)
        attempts.append({"transport": transport, "url": url, "status": status})
        if status != 200:
            continue
        if transport == "form.zip":
            try:
                with zipfile.ZipFile(io.BytesIO(body)) as archive:
                    names = [name for name in archive.namelist() if name.lower() == "form.idx" or name.lower().endswith("/form.idx")]
                    if len(names) != 1:
                        raise RuntimeError(f"SEC_FORM_ZIP_UNEXPECTED_MEMBERS:{names}")
                    logical = archive.read(names[0])
            except (zipfile.BadZipFile, OSError, KeyError) as exc:
                raise RuntimeError(f"SEC_FORM_ZIP_INVALID:{year}:QTR{quarter}:{exc}") from exc
        elif transport == "form.gz":
            try:
                logical = gzip.decompress(body)
            except OSError as exc:
                raise RuntimeError(f"SEC_FORM_GZIP_INVALID:{year}:QTR{quarter}:{exc}") from exc
        else:
            logical = body
        return logical, {
            "transport": transport,
            "transport_url": url,
            "transport_sha256": sha256_bytes(body),
            "logical_sha256": sha256_bytes(logical),
            "raw_bytes": len(body),
            "logical_bytes": len(logical),
            "attempts": attempts,
        }
    raise RuntimeError(
        "SEC_FORM_INDEX_ALL_TRANSPORTS_BLOCKED:"
        + json.dumps(attempts, sort_keys=True, separators=(",", ":"))
    )


def parse_index(body: bytes) -> list[dict[str, str]]:
    pattern = re.compile(
        r"^\s*(?P<form>CT ORDER)\s+"
        r"(?P<company>.*?)\s+"
        r"(?P<cik>\d{1,10})\s+"
        r"(?P<filed>\d{8}|\d{4}-\d{2}-\d{2})\s+"
        r"(?P<filename>edgar/data/\S+)\s*$",
        re.IGNORECASE,
    )
    rows: list[dict[str, str]] = []
    for raw in body.decode("latin-1").splitlines():
        match = pattern.match(raw.rstrip("\r\n"))
        if not match:
            continue
        data = match.groupdict()
        filed = data["filed"]
        if len(filed) == 8 and "-" not in filed:
            filed = f"{filed[:4]}-{filed[4:6]}-{filed[6:8]}"
        try:
            filed_date = date.fromisoformat(filed)
        except ValueError:
            continue
        cik = data["cik"]
        filename = data["filename"]
        if not (START <= filed_date <= END):
            continue
        if not cik.isdigit() or not re.fullmatch(r"edgar/data/\d{1,10}/\d{18}/\S+", filename):
            continue
        rows.append({
            "cik": cik.zfill(10),
            "company_name": data["company"].strip(),
            "form": "CT ORDER",
            "filed_date": filed,
            "filename": filename,
        })
    return rows


def accession_from_filename(filename: str) -> str:
    match = re.search(r"/(\d{18})/", filename)
    if not match:
        match = re.search(r"/(\d{10}-\d{2}-\d{6})", filename)
        if not match:
            raise ValueError(f"ACCESSION_NOT_FOUND:{filename}")
        return match.group(1)
    raw = match.group(1)
    return f"{raw[:10]}-{raw[10:12]}-{raw[12:]}"


def archive_base(filename: str) -> tuple[str, str]:
    parts = filename.split("/")
    if len(parts) < 4 or parts[0] != "edgar" or parts[1] != "data":
        raise ValueError(f"INVALID_ARCHIVE_FILENAME:{filename}")
    return str(int(parts[2])), accession_from_filename(filename)


def header_url(filename: str) -> str:
    cik, accession = archive_base(filename)
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{accession}-index-headers.html"


def detail_url(filename: str) -> str:
    cik, accession = archive_base(filename)
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{accession}-index.html"


def submission_text_url(filename: str) -> str:
    cik, accession = archive_base(filename)
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{accession.replace('-', '')}.txt"


def extract_tag(text: str, tag: str) -> str | None:
    match = re.search(rf"<{re.escape(tag)}>\s*([^<\r\n]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def check_sample(row: dict[str, str]) -> dict[str, object]:
    hurl = header_url(row["filename"])
    time.sleep(REQUEST_GAP_SECONDS)
    hstatus, hbody = fetch(hurl)
    if hstatus != 200:
        raise RuntimeError(f"Q232_HEADER_HTTP_{hstatus}:{row['filename']}")
    htext = hbody.decode("utf-8", errors="replace")
    accession = extract_tag(htext, "ACCESSION NUMBER")
    if not accession:
        label_match = re.search(r"ACCESSION NUMBER\\s*:?\\s*(\\d{10}-\\d{2}-\\d{6})", htext, re.IGNORECASE)
        accession = label_match.group(1) if label_match else None
    accepted_match = re.search(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", htext, re.IGNORECASE)
    accepted = accepted_match.group(1) if accepted_match else None
    conformed = extract_tag(htext, "CONFORMED SUBMISSION TYPE")
    filed_as_of = extract_tag(htext, "FILED AS OF DATE")
    if not accepted:
        label_match = re.search(r"ACCEPTANCE-DATETIME\s+(\d{14})", htext, re.IGNORECASE)
        accepted = label_match.group(1) if label_match else None
    if not conformed:
        label_match = re.search(r"CONFORMED SUBMISSION TYPE\s*:?\s*([^\r\n]+)", htext, re.IGNORECASE)
        conformed = label_match.group(1).strip() if label_match else None
    if not filed_as_of:
        label_match = re.search(r"FILED AS OF DATE\s*:?\s*(\d{8})", htext, re.IGNORECASE)
        filed_as_of = label_match.group(1).strip() if label_match else None

    expected_accession = accession_from_filename(row["filename"])
    if accession and accession != expected_accession:
        raise RuntimeError(f"Q232_ACCESSION_MISMATCH:{accession}!={expected_accession}")
    if conformed and conformed.upper() != "CT ORDER":
        raise RuntimeError(f"Q232_FORM_MISMATCH:{conformed}")
    if not accepted:
        raise RuntimeError(f"Q232_ACCEPTANCE_MISSING:{expected_accession}")
    normalized_filed = f"{filed_as_of[:4]}-{filed_as_of[4:6]}-{filed_as_of[6:8]}" if filed_as_of and re.fullmatch(r"\d{8}", filed_as_of) else filed_as_of
    if normalized_filed != row["filed_date"]:
        raise RuntimeError(f"Q232_FILED_DATE_MISMATCH:{expected_accession}:{filed_as_of}:{row['filed_date']}")

    time.sleep(REQUEST_GAP_SECONDS)
    status_text, body_text = fetch(submission_text_url(row["filename"]))
    if status_text != 200:
        raise RuntimeError(f"Q232_SUBMISSION_TEXT_HTTP_{status_text}:{expected_accession}")
    complete_text = gzip.decompress(body_text) if body_text.startswith(b"\x1f\x8b") else body_text
    complete = complete_text.decode("utf-8", errors="replace")
    if not re.search(r"<TYPE>\s*CT ORDER\b", complete, re.IGNORECASE):
        raise RuntimeError(f"Q232_COMPLETE_TEXT_FORM_MISSING:{expected_accession}")
    pdf_name_match = re.search(r"<DOCUMENT>.*?<TYPE>\s*CT ORDER\b.*?<FILENAME>\s*([^\s<]+)", complete, re.IGNORECASE | re.DOTALL)
    if not pdf_name_match:
        raise RuntimeError(f"Q232_CT_ORDER_DOCUMENT_NOT_DECLARED:{expected_accession}")
    document_name = pdf_name_match.group(1).strip()
    cik, accession_dashed = archive_base(row["filename"])
    pdf_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_dashed.replace('-', '')}/{document_name}"
    time.sleep(REQUEST_GAP_SECONDS)
    pdf_status, pdf_body = fetch(pdf_url)
    if pdf_status != 200 or not pdf_body:
        raise RuntimeError(f"Q232_CT_ORDER_DOCUMENT_HTTP_{pdf_status}:{expected_accession}:{document_name}")
    return {
        "accession_number": expected_accession,
        "cik": row["cik"],
        "company_name": row["company_name"],
        "filing_date": row["filed_date"],
        "header_url": hurl,
        "header_sha256": sha256_bytes(hbody),
        "detail_url": detail_url(row["filename"]),
        "submission_text_url": submission_text_url(row["filename"]),
        "submission_text_sha256": sha256_bytes(body_text),
        "ct_order_document": document_name,
        "ct_order_document_url": pdf_url,
        "ct_order_document_sha256": sha256_bytes(pdf_body),
        "accepted_datetime": accepted,
        "status": "PASS",
    }


def sample_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_year: dict[int, list[dict[str, str]]] = {}
    for row in sorted(rows, key=lambda x: (x["filed_date"], accession_from_filename(x["filename"]))):
        by_year.setdefault(int(row["filed_date"][:4]), []).append(row)
    out: list[dict[str, str]] = []
    for year in sorted(by_year):
        year_rows = by_year[year]
        indices = sorted(set([0, (len(year_rows) - 1) // 2, len(year_rows) - 1]))
        out.extend(year_rows[i] for i in indices)
    return out


def run(output: Path) -> dict[str, object]:
    quarter_receipts: list[dict[str, object]] = []
    all_rows: list[dict[str, str]] = []
    for year, quarter in quarter_list():
        body, transport = fetch_form_index(year, quarter)
        rows = parse_index(body)
        quarter_receipts.append({
            "year": year,
            "quarter": quarter,
            "matching_rows": len(rows),
            "source_family": f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/",
            **transport,
        })
        all_rows.extend(rows)

    by_accession: dict[str, dict[str, str]] = {}
    for row in all_rows:
        accession = accession_from_filename(row["filename"])
        if accession in by_accession and by_accession[accession] != row:
            raise RuntimeError(f"Q232_DUPLICATE_ACCESSION_CONFLICT:{accession}")
        by_accession[accession] = row

    unique_rows = sorted(by_accession.values(), key=lambda x: (x["filed_date"], accession_from_filename(x["filename"])))
    sampled = sample_rows(unique_rows)
    checks = [check_sample(row) for row in sampled]

    years = sorted({int(r["filed_date"][:4]) for r in unique_rows})
    result: dict[str, object] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-06-232-SEC-CT-SOURCE-CENSUS",
        "status": "Q232_SEC_CT_SOURCE_CENSUS_COMPLETED",
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "quarters_checked": len(quarter_receipts),
        "quarter_receipts": quarter_receipts,
        "filtered_ct_order_rows": len(all_rows),
        "unique_accessions": len(unique_rows),
        "calendar_years_with_ct_orders": years,
        "event_density_by_year": {str(year): sum(1 for r in unique_rows if int(r["filed_date"][:4]) == year) for year in years},
        "deterministic_sample_rule": "first/median/last per year",
        "sample_size": len(sampled),
        "sample_checks": checks,
        "interpretation": {
            "quarterly_index_route_retrieved": True,
            "ct_order_population_reconstructed_for_fixed_window": True,
            "sampled_headers_verified": True,
            "sampled_complete_submission_text_verified": True,
            "sampled_ct_order_documents_verified": True,
            "public_observation_time_proven": False,
            "same_day_pit_safe": False,
            "approval_extension_unredacted_lineage_compiled": False,
            "full_linked_exhibit_lineage_compiled": False,
        },
        "governance": {
            "performance": False, "holdout_selection": False, "ranking": False,
            "parameter_search": False, "threshold_search": False, "horizon_search": False,
            "asset_search": False, "variant_search": False, "promotion": False,
            "performance_authorized": False, "automatic_promotion": False, "live_execution": False,
        },
        "safety": {"PAPER_ONLY": True, "LIVE_TRADING_ENABLED": False, "ORDERS_ENABLED": False, "AUTOMATIC_PROMOTION": False},
    }
    result["receipt_fingerprint"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({
        "status": result["status"],
        "quarters_checked": result["quarters_checked"],
        "filtered_ct_order_rows": result["filtered_ct_order_rows"],
        "unique_accessions": result["unique_accessions"],
        "sample_size": result["sample_size"],
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
