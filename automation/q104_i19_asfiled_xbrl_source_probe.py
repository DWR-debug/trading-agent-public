"""Bounded historical as-filed XBRL source probe for Q104:I19.

This gate verifies that the frozen issuer universe can be reconstructed from
official SEC submissions history and that exact XBRL concept facts are reachable
from the as-filed filing archive. It does not compile returns, choose assets,
rank observations, or evaluate performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Q108 = ROOT / "research/evidence/q108_pit_integration_2026_10_01.json"
OUTPUT = ROOT / "research/evidence/q104_i19_asfiled_xbrl_source_probe_latest.json"

START = date(2013, 7, 1)
CUTOFF = date(2025, 9, 24)
FORMS = {"10-K", "10-Q"}
CONCEPTS = {
    "NetIncomeLoss",
    "NetCashProvidedByUsedInOperatingActivities",
    "Assets",
}
UA = "DWR-debug/trading-agent-public Q104-I19 as-filed XBRL source probe/1.0"
REQUEST_GAP = 0.25
MAX_RETRIES = 5


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_json(v: object) -> str:
    return hashlib.sha256(
        json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def parse_date(value: str) -> date:
    return date.fromisoformat(str(value)[:10])


def fetch(url: str) -> bytes:
    last: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            if attempt:
                time.sleep(min(8.0, 1.0 * (2 ** (attempt - 1))))
            else:
                time.sleep(REQUEST_GAP)
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": UA,
                    "Accept": "application/json,text/html,application/xml,text/xml,*/*",
                    "Accept-Encoding": "identity",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in {408, 425, 429, 500, 502, 503, 504} or attempt == MAX_RETRIES - 1:
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
    raise last or RuntimeError("SEC_FETCH_FAILED")


def load_frozen_ciks() -> dict[str, str]:
    data = json.loads(Q108.read_text(encoding="utf-8"))
    ciks = data.get("sec_ticker_mapping", {}).get("ciks", {})
    if not isinstance(ciks, dict) or len(ciks) != 8:
        raise RuntimeError("Q104_I19_Q108_CIK_MAP_NOT_EXACTLY_8")
    return {str(k).upper(): str(v).zfill(10) for k, v in ciks.items()}


def rows_from_submissions(payload: dict) -> list[dict]:
    filings = payload.get("filings", {})
    out: list[dict] = []
    recent = filings.get("recent", {})
    if isinstance(recent, dict):
        keys = list(recent.keys())
        n = len(recent.get("accessionNumber", []))
        for i in range(n):
            out.append({k: recent.get(k, [None] * n)[i] for k in keys if i < len(recent.get(k, []))})
        for item in filings.get("files", []) or []:
            name = item.get("name")
            if name:
                out.append({"_historical_file": str(name)})
    return out


def eligible_rows(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if r.get("_historical_file"):
            continue
        if str(r.get("form") or "").upper() not in FORMS:
            continue
        try:
            d = parse_date(str(r.get("filingDate")))
            accepted = str(r.get("acceptanceDateTime") or "")
        except Exception:
            continue
        if START <= d <= CUTOFF and accepted:
            out.append(r)
    return out


def get_history_files(cik: str, submissions: dict) -> list[dict]:
    out = []
    for f in submissions.get("filings", {}).get("files", []) or []:
        name = f.get("name")
        if not name:
            continue
        url = f"https://data.sec.gov/submissions/{name}"
        payload = json.loads(fetch(url).decode("utf-8"))
        recent = payload.get("filings", payload)
        # Historical submission files expose the same column-array shape.
        keys = list(recent.keys())
        n = len(recent.get("accessionNumber", []))
        for i in range(n):
            row = {k: recent.get(k, [None] * n)[i] for k in keys if i < len(recent.get(k, []))}
            if str(row.get("form") or "").upper() not in FORMS:
                continue
            try:
                d = parse_date(str(row.get("filingDate")))
            except Exception:
                continue
            if START <= d <= CUTOFF and row.get("acceptanceDateTime"):
                out.append(row)
    return out


def archive_base(cik: str, accession: str) -> str:
    no_dash = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{no_dash}"


def extract_from_inline(html: bytes) -> dict:
    text = html.decode("utf-8", "replace")
    return {concept: len(re.findall(rf"(?:[:_\\/]){re.escape(concept)}\\b", text)) for concept in CONCEPTS}


def extract_from_xml(xml: bytes) -> dict:
    text = xml.decode("utf-8", "replace")
    return {concept: len(re.findall(rf":{re.escape(concept)}\\b", text)) for concept in CONCEPTS}


def choose_instance(index_json: dict) -> str | None:
    for item in index_json.get("directory", {}).get("item", []) or []:
        name = str(item.get("name") or "")
        low = name.lower()
        if not low.endswith(".xml"):
            continue
        if any(token in low for token in ("-cal.xml", "-def.xml", "-lab.xml", "-pre.xml", "_cal.xml", "_def.xml", "_lab.xml", "_pre.xml")):
            continue
        if low.endswith(".xsd"):
            continue
        return name
    return None


def probe_filing(cik: str, row: dict, sample_rank: int) -> dict:
    acc = str(row["accessionNumber"])
    base = archive_base(cik, acc)
    primary = str(row.get("primaryDocument") or "")
    inline = bool(row.get("isInlineXBRL"))
    record = {
        "accession": acc,
        "filing_date": str(row.get("filingDate")),
        "acceptance_datetime": str(row.get("acceptanceDateTime")),
        "form": str(row.get("form")),
        "report_date": row.get("reportDate"),
        "fiscal_period": row.get("fp"),
        "is_xbrl": bool(row.get("isXBRL")),
        "is_inline_xbrl": inline,
        "primary_document": primary,
        "sample_rank": sample_rank,
        "source_base": base,
    }
    if not primary:
        record["status"] = "MISSING_PRIMARY_DOCUMENT_METADATA"
        return record

    try:
        if inline:
            url = f"{base}/{primary}"
            body = fetch(url)
            counts = extract_from_inline(body)
            record.update({
                "source_type": "inline_html",
                "source_url": url,
                "source_sha256": sha256_bytes(body),
                "source_bytes": len(body),
                "concept_occurrences": counts,
            })
        else:
            idx_url = f"{base}/{acc}-index.json"
            idx = json.loads(fetch(idx_url).decode("utf-8"))
            instance = choose_instance(idx)
            if not instance:
                record["status"] = "NO_XBRL_INSTANCE_DISCOVERED"
                record["index_url"] = idx_url
                return record
            url = f"{base}/{instance}"
            body = fetch(url)
            counts = extract_from_xml(body)
            record.update({
                "source_type": "xbrl_instance_xml",
                "source_url": url,
                "source_sha256": sha256_bytes(body),
                "source_bytes": len(body),
                "xbrl_instance": instance,
                "index_url": idx_url,
                "concept_occurrences": counts,
            })
        record["all_exact_concepts_observed"] = all(v > 0 for v in counts.values())
        record["status"] = "PASS_EXACT_CONCEPTS_REACHABLE" if record["all_exact_concepts_observed"] else "FAIL_EXACT_CONCEPT_SOURCE"
        return record
    except Exception as exc:
        record["status"] = "FETCH_OR_PARSE_ERROR"
        record["error"] = f"{type(exc).__name__}:{exc}"
        return record


def probe_issuer(symbol: str, cik: str) -> dict:
    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    raw = fetch(submissions_url)
    submissions = json.loads(raw.decode("utf-8"))
    rows = eligible_rows(rows_from_submissions(submissions))
    rows += get_history_files(cik, submissions)
    # Deterministically deduplicate by accession and sort by accepted time.
    by_acc = {str(r["accessionNumber"]): r for r in rows}
    eligible = sorted(by_acc.values(), key=lambda r: (str(r.get("acceptanceDateTime")), str(r.get("accessionNumber"))))

    if not eligible:
        return {
            "symbol": symbol,
            "cik": cik,
            "status": "NO_ELIGIBLE_10K_10Q",
            "eligible_filing_count": 0,
            "source_submission_sha256": sha256_bytes(raw),
            "controls": [],
        }

    indices = [0, len(eligible) // 2, len(eligible) - 1]
    controls = []
    seen = set()
    for rank, idx in enumerate(indices, start=1):
        row = eligible[idx]
        acc = str(row["accessionNumber"])
        if acc in seen:
            continue
        seen.add(acc)
        controls.append(probe_filing(cik, row, rank))

    record = {
        "symbol": symbol,
        "cik": cik,
        "status": "PASS_SOURCE_ROUTE" if all(
            c.get("status") == "PASS_EXACT_CONCEPTS_REACHABLE" for c in controls
        ) else "PARTIAL_OR_FAILED_CONTROL",
        "eligible_filing_count": len(eligible),
        "eligible_form_counts": {
            "10-K": sum(str(r.get("form")).upper() == "10-K" for r in eligible),
            "10-Q": sum(str(r.get("form")).upper() == "10-Q" for r in eligible),
        },
        "source_submission_sha256": sha256_bytes(raw),
        "controls": controls,
        "acceptance_clock_complete": all(bool(r.get("acceptanceDateTime")) for r in eligible),
    }
    return record


def build(selected_symbols: list[str] | None = None) -> dict:
    ciks = load_frozen_ciks()
    if selected_symbols:
        wanted = {str(x).upper() for x in selected_symbols}
        unknown = sorted(wanted - set(ciks))
        if unknown:
            raise RuntimeError("Q104_I19_UNKNOWN_SYMBOLS:" + ",".join(unknown))
        ciks = {k: v for k, v in ciks.items() if k in wanted}
    results = {}
    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = {ex.submit(probe_issuer, symbol, cik): symbol for symbol, cik in ciks.items()}
        for f in as_completed(futures):
            symbol = futures[f]
            results[symbol] = f.result()
    results = {k: results[k] for k in sorted(results)}
    all_source_pass = len(results) == 8 and all(v["status"] == "PASS_SOURCE_ROUTE" for v in results.values())
    receipt = {
        "schema_version": "1.0",
        "record_type": "q104_i19_asfiled_xbrl_source_probe",
        "candidate_id": "Q104:I19",
        "status": "HISTORICAL_AS_FILED_XBRL_SOURCE_PROBE_COMPLETED" if all_source_pass else "HISTORICAL_AS_FILED_XBRL_SOURCE_PROBE_PARTIAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_universe_source": str(Q108.relative_to(ROOT)).replace("\\", "/"),
        "symbols": sorted(ciks),
        "window": {
            "start": START.isoformat(),
            "cutoff": CUTOFF.isoformat(),
        },
        "exact_concepts": sorted(CONCEPTS),
        "issuer_results": results,
        "scientific_boundary": {
            "performance_authorized": False,
            "holdout_selection_allowed": False,
            "ranking_allowed": False,
            "parameter_search_allowed": False,
            "threshold_search_allowed": False,
            "horizon_search_allowed": False,
            "promotion_allowed": False,
            "live_execution_allowed": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "next_gate": "historical as-filed XBRL fact extraction + concept-specific PIT compiler",
    }
    receipt["receipt_fingerprint"] = sha256_json(receipt)
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=OUTPUT)
    ap.add_argument("--symbols", nargs="+")
    args = ap.parse_args()
    receipt = build(args.symbols)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "receipt_fingerprint": receipt["receipt_fingerprint"],
        "symbols": receipt["symbols"],
    }, sort_keys=True))
    return 0 if receipt["status"] == "HISTORICAL_AS_FILED_XBRL_SOURCE_PROBE_COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
