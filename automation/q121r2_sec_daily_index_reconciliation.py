"""Q121-R2 independent SEC daily-index reconciliation.

Source/PIT only. No prices, returns, holdouts, ranking, tuning, performance,
promotion or live execution.

The Q121-R1 route supplies only a deterministic anchor set. Each anchor's
filing-date membership is independently verified against the SEC historical
daily master index, followed by filing-header subject/filer/acceptance checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import date
from html import unescape
from pathlib import Path

from automation import q121r1_sec_reverse_issuer_coverage as r1

FORM_SET = {"SC 13D", "SC 13G", "SC 13D/A", "SC 13G/A"}
REQUEST_GAP_SECONDS = 0.35
UA = "DWR-debug trading-agent-public Q121R2 via GitHub"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def quarter_for_month(month: int) -> int:
    return ((month - 1) // 3) + 1

def daily_master_index_url(day: str) -> str:
    parsed = date.fromisoformat(day)
    return (
        f"https://www.sec.gov/Archives/edgar/daily-index/{parsed.year}/"
        f"QTR{quarter_for_month(parsed.month)}/master.{parsed:%Y%m%d}.idx"
    )

def fetch(url: str) -> tuple[int, bytes]:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/plain,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"SEC_DAILY_INDEX_TRANSPORT_ERROR:{url}:{exc}") from exc

def parse_master_index(body: bytes) -> list[dict[str, str]]:
    text = body.decode("latin-1")
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            continue
        cik, company, form, filed_date, filename = parts
        if (
            cik.isdigit()
            and re.fullmatch(r"SC 13[DG](?:/A)?", form, re.IGNORECASE)
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}", filed_date)
            and filename.startswith("edgar/data/")
        ):
            rows.append({
                "cik": cik.zfill(10),
                "company_name": company,
                "form": form.upper(),
                "filed_date": filed_date,
                "filename": filename,
            })
    if not rows:
        raise RuntimeError("SEC_DAILY_INDEX_NO_13D13G_ROWS")
    return rows

def normalize_accession(value: str) -> str:
    match = re.search(r"\d{10}-\d{2}-\d{6}", value)
    if not match:
        raise ValueError(f"INVALID_ACCESSION:{value!r}")
    return match.group(0)

def accession_from_filename(filename: str) -> str:
    match = re.search(r"/(\d{18})-index\.(?:htm|html)$", filename, re.IGNORECASE)
    if not match:
        match = re.search(r"/(\d{18})/", filename)
    if not match:
        raise ValueError(f"ACCESSION_NOT_FOUND_IN_FILENAME:{filename}")
    raw = match.group(1)
    return f"{raw[:10]}-{raw[10:12]}-{raw[12:]}"

def build_header_url(filing_href: str) -> str:
    return re.sub(
        r"-index\.(?:htm|html)$",
        "-index-headers.html",
        filing_href,
        flags=re.IGNORECASE,
    )

def collect_anchors() -> tuple[dict[str, object], list[dict[str, object]]]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "q121r1.json"
        r1.run(path)
        payload = json.loads(path.read_text(encoding="utf-8"))

    anchors: list[dict[str, object]] = []
    for symbol, forms in payload["source_records"].items():
        for form, record in forms.items():
            for sample in record["deterministic_samples"]:
                anchors.append({
                    "symbol": symbol,
                    "form_query": form,
                    "accession_number": sample["accession_number"],
                    "filing_date": sample["filing_date"],
                    "filing_href": sample["filing_href"],
                    "filing_type": sample["filing_type"].upper(),
                    "issuer_cik": record["issuer_cik"],
                })
    anchors.sort(key=lambda x: (
        str(x["symbol"]), str(x["form_query"]), str(x["accession_number"])
    ))
    return payload, anchors

def run(output: Path) -> dict[str, object]:
    r1_payload, anchors = collect_anchors()
    if r1_payload.get("status") == "Q121R1_SOURCE_ROUTE_FALSIFIED":
        result: dict[str, object] = {
            "schema_version": "1.0",
            "task_id": "Q-2026-10-03-121R2-SEC-DAILY-INDEX-RECONCILIATION",
            "status": "Q121R2_BLOCKED_BY_Q121R1_FALSIFICATION",
            "fixed_universe": list(r1_payload["issuer_cik_map"].keys()),
            "anchor_rule": "Q121-R1 deterministic first/middle/last per issuer/form",
            "anchors_checked": 0,
            "daily_index_dates_checked": 0,
            "checks": [],
            "interpretation": {
                "independent_anchor_reconciliation": False,
                "full_window_population_exhaustiveness": False,
                "upstream_source_route_falsified": True,
            },
            "upstream": {
                "status": r1_payload["status"],
                "receipt_fingerprint": r1_payload["receipt_fingerprint"],
                "falsification": r1_payload.get("falsification"),
            },
            "pit": {
                "acceptance_timestamp_preserved": False,
                "exact_first_publication_time_proven": False,
                "immutable_revision_lineage_proven": False,
                "same_day_pit_safe": False,
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
    if not anchors:
        raise RuntimeError("Q121R2_NO_Q121R1_ANCHORS")

    index_cache: dict[str, tuple[int, bytes]] = {}
    checks: list[dict[str, object]] = []

    for anchor in anchors:
        filing_date = str(anchor["filing_date"])
        if filing_date not in index_cache:
            time.sleep(REQUEST_GAP_SECONDS)
            index_cache[filing_date] = fetch(daily_master_index_url(filing_date))
        status, body = index_cache[filing_date]
        if status != 200:
            raise RuntimeError(
                f"SEC_DAILY_INDEX_HTTP_{status}:{filing_date}"
            )
        rows = parse_master_index(body)
        accession = normalize_accession(str(anchor["accession_number"]))
        matches = [row for row in rows if accession_from_filename(row["filename"]) == accession]
        if len(matches) != 1:
            raise RuntimeError(
                f"SEC_DAILY_INDEX_ACCESSION_MATCH_FAILED:{anchor['symbol']}:"
                f"{anchor['form_query']}:{accession}:matches={len(matches)}"
            )
        idx = matches[0]
        if idx["filed_date"] != filing_date:
            raise RuntimeError(
                f"SEC_DAILY_INDEX_DATE_MISMATCH:{accession}:"
                f"{idx['filed_date']}!={filing_date}"
            )
        if idx["form"] not in FORM_SET:
            raise RuntimeError(f"SEC_DAILY_INDEX_FORM_MISMATCH:{accession}:{idx['form']}")

        header_url = build_header_url(str(anchor["filing_href"]))
        header_status, header_body = fetch(header_url)
        if header_status != 200:
            raise RuntimeError(f"SEC_HEADER_HTTP_{header_status}:{accession}")

        header_text = header_body.decode("utf-8", errors="replace")
        subject = r1.extract_header_section_cik(header_text, "Subject")
        filer = r1.extract_header_section_cik(header_text, "Filed by")
        accepted = r1.extract_accepted(header_text)
        subject_ok = subject == anchor["issuer_cik"]
        filer_ok = filer == idx["cik"]
        acceptance_ok = accepted is not None
        form_ok = str(anchor["filing_type"]) == idx["form"]
        pass_check = subject_ok and filer_ok and acceptance_ok and form_ok

        checks.append({
            "symbol": anchor["symbol"],
            "form_query": anchor["form_query"],
            "accession_number": accession,
            "filing_date": filing_date,
            "daily_index_url": daily_master_index_url(filing_date),
            "daily_index_sha256": sha256_bytes(body),
            "daily_index_cik": idx["cik"],
            "daily_index_form": idx["form"],
            "daily_index_filename": idx["filename"],
            "header_url": header_url,
            "header_sha256": sha256_bytes(header_body),
            "subject_cik": subject,
            "filed_by_cik": filer,
            "accepted_datetime": accepted,
            "status": "PASS" if pass_check else "FAIL",
        })
        if not pass_check:
            raise RuntimeError(
                f"SEC_DAILY_INDEX_IDENTITY_FAILED:{anchor['symbol']}:{accession}:"
                f"subject_ok={subject_ok}:filer_ok={filer_ok}:acceptance_ok={acceptance_ok}:form_ok={form_ok}"
            )
        time.sleep(REQUEST_GAP_SECONDS)

    result: dict[str, object] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-121R2-SEC-DAILY-INDEX-RECONCILIATION",
        "status": "Q121R2_INDEPENDENT_DAILY_INDEX_RECONCILIATION_COMPLETED",
        "fixed_universe": list(r1_payload["issuer_cik_map"].keys()),
        "anchor_rule": "Q121-R1 deterministic first/middle/last per issuer/form",
        "anchors_checked": len(checks),
        "daily_index_dates_checked": len(index_cache),
        "checks": checks,
        "interpretation": {
            "independent_anchor_reconciliation": True,
            "full_window_population_exhaustiveness": False,
        },
        "pit": {
            "acceptance_timestamp_preserved": True,
            "exact_first_publication_time_proven": False,
            "immutable_revision_lineage_proven": False,
            "same_day_pit_safe": False,
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
        "anchors_checked": result["anchors_checked"],
        "daily_index_dates_checked": result["daily_index_dates_checked"],
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
