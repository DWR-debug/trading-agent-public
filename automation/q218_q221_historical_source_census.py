"""Historical source-census gates for Q218-Q221.

The census is deliberately discovery/PIT infrastructure only. It does not read
market outcomes, rank candidates, optimize parameters, or authorize performance.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SEC_CIKS = {
    "AAPL": "320193",
    "MSFT": "789019",
    "AMZN": "1018724",
    "JPM": "19617",
    "XOM": "34088",
    "NVDA": "1045810",
    "WMT": "104169",
    "DIS": "1744489",
}
FIXED_START = "2025-01-01"
FIXED_END = "2026-10-05"
SEC_HEADERS = {"User-Agent": "TradingAgent-Public-Research/1.0 research@example.invalid"}
USA_RDTNE_URL = "https://www.usaspending.gov/award/CONT_AWD_N0003019F5005_9700_N0003017G0050_9700/"
SEC_NOTES_URL = "https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets/2009q1_notes.zip"


def fetch(url: str, limit: int | None = 1000000) -> tuple[int, str, bytes]:
    request = urllib.request.Request(url, headers=SEC_HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read(limit) if limit is not None else response.read()
        return int(getattr(response, "status", 200)), response.headers.get("Content-Type", ""), body


def sec_submission_census() -> dict:
    """Census SEC annual filings and deterministic mandatory/voluntary pairing.

    Pairing is based only on public SEC filing structure and acceptance order:
    for each in-window 10-K, select the latest eligible earnings-release 8-K
    whose acceptance timestamp falls after the preceding 10-K acceptance and
    on/before the target 10-K acceptance. No arbitrary lookback window, market
    outcome, or future information is used.
    """
    issuer_results = {}
    pairing_rule = (
        "latest eligible Item-2.02/Exhibit-99.1-style 8-K by SEC acceptance "
        "timestamp within the interval (preceding 10-K acceptance, target 10-K acceptance]"
    )
    for symbol, cik in SEC_CIKS.items():
        padded_cik = f"{int(cik):010d}"
        status, content_type, body = fetch(
            f"https://data.sec.gov/submissions/CIK{padded_cik}.json", None
        )
        data = json.loads(body.decode("utf-8"))
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        accessions = recent.get("accessionNumber", [])
        primaries = recent.get("primaryDocument", [])
        items = recent.get("items", [])
        rows = []
        for i, form in enumerate(forms):
            if form not in {"10-K", "8-K"}:
                continue
            filing_date = filing_dates[i] if i < len(filing_dates) else None
            if not filing_date or filing_date > FIXED_END:
                continue
            in_window = FIXED_START <= filing_date <= FIXED_END
            prior_boundary_10k = form == "10-K" and filing_date < FIXED_START
            if not in_window and not prior_boundary_10k:
                continue
            accession = accessions[i]
            primary = primaries[i]
            report_date = report_dates[i] if i < len(report_dates) else None
            item_field = str(items[i] if i < len(items) else "")
            archive_base = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                f"{accession.replace('-', '')}/"
            )
            index_headers = archive_base + f"{accession}-index-headers.html"
            primary_url = archive_base + primary
            row = {
                "form": form, "filing_date": filing_date, "accession": accession,
                "primary_document": primary, "report_date": report_date,
                "items": item_field, "index_headers_url": index_headers,
                "primary_url": primary_url, "in_control_window": in_window,
                "prior_10k_boundary": prior_boundary_10k,
                "acceptance_datetime_found": False, "acceptance_datetime": None,
                "exhibit_99_1": False, "earnings_release_marker": False,
                "item_2_02_marker": bool(
                    re.search(r"(^|[,;\s])2\.02([,;\s]|$)", item_field)
                ),
                "primary_publication_terms_marker": False,
                "is_eligible_earnings_release_8k": False,
            }
            try:
                _, _, page = fetch(index_headers, None)
                index_text = page.decode("utf-8", errors="replace")
                acceptance = re.findall(
                    r"<ACCEPTANCE-DATETIME>\s*([0-9]{14})",
                    index_text, flags=re.I
                )
                row["acceptance_datetime"] = acceptance[0] if acceptance else None
                row["acceptance_datetime_found"] = bool(acceptance)
                row["exhibit_99_1"] = bool(
                    re.search(r"EXHIBIT\s+99\.1", index_text, flags=re.I)
                )
                row["earnings_release_marker"] = bool(
                    re.search(r"EARNINGS\s+RELEASE|PRESS\s+RELEASE", index_text, flags=re.I)
                )
            except Exception as exc:
                row["error"] = type(exc).__name__ + ":" + str(exc)
            rows.append(row)
        annual = [
            r for r in rows
            if r["form"] == "10-K"
            and r.get("in_control_window") is True
            and r.get("acceptance_datetime_found") is True
        ]
        annual_all = [
            r for r in rows
            if r["form"] == "10-K"
            and r.get("acceptance_datetime_found") is True
        ]
        eight_k = [r for r in rows if r["form"] == "8-K"]
        for target in annual:
            target_accept = target["acceptance_datetime"]
            prior = [
                r["acceptance_datetime"] for r in annual_all
                if r is not target and r["acceptance_datetime"] < target_accept
            ]
            lower_bound = max(prior) if prior else None
            cycle_candidates = [
                r for r in eight_k
                if r.get("acceptance_datetime_found") is True
                and r["acceptance_datetime"] <= target_accept
                and (lower_bound is None or r["acceptance_datetime"] > lower_bound)
                and (
                    r.get("item_2_02_marker") is True
                    or r.get("exhibit_99_1") is True
                    or r.get("earnings_release_marker") is True
                )
            ]
            for candidate in cycle_candidates:
                try:
                    _, _, primary_page = fetch(candidate["primary_url"], None)
                    primary_text = primary_page.decode("utf-8", errors="replace")
                    candidate["primary_publication_terms_marker"] = bool(
                        re.search(
                            r"EARNINGS|FINANCIAL\s+RESULTS|QUARTERLY\s+RESULTS|FULL[-\s]?YEAR\s+RESULTS",
                            primary_text, flags=re.I
                        )
                    )
                except Exception as exc:
                    candidate["primary_fetch_error"] = type(exc).__name__ + ":" + str(exc)
                candidate["is_eligible_earnings_release_8k"] = bool(
                    candidate.get("item_2_02_marker")
                    or candidate.get("exhibit_99_1")
                    or candidate.get("earnings_release_marker")
                    or candidate.get("primary_publication_terms_marker")
                )
            eligible = [
                r for r in cycle_candidates
                if r.get("is_eligible_earnings_release_8k") is True
            ]
            if eligible:
                selected = max(eligible, key=lambda r: r["acceptance_datetime"])
                target["paired_8k"] = selected
                target["pair_lower_bound_acceptance"] = lower_bound
                target["pairing_observed"] = True
            else:
                target["paired_8k"] = None
                target["pair_lower_bound_acceptance"] = lower_bound
                target["pairing_observed"] = False
        eligible_all = [
            r for r in eight_k
            if r.get("is_eligible_earnings_release_8k") is True
        ]
        paired_targets = [r for r in annual if r.get("pairing_observed") is True]
        issuer_results[symbol] = {
            "cik": cik, "status": status, "content_type": content_type,
            "window_row_count": sum(
                1 for r in rows if r.get("in_control_window") is True
            ),
            "annual_10k_count": len(annual),
            "earnings_release_8k_count": len(
                [r for r in eligible_all if r.get("in_control_window") is True]
            ),
            "pairing_rule": pairing_rule,
            "paired_10k_count": len(paired_targets),
            "pairable_report_period_count": len(paired_targets),
            "latest_10k": (
                max(annual, key=lambda r: r["acceptance_datetime"]) if annual else None
            ),
            "latest_8k_earnings_release": (
                max(eligible_all, key=lambda r: r["acceptance_datetime"])
                if eligible_all else None
            ),
            "paired_10k_events": [
                {
                    "ten_k_accession": r["accession"],
                    "ten_k_acceptance_datetime": r["acceptance_datetime"],
                    "ten_k_report_date": r.get("report_date"),
                    "paired_8k_accession": (
                        r["paired_8k"]["accession"] if r.get("paired_8k") else None
                    ),
                    "paired_8k_acceptance_datetime": (
                        r["paired_8k"]["acceptance_datetime"]
                        if r.get("paired_8k") else None
                    ),
                    "paired_8k_report_date": (
                        r["paired_8k"].get("report_date") if r.get("paired_8k") else None
                    ),
                    "pair_lower_bound_acceptance": r.get("pair_lower_bound_acceptance"),
                    "pairing_observed": r.get("pairing_observed") is True,
                }
                for r in annual
            ],
            "exact_report_date_pair_count_diagnostic": sum(
                int(
                    any(
                        r.get("form") == "8-K"
                        and r.get("report_date") == target.get("report_date")
                        and r.get("is_eligible_earnings_release_8k") is True
                        for r in eight_k
                    )
                )
                for target in annual
            ),
        }
    return {
        "fixed_window": {"start": FIXED_START, "end": FIXED_END},
        "issuer_count": len(issuer_results),
        "pairing_rule": pairing_rule,
        "issuer_results": issuer_results,
        "pairable_issuer_count": sum(
            int(x["pairable_report_period_count"] > 0)
            for x in issuer_results.values()
        ),
    }

def sec_notes_census() -> dict:
    status, content_type, body = fetch(SEC_NOTES_URL, None)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        names = archive.namelist()
    lower = {name.lower() for name in names}
    variant_groups = {
        "sub": {"sub.txt", "sub.tsv"},
        "tag": {"tag.txt", "tag.tsv"},
        "dim": {"dim.txt", "dim.tsv"},
        "num": {"num.txt", "num.tsv"},
        "txt": {"txt.txt", "txt.tsv"},
    }
    present = {
        key: any(candidate in lower for candidate in variants)
        for key, variants in variant_groups.items()
    }
    return {
        "status": status,
        "content_type": content_type,
        "archive_sha256": hashlib.sha256(body).hexdigest(),
        "archive_bytes": len(body),
        "zip_parse_ok": True,
        "required_member_markers_present": present,
        "required_member_variants": {key: sorted(variants) for key, variants in variant_groups.items()},
        "member_count": len(names),
        "members_sample": names[:20],
    }


USA_USASPENDING_ABOUT_DATA_URL = "https://www.usaspending.gov/data/about-the-data-download.pdf"
USA_USASPENDING_API_DOCS_URL = "https://api.usaspending.gov/docs/endpoints"


def _extract_pdf_text(body: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(body))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def usa_rdtne_census() -> dict:
    status, content_type, body = fetch(USA_USASPENDING_ABOUT_DATA_URL, None)
    text = _extract_pdf_text(body)
    upper = re.sub(r"\s+", " ", text).upper()
    api_status, api_content_type, api_body = fetch(USA_USASPENDING_API_DOCS_URL, None)
    api_text = re.sub(r"\s+", " ", api_body.decode("utf-8", errors="replace")).upper()
    return {
        "status": status,
        "content_type": content_type,
        "content_sha256": hashlib.sha256(body).hexdigest(),
        "content_bytes": len(body),
        "public_clock_section_found": "FREQUENCY OF UPDATES TO PRIME AWARD DATA FOR CONTRACTS" in upper,
        "contract_modification_within_five_days_found": "WITHIN FIVE DAYS" in upper,
        "publication_sequence_found": "PUBLISHED TO USASPENDING.GOV" in upper and "FOLLOWING MORNING" in upper,
        "transactions_endpoint_documented": "/API/V2/TRANSACTIONS/" in api_text,
        "api_status": api_status,
        "api_content_type": api_content_type,
        "api_content_bytes": len(api_body),
        "lookahead_used": False,
    }


def q129_contract_check(repo_root: Path) -> dict:
    contract = repo_root / "research/governance/q129_options_source_contract_2026_10_03.json"
    receipt = repo_root / "research/evidence/q129_independent_pit_2026_10_03.json"
    return {
        "contract_present": contract.is_file(),
        "independent_pit_receipt_present": receipt.is_file(),
        "same_day_use_allowed": False,
    }


def run(output: Path) -> dict:
    result = {
        "schema_version": 1,
        "record_type": "q218_q221_historical_source_census",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixed_control_window": {"start": FIXED_START, "end": FIXED_END},
        "candidate_ids": ["Q218", "Q219", "Q220", "Q221"],
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "q218_sec_pair_census": sec_submission_census(),
        "q219_q129_contract": q129_contract_check(Path.cwd()),
        "q220_sec_notes_census": sec_notes_census(),
        "q221_usa_rdtne_census": usa_rdtne_census(),
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    result["receipt_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
