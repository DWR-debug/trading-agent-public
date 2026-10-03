"""Q121-R3 SEC quarterly form-index reverse-issuer feasibility probe.

Source/PIT only. No prices, returns, holdouts, ranking, tuning, promotion or
live execution. The probe verifies deterministic index acquisition and recovery
of frozen control filings; it does not compile the full subject-issuer population.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
import gzip
import io
import zipfile
from datetime import date
from pathlib import Path

from automation import q121r1_sec_reverse_issuer_coverage as r1

START = "2024-02-05"
END = "2025-09-24"
FORM_SET = {"SC 13D", "SC 13G", "SC 13D/A", "SC 13G/A"}
REQUEST_GAP_SECONDS = 0.35
UA = "trading-agent-public/Q121R3-sec-form-index/1"
INDEX_TRANSPORTS = ("form.zip", "form.gz", "form.idx")

CIKS = {
    "SPGI": "0000064040",
    "NDAQ": "0001120193",
    "AMP": "0000820027",
    "RJF": "0000720005",
    "WMB": "0000107263",
    "VLO": "0001035002",
    "DVN": "0001090012",
    "EMN": "0000915389",
}

QUARTERS = (
    (2024, 1), (2024, 2), (2024, 3), (2024, 4),
    (2025, 1), (2025, 2), (2025, 3),
)

CONTROLS = (
    ("0001104659-24-021877", "0000064040", None),
    ("0001193125-24-189043", "0001120193", None),
    ("0001193125-24-258276", "0001239819", "0000820027"),
)

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def decode_sec_submission_body(body: bytes) -> bytes:
    """Decode a SEC archive payload when HTTP delivered gzip content."""
    if body.startswith(b"\\x1f\\x8b"):
        try:
            return gzip.decompress(body)
        except OSError as exc:
            raise RuntimeError("SEC_SUBMISSION_GZIP_DECODE_FAILED") from exc
    return body


def extract_control_cik(text: str, section: str) -> str | None:
    """Extract the first CIK from the requested SEC-HEADER section."""
    compact = r1.plain_text(text)
    if section == "Subject":
        section_pattern = r"SUBJECT COMPANY\\s*:?(.*?)(?=FILED BY\\s*:|$)"
    elif section == "Filed by":
        section_pattern = r"FILED BY\\s*:?(.*)$"
    else:
        raise ValueError(f"UNKNOWN_HEADER_SECTION:{section}")
    section_match = re.search(section_pattern, compact, re.IGNORECASE | re.DOTALL)
    if not section_match:
        return None
    cik_match = re.search(r"CENTRAL\\s+INDEX\\s+KEY\\s*:?\\s*(\\d{1,10})", section_match.group(1), re.IGNORECASE)
    return cik_match.group(1).zfill(10) if cik_match else None


def index_url(year: int, quarter: int) -> str:
    return f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/form.idx"

def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/plain,application/zip,application/gzip,*/*",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"SEC_FORM_INDEX_TRANSPORT_ERROR:{url}:{exc}") from exc

def parse_index(body: bytes) -> list[dict[str, str]]:
    """Parse SEC form.idx rows by stable semantic anchors.

    The official quarterly form index uses a fixed-width row layout and may
    render its header over multiple lines. Historical index rows also use a
    compact YYYYMMDD filing-date field, so the parser normalizes both that
    representation and the dashed ISO form.
    """
    row_pattern = re.compile(
        r"^\s*(?P<form>SC 13[DG](?:/A)?)\s+"
        r"(?P<company>.*?)\s+"
        r"(?P<cik>\d{1,10})\s+"
        r"(?P<filed_date>\d{8}|\d{4}-\d{2}-\d{2})\s+"
        r"(?P<filename>edgar/data/\S+)\s*$",
        re.IGNORECASE,
    )

    rows: list[dict[str, str]] = []
    for raw in body.decode("latin-1").splitlines():
        match = row_pattern.match(raw.rstrip("\r\n"))
        if not match:
            continue
        data = match.groupdict()
        form = data["form"].upper()
        filed_date = data["filed_date"]
        if len(filed_date) == 8 and "-" not in filed_date:
            filed_date = (
                f"{filed_date[0:4]}-{filed_date[4:6]}-{filed_date[6:8]}"
            )
        cik = data["cik"]
        filename = data["filename"]
        if form not in FORM_SET:
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", filed_date):
            continue
        if not re.fullmatch(r"\d{1,10}", cik):
            continue
        if not filename.startswith("edgar/data/"):
            continue
        rows.append({
            "cik": cik.zfill(10),
            "company_name": data["company"].strip(),
            "form": form,
            "filed_date": filed_date,
            "filename": filename,
        })
    return rows

def accession_from_filename(filename: str) -> str:
    dashed = re.search(r"(\d{10}-\d{2}-\d{6})(?:[-.]|$)", filename)
    if dashed:
        return dashed.group(1)
    m = re.search(r"/(\d{18})/", filename)
    if m:
        raw = m.group(1)
        return f"{raw[:10]}-{raw[10:12]}-{raw[12:]}"
    raise ValueError(f"ACCESSION_NOT_FOUND_IN_FILENAME:{filename}")

def archive_header_url(filename: str) -> str:
    parts = filename.split("/")
    if len(parts) < 4:
        raise ValueError(f"INVALID_FILENAME:{filename}")
    cik = str(int(parts[2]))
    accession = accession_from_filename(filename).replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{accession}-index-headers.html"

def within_window(value: str) -> bool:
    d = date.fromisoformat(value)
    return date.fromisoformat(START) <= d <= date.fromisoformat(END)


def fetch_logical_form_index(year: int, quarter: int) -> tuple[bytes, dict[str, object]]:
    attempts: list[dict[str, object]] = []
    for transport in INDEX_TRANSPORTS:
        url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/{transport}"
        time.sleep(REQUEST_GAP_SECONDS)
        status, body = fetch(url)
        attempts.append({"url": url, "status": status, "transport": transport})
        if status != 200:
            continue
        if transport == "form.zip":
            try:
                with zipfile.ZipFile(io.BytesIO(body)) as archive:
                    names = [n for n in archive.namelist() if n.lower().endswith("/form.idx") or n.lower() == "form.idx"]
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

def run(output: Path) -> dict[str, object]:
    quarter_receipts: list[dict[str, object]] = []
    all_rows: list[dict[str, str]] = []

    for year, quarter in QUARTERS:
        body, transport = fetch_logical_form_index(year, quarter)
        parsed = [row for row in parse_index(body) if row["form"] in FORM_SET and within_window(row["filed_date"])]
        quarter_receipts.append({
            "year": year,
            "quarter": quarter,
            "source_family": f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/",
            **transport,
            "matching_rows": len(parsed),
        })
        all_rows.extend(parsed)

    print("Q121R3_INDEX_DIAG rows=", len(all_rows))
    for row in all_rows:
        if row["filed_date"] in {"2024-02-13", "2024-07-30"} and row["form"] in FORM_SET:
            if any(key in row["filename"] for key in ("0001104659-24-021877", "0001193125-24-189043")):
                print("Q121R3_CONTROL_FILENAME_DIAG", json.dumps(row, sort_keys=True))

    by_accession: dict[str, list[dict[str, str]]] = {}
    for row in all_rows:
        accession = accession_from_filename(row["filename"])
        by_accession.setdefault(accession, []).append(row)

    controls: list[dict[str, object]] = []
    for accession, expected_subject, expected_filer in CONTROLS:
        matches = by_accession.get(accession, [])
        if not matches:
            raise RuntimeError(f"Q121R3_CONTROL_NOT_RECOVERED:{accession}")

        matched_check: dict[str, object] | None = None
        for row in matches:
            header_url = archive_header_url(row["filename"])
            time.sleep(REQUEST_GAP_SECONDS)
            status, body = fetch(header_url)
            candidates: list[tuple[str, bytes, int]] = []
            if status == 200:
                candidates.append((header_url, body, status))

            source_text_url = "https://www.sec.gov/Archives/" + row["filename"]
            if not candidates:
                time.sleep(REQUEST_GAP_SECONDS)
                source_status, source_body = fetch(source_text_url)
                if source_status == 200:
                    candidates.append((source_text_url, source_body, source_status))
            else:
                source_status = None

            matched_for_row = None
            for identity_url, identity_body, identity_status in candidates:
                header_text = identity_body.decode("utf-8", errors="replace")
                subject = extract_control_cik(header_text, "Subject") or r1.extract_header_section_cik(header_text, "Subject") or r1.extract_labeled_cik(header_text, "Subject")
                filer = extract_control_cik(header_text, "Filed by") or r1.extract_header_section_cik(header_text, "Filed by") or r1.extract_labeled_cik(header_text, "Filed by")
                accepted = r1.extract_accepted(header_text)
                if subject == expected_subject and (expected_filer is None or filer == expected_filer) and accepted is not None:
                    matched_for_row = {
                        "accession_number": accession,
                        "index_cik": row["cik"],
                        "form": row["form"],
                        "filing_date": row["filed_date"],
                        "filename": row["filename"],
                        "header_url": header_url,
                        "identity_source_url": identity_url,
                        "header_http_status": status,
                        "identity_http_status": identity_status,
                        "header_sha256": sha256_bytes(identity_body),
                        "subject_cik": subject,
                        "filed_by_cik": filer,
                        "accepted_datetime": accepted,
                        "expected_subject_cik": expected_subject,
                        "expected_filer_cik": expected_filer,
                    }
                    break
            if matched_for_row is None:
                source_text_url = "https://www.sec.gov/Archives/" + row["filename"]
                time.sleep(REQUEST_GAP_SECONDS)
                source_status, source_body = fetch(source_text_url)
                if source_status == 200:
                    source_preview = r1.plain_text(decode_sec_submission_body(source_body).decode("utf-8", errors="replace"))
                    print("Q121R3_IDENTITY_DIAG", json.dumps({
                        "accession_number": accession,
                        "index_cik": row["cik"],
                        "header_status": status,
                        "source_status": source_status,
                        "header_preview": r1.plain_text(body.decode("utf-8", errors="replace"))[:500] if status == 200 else "",
                        "source_preview": source_preview[:500],
                    }, sort_keys=True))
                if source_status == 200:
                    header_text = decode_sec_submission_body(source_body).decode("utf-8", errors="replace")
                    subject = r1.extract_header_section_cik(header_text, "Subject") or r1.extract_labeled_cik(header_text, "Subject")
                    filer = r1.extract_header_section_cik(header_text, "Filed by") or r1.extract_labeled_cik(header_text, "Filed by")
                    accepted = r1.extract_accepted(header_text)
                    if subject == expected_subject and (expected_filer is None or filer == expected_filer) and accepted is not None:
                        matched_for_row = {
                            "accession_number": accession,
                            "index_cik": row["cik"],
                            "form": row["form"],
                            "filing_date": row["filed_date"],
                            "filename": row["filename"],
                            "header_url": header_url,
                            "identity_source_url": source_text_url,
                            "header_http_status": status,
                            "identity_http_status": source_status,
                            "header_sha256": sha256_bytes(source_body),
                            "subject_cik": subject,
                            "filed_by_cik": filer,
                            "accepted_datetime": accepted,
                            "expected_subject_cik": expected_subject,
                            "expected_filer_cik": expected_filer,
                        }
            if matched_for_row is not None:
                matched_check = matched_for_row
                break

        if matched_check is None:
            raise RuntimeError(
                f"Q121R3_CONTROL_IDENTITY_NOT_RECOVERED:{accession}:"
                f"expected_subject={expected_subject}:expected_filer={expected_filer}"
            )
        controls.append(matched_check)

    result: dict[str, object] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-121R3-SEC-FORM-INDEX-REVERSE-ISSUER-FEASIBILITY",
        "status": "Q121R3_FORM_INDEX_ROUTE_FEASIBILITY_COMPLETED",
        "window": {"start": START, "end": END},
        "forms": sorted(FORM_SET),
        "frozen_issuer_cik_map": CIKS,
        "quarters_checked": len(quarter_receipts),
        "quarter_receipts": quarter_receipts,
        "filtered_form_rows": len(all_rows),
        "unique_accessions": len(by_accession),
        "frozen_controls_checked": len(controls),
        "controls": controls,
        "interpretation": {
            "quarterly_index_coverage_for_fixed_window": True,
            "frozen_controls_recovered": True,
            "subject_header_recovery_verified": True,
            "full_subject_issuer_population_compiled": False,
            "same_day_pit_safe": False,
            "revision_lineage_established": False,
        },
        "governance": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "performance_authorized": False,
            "automatic_promotion": False,
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
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({
        "status": result["status"],
        "quarters_checked": result["quarters_checked"],
        "filtered_form_rows": result["filtered_form_rows"],
        "controls": result["frozen_controls_checked"],
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
