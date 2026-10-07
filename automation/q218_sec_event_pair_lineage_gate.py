"""Q218 deterministic SEC 10-K / Item 2.02 event-pair and amendment-lineage gate.

Source/PIT structure only. No market outcomes, ranking, tuning, or authorization.
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
UA = {
    "User-Agent": "TradingAgent-Public-Research/1.0 research@example.invalid",
    "Accept-Encoding": "identity",
}
FETCH_TIMEOUT_SECONDS = 30
MAX_TRANSIENT_FETCH_ATTEMPTS = 3
FETCH_BACKOFF_SECONDS = 2


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    last_error: Exception | None = None
    for attempt in range(1, MAX_TRANSIENT_FETCH_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_SECONDS) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                raise
            last_error = exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
        if attempt < MAX_TRANSIENT_FETCH_ATTEMPTS:
            time.sleep(FETCH_BACKOFF_SECONDS * attempt)
    raise last_error or RuntimeError("SEC_FETCH_FAILED")


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


def _extract_initial_8k_filing_date(primary_text: str) -> str | None:
    """Extract a narrowly scoped explicit Initial Form 8-K filing date from an amendment."""
    compact = re.sub(r"\\s+", " ", primary_text)
    match = re.search(
        r"Initial Form 8-K.{0,500}?filed.{0,120}?(January|February|March|April|May|June|July|August|September|October|November|December)\\s+"
        r"(\\d{1,2}),\\s+(\\d{4})",
        compact,
        flags=re.I,
    )
    if not match:
        return None
    return f"{match.group(1).title()} {match.group(2)}, {match.group(3)}"


def _resolve_amendment_parent(
    originals: list[dict],
    target: dict,
) -> tuple[dict | None, str]:
    """Resolve an 8-K/A parent using explicit source lineage first, else same report date."""
    explicit_filing_date = target.get("initial_8k_filing_date")
    if explicit_filing_date:
        candidates = [
            row
            for row in originals
            if row.get("filing_date") == explicit_filing_date
            and row.get("acceptance_datetime")
            and target.get("acceptance_datetime")
            and row["acceptance_datetime"] < target["acceptance_datetime"]
        ]
        if len(candidates) == 1:
            return candidates[0], "explicit_initial_8k_filing_date"
        if len(candidates) > 1:
            return None, "explicit_initial_8k_filing_date_ambiguous"

    parent = _nearest_prior(originals, target)
    return (parent, "same_report_date_acceptance") if parent else (None, "unresolved")


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
        prior_boundary_10ks: list[dict] = []
        earnings: list[dict] = []
        tenk_amendments: list[dict] = []
        earnings_amendments: list[dict] = []

        prior_10k_indices = [
            i for i, form in enumerate(forms)
            if form == "10-K"
            and i < len(dates)
            and dates[i]
            and dates[i] < START
        ]
        latest_prior_10k_index = (
            max(prior_10k_indices, key=lambda i: dates[i])
            if prior_10k_indices else None
        )

        for i, form in enumerate(forms):
            filing_date = dates[i] if i < len(dates) else None
            if form not in {"10-K", "10-K/A", "8-K", "8-K/A"}:
                continue
            in_window = bool(filing_date and START <= filing_date <= END)
            prior_boundary = i == latest_prior_10k_index
            if not (in_window or prior_boundary):
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
                "in_control_window": in_window,
                "prior_10k_boundary": prior_boundary,
                "exhibit_99_1": False,
                "earnings_release_marker": False,
                "primary_publication_terms_marker": False,
                "is_eligible_earnings_release_8k": False,
            }

            if form == "10-K":
                (prior_boundary_10ks if prior_boundary else tenks).append(row)
            elif form == "10-K/A":
                tenk_amendments.append(row)
            elif form in {"8-K", "8-K/A"}:
                try:
                    _, _, index_page = (
                        None,
                        None,
                        fetch(
                            "https://www.sec.gov/Archives/edgar/data/"
                            f"{int(cik)}/{accession_number.replace('-', '')}/"
                            f"{accession_number}-index-headers.html"
                        ),
                    )
                    index_text = index_page.decode("utf-8", errors="replace")
                    row["exhibit_99_1"] = bool(
                        re.search(r"EXHIBIT\s+99\.1", index_text, flags=re.I)
                    )
                    row["earnings_release_marker"] = bool(
                        re.search(r"EARNINGS\s+RELEASE|PRESS\s+RELEASE", index_text, flags=re.I)
                    )
                except Exception as exc:
                    row["index_header_fetch_error"] = type(exc).__name__ + ":" + str(exc)
                if form == "8-K":
                    earnings.append(row)
                    try:
                        _, _, primary_page = fetch(
                            "https://www.sec.gov/Archives/edgar/data/"
                            f"{int(cik)}/{accession_number.replace('-', '')}/"
                            f"{row['primary_document']}"
                        )
                        primary_text = primary_page.decode("utf-8", errors="replace")
                        row["primary_publication_terms_marker"] = bool(
                            re.search(
                                r"EARNINGS|FINANCIAL\s+RESULTS|QUARTERLY\s+RESULTS|FULL[-\s]?YEAR\s+RESULTS",
                                primary_text,
                                flags=re.I,
                            )
                        )
                    except Exception as exc:
                        row["primary_fetch_error"] = type(exc).__name__ + ":" + str(exc)
                    row["is_eligible_earnings_release_8k"] = bool(
                        "2.02" in str(item_field).split(",")
                        or row["exhibit_99_1"]
                        or row["earnings_release_marker"]
                        or row["primary_publication_terms_marker"]
                    )
                else:
                    try:
                        _, _, primary_page = fetch(
                            "https://www.sec.gov/Archives/edgar/data/"
                            f"{int(cik)}/{accession_number.replace('-', '')}/"
                            f"{row['primary_document']}"
                        )
                        primary_text = primary_page.decode("utf-8", errors="replace")
                        row["initial_8k_filing_date"] = _extract_initial_8k_filing_date(primary_text)
                    except Exception as exc:
                        row["primary_fetch_error"] = type(exc).__name__ + ":" + str(exc)
                    earnings_amendments.append(row)

        # Prefer exact fiscal/report-date alignment. When SEC's 8-K reportDate
        # denotes the earnings-release filing date rather than the 10-K fiscal
        # period end, fall back to the deterministic reporting-cycle interval:
        # latest eligible Item 2.02 8-K strictly after the preceding in-window
        # 10-K acceptance (when one exists) and strictly before the target 10-K.
        # This remains source/PIT-only and introduces no outcome information.
        pairs = []
        unmatched = []
        tenks_sorted = sorted(tenks, key=_acceptance_key)
        annual_all_sorted = sorted(
            [*prior_boundary_10ks, *tenks],
            key=_acceptance_key,
        )
        pairing_rule = (
            "latest eligible Item-2.02/Exhibit-99.1-style 8-K by SEC acceptance "
            "within the interval (preceding 10-K acceptance, target 10-K acceptance]"
        )
        for tenk in tenks_sorted:
            lower_bounds = [
                prior.get("acceptance_datetime")
                for prior in annual_all_sorted
                if prior.get("acceptance_datetime")
                and tenk.get("acceptance_datetime")
                and prior["acceptance_datetime"] < tenk["acceptance_datetime"]
            ]
            lower_bound = max(lower_bounds) if lower_bounds else None
            interval_candidates = [
                candidate
                for candidate in earnings
                if candidate.get("is_eligible_earnings_release_8k") is True
                and candidate.get("acceptance_datetime")
                and tenk.get("acceptance_datetime")
                and candidate["acceptance_datetime"] <= tenk["acceptance_datetime"]
                and (lower_bound is None or candidate["acceptance_datetime"] > lower_bound)
            ]
            event = max(interval_candidates, key=_acceptance_key) if interval_candidates else None
            pairing_method = "acceptance_interval"
            if event is None:
                unmatched.append(
                    {
                        "ten_k_accession": tenk.get("accession"),
                        "report_date": tenk.get("report_date"),
                        "pairing_lower_bound_acceptance": lower_bound,
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
                    "pairing_method": pairing_method,
                    "pairing_lower_bound_acceptance": lower_bound,
                    "event_report_date": event.get("report_date"),
                    "exact_report_date_match": event.get("report_date") == tenk.get("report_date"),
                    "acceptance_order_valid": (
                        event["acceptance_datetime"] <= tenk["acceptance_datetime"]
                        and (lower_bound is None or event["acceptance_datetime"] > lower_bound)
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
                if kind == "8-K/A":
                    parent, lineage_resolution_method = _resolve_amendment_parent(originals, row)
                else:
                    parent = _nearest_prior(originals, row)
                    lineage_resolution_method = "same_report_date_acceptance" if parent else "unresolved"
                item = {
                    "amendment_form": kind,
                    "amendment_accession": row.get("accession"),
                    "report_date": row.get("report_date"),
                    "initial_8k_filing_date": row.get("initial_8k_filing_date"),
                    "lineage_resolution_method": lineage_resolution_method,
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
            "prior_boundary_10k_count": len(prior_boundary_10ks),
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
            "pairing_rule": pairing_rule,
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
        "network_retry_policy": {
            "timeout_seconds": FETCH_TIMEOUT_SECONDS,
            "max_transient_attempts": MAX_TRANSIENT_FETCH_ATTEMPTS,
            "backoff_seconds_per_attempt": FETCH_BACKOFF_SECONDS,
            "retryable_http_statuses": [408, 425, 429, 500, 502, 503, 504],
        },
        "pairing_rule": (
            "exact report_date preferred; otherwise latest eligible Item-2.02 "
            "8-K by SEC acceptance within the target 10-K reporting cycle, "
            "bounded below by the preceding in-window 10-K acceptance"
        ),
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
