"""Independent Q218 source/PIT architecture reproduction.

This gate rechecks the positive Q218 source/event receipts using a separate
implementation: SEC submissions metadata plus direct EDGAR archive headers
and primary documents. It does not reuse Q218 gate functions and never
reads market outcomes or authorizes performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ISSUERS = {
    "AAPL": "320193",
    "MSFT": "789019",
    "AMZN": "1018724",
    "JPM": "19617",
    "XOM": "34088",
    "NVDA": "1045810",
    "WMT": "104169",
    "DIS": "1744489",
}
START = "2025-01-01"
END = "2026-10-05"
UA = "TradingAgent-Public-Research/Q218-independent-architecture-PIT/1"
TIMEOUT = 45
RETRYABLE = {408, 425, 429, 500, 502, 503, 504}


def fetch(url: str) -> bytes:
    last: Exception | None = None
    for attempt in range(1, 4):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "*/*",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                body = response.read()
            time.sleep(0.5)
            return body
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in RETRYABLE or attempt >= 3:
                raise
            retry_after = 0
            try:
                retry_after = int(exc.headers.get("Retry-After", "0"))
            except (TypeError, ValueError):
                pass
            time.sleep(max(2 * attempt, retry_after, 2))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            if attempt >= 3:
                raise
            time.sleep(2 * attempt)
    raise last or RuntimeError("Q218_INDEPENDENT_FETCH_FAILED")


def archive_base(cik: str, accession: str) -> str:
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession.replace("-", "")}/"
    )


def parse_header(header: bytes) -> dict[str, str | None]:
    text = header.decode("utf-8", errors="replace")
    def find(pattern: str) -> str | None:
        match = re.search(pattern, text, flags=re.I)
        return match.group(1).strip() if match else None
    return {
        "accession": find(r"ACCESSION NUMBER:\s*([0-9]{10}-[0-9]{2}-[0-9]{6})"),
        "cik": find(r"CENTRAL INDEX KEY:\s*([0-9]{10})"),
        "form": find(r"CONFORMED SUBMISSION TYPE:\s*([^\s<]+)"),
        "filed_as_of_date": find(r"FILED AS OF DATE:\s*([0-9]{8})"),
        "acceptance_datetime": find(r"<ACCEPTANCE-DATETIME>\s*([0-9]{14})"),
    }


def load_submissions(cik: str) -> dict[str, dict]:
    data = json.loads(
        fetch(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json").decode("utf-8")
    )
    recent = data.get("filings", {}).get("recent", {})
    keys = ["form", "filingDate", "reportDate", "accessionNumber", "primaryDocument", "items"]
    rows: dict[str, dict] = {}
    accessions = recent.get("accessionNumber", [])
    for i, acc in enumerate(accessions):
        if not acc:
            continue
        rows[acc] = {
            key: (recent.get(key, [None] * len(accessions))[i] if i < len(recent.get(key, [])) else None)
            for key in keys
        }
    return rows


def header_record(cik: str, accession: str) -> dict[str, str | None]:
    body = fetch(archive_base(cik, accession) + f"{accession}-index-headers.html")
    parsed = parse_header(body)
    if parsed["accession"] != accession:
        raise AssertionError(f"{accession}: accession mismatch")
    if parsed["cik"] != f"{int(cik):010d}":
        raise AssertionError(f"{accession}: CIK mismatch")
    if not parsed["acceptance_datetime"]:
        raise AssertionError(f"{accession}: missing acceptance")
    parsed["header_sha256"] = hashlib.sha256(body).hexdigest()
    return parsed


def primary_document(cik: str, accession: str, document: str) -> str:
    return fetch(archive_base(cik, accession) + document).decode("utf-8", errors="replace")


def parent_date_from_amendment(text: str) -> str | None:
    m = re.search(
        r"Initial Form 8-K.*?filed with the Securities and Exchange Commission "
        r"on ([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
        text,
        flags=re.I | re.S,
    )
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat()
    except ValueError:
        return None


def reproduce(source: dict, event: dict) -> dict:
    assert source.get("record_type") == "q218_sec_multichannel_source_gate"
    assert source.get("candidate_id") == "Q218"
    assert source.get("issuer_count") == 8
    assert source.get("all_required_issuer_channels_observed") is True
    assert source.get("scientific_evidence") is False
    assert source.get("performance_authorization") is False
    assert source.get("holdout_selection") is False
    assert source.get("ranking") is False
    assert source.get("tuning") is False
    assert source.get("promotion") is False
    assert source.get("live_execution") is False

    assert event.get("record_type") == "q218_sec_event_pair_lineage_gate"
    assert event.get("candidate_id") == "Q218"
    assert event.get("issuer_count") == 8
    assert event.get("all_pairing_valid") is True
    assert event.get("scientific_evidence") is False
    assert event.get("performance_authorization") is False
    assert event.get("holdout_selection") is False
    assert event.get("ranking") is False
    assert event.get("tuning") is False
    assert event.get("promotion") is False
    assert event.get("live_execution") is False
    assert event.get("fixed_window") == {"start": START, "end": END}

    issuer_results = event.get("issuer_results", {})
    if set(issuer_results) != set(ISSUERS):
        raise AssertionError("Q218_INDEPENDENT_ISSUER_SET_MISMATCH")
    reproduced = {}
    total_pairs = 0
    for symbol, cik in ISSUERS.items():
        expected = issuer_results[symbol]
        if expected.get("all_pairing_valid") is not True or expected.get("all_lineage_valid") is not True:
            raise AssertionError(f"{symbol}: upstream lineage/pair gate not positive")
        rows = load_submissions(cik)
        pairs = []
        for pair in expected.get("event_pairs", []):
            tenk_acc = pair["ten_k_accession"]
            event_acc = pair["item_2_02_8k_accession"]
            tenk_meta = rows.get(tenk_acc)
            event_meta = rows.get(event_acc)
            if not tenk_meta or tenk_meta.get("form") != "10-K":
                raise AssertionError(f"{symbol}: missing independent 10-K {tenk_acc}")
            if not event_meta or event_meta.get("form") != "8-K":
                raise AssertionError(f"{symbol}: missing independent 8-K {event_acc}")
            if not (START <= str(tenk_meta.get("filingDate")) <= END):
                raise AssertionError(f"{symbol}: 10-K outside fixed window {tenk_acc}")
            if not (START <= str(event_meta.get("filingDate")) <= END):
                raise AssertionError(f"{symbol}: 8-K outside fixed window {event_acc}")
            tenk_header = header_record(cik, tenk_acc)
            event_header = header_record(cik, event_acc)
            ta = tenk_header["acceptance_datetime"]
            ea = event_header["acceptance_datetime"]
            if ta != pair["ten_k_acceptance_datetime"]:
                raise AssertionError(f"{symbol}: 10-K acceptance mismatch {tenk_acc}")
            if ea != pair["item_2_02_8k_acceptance_datetime"]:
                raise AssertionError(f"{symbol}: 8-K acceptance mismatch {event_acc}")
            lower = pair.get("pairing_lower_bound_acceptance")
            if not ea or not ta or not (ea <= ta and (lower is None or ea > lower)):
                raise AssertionError(f"{symbol}: PIT acceptance interval failed {event_acc}")
            pairs.append({
                "ten_k_accession": tenk_acc,
                "item_2_02_8k_accession": event_acc,
                "ten_k_acceptance_datetime": ta,
                "item_2_02_8k_acceptance_datetime": ea,
                "lower_bound_acceptance": lower,
                "pit_interval_valid": True,
            })
        lineages = []
        for lineage in expected.get("amendment_lineage", []):
            amendment = lineage.get("amendment_accession")
            parent = lineage.get("parent_candidate_accession")
            if not amendment or not parent:
                raise AssertionError(f"{symbol}: unresolved amendment lineage")
            amendment_meta = rows.get(amendment)
            parent_meta = rows.get(parent)
            if not amendment_meta or not str(amendment_meta.get("form", "")).endswith("/A"):
                raise AssertionError(f"{symbol}: amendment metadata missing {amendment}")
            if not parent_meta or str(parent_meta.get("form", "")).endswith("/A"):
                raise AssertionError(f"{symbol}: parent metadata invalid {parent}")
            am_header = header_record(cik, amendment)
            parent_header = header_record(cik, parent)
            if not am_header["acceptance_datetime"] or not parent_header["acceptance_datetime"]:
                raise AssertionError(f"{symbol}: missing amendment/parent acceptance")
            if not parent_header["acceptance_datetime"] < am_header["acceptance_datetime"]:
                raise AssertionError(f"{symbol}: amendment acceptance ordering failed")
            doc = amendment_meta.get("primaryDocument")
            if not doc:
                raise AssertionError(f"{symbol}: missing amendment primary document")
            am_text = primary_document(cik, amendment, str(doc))
            hint = parent_date_from_amendment(am_text)
            explicit_parent_valid = None
            if str(amendment_meta.get("form")) == "8-K/A" and hint:
                if str(parent_meta.get("filingDate")) != hint:
                    raise AssertionError(f"{symbol}: explicit parent filing-date mismatch {amendment}")
                explicit_parent_valid = True
            lineages.append({
                "amendment_accession": amendment,
                "parent_candidate_accession": parent,
                "amendment_acceptance_datetime": am_header["acceptance_datetime"],
                "parent_acceptance_datetime": parent_header["acceptance_datetime"],
                "explicit_parent_filing_date_hint": hint,
                "explicit_parent_date_valid": explicit_parent_valid,
                "acceptance_order_valid": True,
            })
        reproduced[symbol] = {
            "pair_count": len(pairs),
            "pairs": pairs,
            "lineage_count": len(lineages),
            "lineage": lineages,
            "all_pair_checks_passed": len(pairs) == len(expected.get("event_pairs", [])),
            "all_lineage_checks_passed": len(lineages) == len(expected.get("amendment_lineage", [])),
        }
        total_pairs += len(pairs)

    result = {
        "schema_version": "1.0",
        "record_type": "q218_independent_architecture_pit_reproduction",
        "candidate_id": "Q218",
        "status": "Q218_INDEPENDENT_ARCHITECTURE_PIT_REPRODUCED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixed_window": {"start": START, "end": END},
        "upstream_receipts": {
            "source_receipt_fingerprint": source["receipt_fingerprint"],
            "event_pair_receipt_fingerprint": event["receipt_fingerprint"],
        },
        "independent_method": {
            "implementation": "separate parser and reconciliation path",
            "source_route": "SEC submissions JSON plus direct EDGAR archive header and primary-document retrieval",
            "reused_q218_gate_functions": False,
            "market_outcomes_read": False,
        },
        "reproduction": {
            "issuer_count": 8,
            "total_event_pairs_reproduced": total_pairs,
            "issuer_results": reproduced,
            "all_checks_passed": True,
            "future_cutoff_used": END,
            "same_day_decision_use_allowed": False,
        },
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "asset_selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "variant_search": False,
            "candidate_ranking": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "next_gate": "FROZEN_PREREGISTRATION_AND_IMMUTABLE_AUTHORIZATION_RECONCILE",
    }
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    event = json.loads(args.event.read_text(encoding="utf-8"))
    result = reproduce(source, event)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "receipt_fingerprint": result["receipt_fingerprint"],
        "total_event_pairs_reproduced": result["reproduction"]["total_event_pairs_reproduced"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
