"""Q218 deterministic SEC 10-K / Item 2.02 event-pair and amendment-lineage gate.

Source/PIT structure only. No market outcomes, ranking, tuning, or authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
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
UA = {
    "User-Agent": "TradingAgent-Public-Research/1.0 research@example.invalid",
    "Accept-Encoding": "identity",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def acceptance(cik: str, accession: str) -> str | None:
    base = (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession.replace('-', '')}/"
    )
    url = base + f"{accession}-index-headers.html"
    text = fetch(url).decode("utf-8", errors="replace")
    match = re.search(r"<ACCEPTANCE-DATETIME>\s*([0-9]{14})", text, re.I)
    return match.group(1) if match else None


def _acceptance_key(row: dict) -> tuple[str, str]:
    return (
        row.get("acceptance_datetime") or "",
        row.get("accession") or "",
    )


def _nearest_prior(rows: list[dict], target: dict) -> dict | None:
    candidates = [
        row
        for row in rows
        if row.get("report_date") == target.get("report_date")
        and row.get("acceptance_datetime")
        and target.get("acceptance_datetime")
        and row["acceptance_datetime"] < target["acceptance_datetime"]
    ]
    return max(candidates, key=_acceptance_key) if candidates else None


def run(output: Path) -> dict:
    issuer_results: dict[str, dict] = {}

    for symbol, cik in ISSUERS.items():
        data = json.loads(
            fetch(
                f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
            ).decode("utf-8")
        )
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        documents = recent.get("primaryDocument", [])
        reports = recent.get("reportDate", [])
        items = recent.get("items", [])

        tenks: list[dict] = []
        earnings: list[dict] = []
        tenk_amendments: list[dict] = []
        earnings_amendments: list[dict] = []

        for i, form in enumerate(forms):
            filing_date = dates[i] if i < len(dates) else None
            if form not in {"10-K", "10-K/A", "8-K", "8-K/A"}:
                continue
            if not filing_date or not (START <= filing_date <= END):
                continue

            accession_number = accessions[i]
            report_date = reports[i] if i < len(reports) else None
            item_field = items[i] if i < len(items) else ""
            row = {
                "form": form,
                "filing_date": filing_date,
                "report_date": report_date,
                "accession": accession_number,
                "primary_document": (
                    documents[i] if i < len(documents) else None
                ),
                "acceptance_datetime": acceptance(cik, accession_number),
                "items": item_field if form in {"8-K", "8-K/A"} else None,
            }

            if form == "10-K":
                tenks.append(row)
            elif form == "10-K/A":
                tenk_amendments.append(row)
            elif form == "8-K" and "2.02" in str(item_field).split(","):
                earnings.append(row)
            elif form == "8-K/A" and "2.02" in str(item_field).split(","):
                earnings_amendments.append(row)

        pairs = []
        unmatched = []
        for tenk in sorted(tenks, key=lambda x: (x.get("report_date") or "", _acceptance_key(x))):
            candidates = [
                event
                for event in earnings
                if event.get("report_date") == tenk.get("report_date")
                and event.get("acceptance_datetime")
                and tenk.get("acceptance_datetime")
                and event["acceptance_datetime"] < tenk["acceptance_datetime"]
            ]
            event = max(candidates, key=_acceptance_key) if candidates else None
            if event is None:
                unmatched.append(
                    {
                        "ten_k_accession": tenk.get("accession"),
                        "report_date": tenk.get("report_date"),
                    }
                )
                continue
            pairs.append(
                {
                    "ten_k_accession": tenk["accession"],
                    "ten_k_acceptance_datetime": tenk["acceptance_datetime"],
                    "item_2_02_8k_accession": event["accession"],
                    "item_2_02_8k_acceptance_datetime": event["acceptance_datetime"],
                    "report_date": tenk["report_date"],
                    "acceptance_order_valid": (
                        event["acceptance_datetime"] <= tenk["acceptance_datetime"]
                    ),
                }
            )

        lineage = []
        unresolved_lineage = []
        for amendment, originals, kind in [
            (tenk_amendments, tenks, "10-K/A"),
            (earnings_amendments, earnings, "8-K/A"),
        ]:
            for row in amendment:
                parent = _nearest_prior(originals, row)
                item = {
                    "amendment_form": kind,
                    "amendment_accession": row.get("accession"),
                    "report_date": row.get("report_date"),
                    "parent_candidate_accession": parent.get("accession") if parent else None,
                    "parent_candidate_acceptance_datetime": (
                        parent.get("acceptance_datetime") if parent else None
                    ),
                    "acceptance_order_valid": bool(parent),
                }
                lineage.append(item)
                if not parent:
                    unresolved_lineage.append(item)

        all_pairing_valid = len(unmatched) == 0 and all(
            pair["acceptance_order_valid"] for pair in pairs
        )
        all_lineage_valid = len(unresolved_lineage) == 0

        issuer_results[symbol] = {
            "cik": cik,
            "ten_k_count": len(tenks),
            "item_2_02_8k_count": len(earnings),
            "ten_k_amendment_count": len(tenk_amendments),
            "item_2_02_8k_amendment_count": len(earnings_amendments),
            "event_pair_count": len(pairs),
            "event_pair_coverage": (
                len(pairs) / len(tenks) if tenks else 0.0
            ),
            "event_pairs": pairs,
            "unmatched_ten_k": unmatched,
            "amendment_lineage": lineage,
            "all_pairing_valid": all_pairing_valid,
            "all_lineage_valid": all_lineage_valid,
        }

    complete = bool(issuer_results) and all(
        row["ten_k_count"] > 0
        and row["item_2_02_8k_count"] > 0
        and row["event_pair_coverage"] == 1.0
        and row["all_pairing_valid"]
        and row["all_lineage_valid"]
        for row in issuer_results.values()
    )

    result = {
        "schema_version": 1,
        "record_type": "q218_sec_event_pair_lineage_gate",
        "candidate_id": "Q218",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixed_window": {"start": START, "end": END},
        "issuer_results": issuer_results,
        "issuer_count": len(issuer_results),
        "all_pairing_valid": complete,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "paper_only": True,
        "next_gate": (
            "INDEPENDENT_ARCHITECTURE_PIT_REPRODUCTION"
            if complete
            else "REPAIR_10K_8K_EVENT_PAIR_AND_AMENDMENT_LINEAGE"
        ),
    }
    canonical = json.dumps(
        result, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    result["receipt_fingerprint"] = hashlib.sha256(canonical).hexdigest()

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), sort_keys=True))
