"""Q121-R1 SEC reverse-issuer source feasibility probe.

Source/PIT feasibility only. This deliberately does not touch prices, returns,
holdouts, ranking, tuning, promotion or live execution.

The primary source is the SEC issuer-oriented browse endpoint, which can list
beneficial-ownership filings associated with a target issuer even when the
filing was submitted by another CIK. A bounded deterministic sample of filing
detail pages verifies subject/filer identity and acceptance-time availability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from html import unescape
from datetime import date

SYMBOLS = ("SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN")
FORMS = ("SC 13D", "SC 13G", "SC 13D/A", "SC 13G/A")
START = "20240205"
END = "20250924"
PAGE_SIZE = 100
REQUEST_GAP_SECONDS = 0.35
MAX_PAGES_PER_QUERY = 100
UA = "trading-agent-public/Q121R1-sec-reverse-issuer-coverage/1"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def get(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/atom+xml,application/xml,text/html,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return int(getattr(r, "status", 200)), r.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"HTTP_TRANSPORT_ERROR:{url}:{exc}") from exc

def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]

def first_text(node: ET.Element, wanted: str) -> str:
    for child in node.iter():
        if local_name(child.tag) == wanted:
            return "".join(child.itertext()).strip()
    return ""

def parse_atom_entries(body: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(body)
    entries: list[dict[str, str]] = []
    for entry in root.iter():
        if local_name(entry.tag) != "entry":
            continue
        row = {
            "accession_number": first_text(entry, "accession-nunber") or first_text(entry, "accession-number"),
            "filing_date": first_text(entry, "filing-date"),
            "filing_type": first_text(entry, "filing-type"),
            "title": first_text(entry, "title"),
            "filing_href": "",
        }
        for child in entry.iter():
            if local_name(child.tag) == "link":
                href = str(child.attrib.get("href", ""))
                rel = str(child.attrib.get("rel", ""))
                if rel == "alternate" and href:
                    row["filing_href"] = href
                    break
        if row["accession_number"] and row["filing_href"]:
            entries.append(row)
    return entries

def normalize_cik(value: str) -> str:
    digits = re.sub(r"[^0-9]", "", value)
    if not digits:
        raise ValueError(f"INVALID_CIK:{value!r}")
    return digits.zfill(10)

def plain_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(text))).strip()

def extract_labeled_cik(text: str, label: str) -> str | None:
    compact = plain_text(text)
    match = re.search(rf"\({re.escape(label)}\)\s*CIK:\s*0*(\d+)", compact, re.IGNORECASE)
    return match.group(1).zfill(10) if match else None

def extract_header_section_cik(text: str, section: str) -> str | None:
    compact = unescape(text)
    if section == "Subject":
        pattern = r"SUBJECT COMPANY:.*?CENTRAL INDEX KEY:\s*(\d+)"
    elif section == "Filed by":
        pattern = r"FILED BY:.*?CENTRAL INDEX KEY:\s*(\d+)"
    else:
        raise ValueError(f"UNKNOWN_HEADER_SECTION:{section}")
    match = re.search(pattern, compact, re.IGNORECASE | re.DOTALL)
    return match.group(1).zfill(10) if match else None

def extract_accepted(text: str) -> str | None:
    compact = plain_text(text)
    match = re.search(r"Accepted\s+([0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2}:[0-9]{2})", compact, re.IGNORECASE)
    if match:
        return match.group(1)
    header_match = re.search(r"ACCEPTANCE-DATETIME:\s*([0-9]{14})", unescape(text), re.IGNORECASE)
    if header_match:
        raw = header_match.group(1)
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]} {raw[8:10]}:{raw[10:12]}:{raw[12:14]}"
    return None

def validate_page_dates(rows: list[dict[str, str]]) -> None:
    start = date.fromisoformat(f"{START[:4]}-{START[4:6]}-{START[6:8]}")
    end = date.fromisoformat(f"{END[:4]}-{END[4:6]}-{END[6:8]}")
    for row in rows:
        raw = row.get("filing_date", "")
        try:
            filing_date = date.fromisoformat(raw)
        except ValueError as exc:
            raise RuntimeError(f"INVALID_FILING_DATE:{raw!r}") from exc
        if not start <= filing_date <= end:
            raise RuntimeError(f"SEC_BROWSE_DATE_FILTER_MISMATCH:{raw}:expected={START}..{END}")

def deterministic_sample(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    indexes = [0, len(rows) // 2, len(rows) - 1]
    out: list[dict[str, str]] = []
    seen: set[int] = set()
    for idx in indexes:
        if idx not in seen:
            seen.add(idx)
            out.append(rows[idx])
    return out

def browse_url(cik: str, form: str, start: int) -> str:
    params = {
        "action": "getcompany",
        "CIK": cik,
        "type": form,
        "datea": START,
        "dateb": END,
        "owner": "exclude",
        "count": str(PAGE_SIZE),
        "start": str(start),
        "output": "atom",
    }
    return "https://www.sec.gov/cgi-bin/browse-edgar?" + urllib.parse.urlencode(params)

def issuer_map() -> dict[str, str]:
    status, body = get("https://www.sec.gov/files/company_tickers.json")
    if status != 200:
        raise RuntimeError(f"SEC_TICKERS_HTTP_{status}")
    payload = json.loads(body)
    mapping: dict[str, str] = {}
    for row in payload.values():
        ticker = str(row.get("ticker", "")).upper()
        if ticker in SYMBOLS:
            mapping[ticker] = normalize_cik(str(row.get("cik_str", "")))
    if set(mapping) != set(SYMBOLS):
        raise RuntimeError(f"MISSING_CIK_MAPPING:{sorted(set(SYMBOLS)-set(mapping))}")
    return mapping

def run(output: Path) -> dict[str, object]:
    ciks = issuer_map()
    source_records: dict[str, object] = {}
    identity_checks: list[dict[str, object]] = []
    total_entries = 0

    for symbol in SYMBOLS:
        issuer_cik = ciks[symbol]
        per_form: dict[str, object] = {}
        for form in FORMS:
            rows: list[dict[str, str]] = []
            page_records: list[dict[str, object]] = []
            for page in range(MAX_PAGES_PER_QUERY):
                start = page * PAGE_SIZE
                url = browse_url(issuer_cik, form, start)
                status, body = get(url)
                if status != 200:
                    raise RuntimeError(f"SEC_BROWSE_HTTP_{status}:{symbol}:{form}:{start}")
                page_rows = parse_atom_entries(body)
                validate_page_dates(page_rows)
                page_records.append({
                    "start": start,
                    "count": len(page_rows),
                    "source_url": url,
                    "source_sha256": sha256_bytes(body),
                })
                rows.extend(page_rows)
                if not page_rows:
                    break
                if len(page_rows) < PAGE_SIZE:
                    break
                time.sleep(REQUEST_GAP_SECONDS)
            else:
                raise RuntimeError(f"PAGINATION_LIMIT_EXCEEDED:{symbol}:{form}")

            accessions = [r["accession_number"] for r in rows]
            if len(accessions) != len(set(accessions)):
                raise RuntimeError(f"DUPLICATE_ACCESSION:{symbol}:{form}")

            per_form[form] = {
                "issuer_cik": issuer_cik,
                "entry_count": len(rows),
                "pages": page_records,
                "filings": rows,
                "deterministic_samples": deterministic_sample(rows),
            }
            total_entries += len(rows)

            for sample in deterministic_sample(rows):
                detail_url = sample["filing_href"]
                if detail_url.startswith("http://"):
                    detail_url = "https://" + detail_url[len("http://"):]
                header_url = re.sub(r"-index\\.(?:htm|html)$", "-index-headers.html", detail_url, flags=re.IGNORECASE)
                if header_url == detail_url:
                    header_url = detail_url.replace("-index.htm", "-index-headers.html").replace("-index.html", "-index-headers.html")
                time.sleep(REQUEST_GAP_SECONDS)
                dstatus, dbody = get(header_url)
                if dstatus != 200:
                    raise RuntimeError(f"SEC_HEADER_HTTP_{dstatus}:{symbol}:{form}:{sample['accession_number']}")
                detail = dbody.decode("utf-8", errors="replace")
                subject = extract_header_section_cik(detail, "Subject") or extract_labeled_cik(detail, "Subject")
                filer = extract_header_section_cik(detail, "Filed by") or extract_labeled_cik(detail, "Filed by")
                accepted = extract_accepted(detail)
                ok = (
                    subject == issuer_cik
                    and filer is not None
                    and accepted is not None
                    and sample["filing_type"].upper() in {x.upper() for x in FORMS}
                )
                identity_checks.append({
                    "symbol": symbol,
                    "issuer_cik": issuer_cik,
                    "form_query": form,
                    "accession_number": sample["accession_number"],
                    "subject_cik": subject,
                    "filed_by_cik": filer,
                    "accepted_datetime": accepted,
                    "source_url": header_url,
                    "status": "PASS" if ok else "FAIL",
                    "detail_sha256": sha256_bytes(dbody),
                })
                if not ok:
                    raise RuntimeError(
                        f"IDENTITY_CHECK_FAILED:{symbol}:{form}:{sample['accession_number']}:"
                        f"subject={subject}:filer={filer}:accepted={accepted}"
                    )

        source_records[symbol] = per_form

    result: dict[str, object] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-121R1-SEC-REVERSE-ISSUER-COVERAGE",
        "status": "Q121R1_SOURCE_REVERSE_COVERAGE_COMPLETED",
        "issuer_cik_map": ciks,
        "source_contract": {
            "endpoint": "https://www.sec.gov/cgi-bin/browse-edgar",
            "forms": list(FORMS),
            "datea": START,
            "dateb": END,
            "page_size": PAGE_SIZE,
            "pagination": "monotonic_start",
        },
        "source_records": source_records,
        "identity_checks": identity_checks,
        "summary": {
            "issuers": len(SYMBOLS),
            "forms": len(FORMS),
            "discovered_filing_entries": total_entries,
            "identity_checks": len(identity_checks),
            "identity_checks_passed": sum(1 for x in identity_checks if x["status"] == "PASS"),
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
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
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
        "discovered_filing_entries": result["summary"]["discovered_filing_entries"],
        "identity_checks": result["summary"]["identity_checks"],
        "receipt_fingerprint": result["receipt_fingerprint"],
    }))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
