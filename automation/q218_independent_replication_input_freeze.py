"""Freeze a fresh-symbol, PIT-safe Q218 independent replication input bundle.

This module intentionally reimplements the SEC discovery/pairing and market-input
freeze path rather than importing the original Q218 gate functions. It never reads
the original performance outputs except for immutable lineage identifiers in the
replication contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/governance/q218_independent_replication_2026_10_08.json"
TRIAL_ID = "T-2026-10-08-Q218-REPLICATION-01"
START = "2025-01-01"
END = "2026-10-05"
CUTOFF = "2026-10-05T23:59:59Z"
ISSUERS = {
    "GOOGL": "1652044",
    "META": "1326801",
    "ORCL": "1341439",
    "PFE": "78003",
}
MAX_ATTEMPTS = 5
TRANSIENT = {408, 425, 429, 500, 502, 503, 504}
SEC_UA = "DWR-debug/trading-agent-public Q218 fresh-symbol replication/1.0 research@example.invalid"
YAHOO_UA = "DWR-debug/trading-agent-public Q218 fresh-symbol replication market freeze/1.0 research@example.invalid"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fp(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, headers: dict[str, str]) -> bytes:
    last: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in TRANSIENT:
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
        if attempt < MAX_ATTEMPTS:
            time.sleep(min(16, 2 ** (attempt - 1)))
    raise RuntimeError(f"Q218_REPLICATION_FETCH_FAILED:{url}:{last}")


def load_contract() -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["replication_trial_id"] == TRIAL_ID
    assert contract["status"] == "FROZEN_PRE_EXECUTION"
    assert contract["fixed_observation_scope"] == {
        "window_start": START,
        "window_end": END,
        "future_cutoff_utc": CUTOFF,
        "same_day_decision_use_allowed": False,
    }
    assert contract["universe"]["fresh_symbol_disjoint"] is True
    assert contract["universe"]["issuer_ciks"] == ISSUERS
    assert contract["lineage"]["reuse_of_performance_output_for_rule_changes"] is False
    assert contract["lineage"]["post_pass_optimization"] is False
    assert contract["governance"]["performance_authorization"] is False
    assert contract["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    return contract


def archive_base(cik: str, accession: str) -> str:
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession.replace('-', '')}/"
    )


def acceptance_datetime(cik: str, accession: str) -> str:
    raw = fetch(
        archive_base(cik, accession) + f"{accession}-index-headers.html",
        {"User-Agent": SEC_UA, "Accept-Encoding": "identity"},
    )
    text = raw.decode("utf-8", errors="replace")
    m = re.search(r"<ACCEPTANCE-DATETIME>s*([0-9]{14})", text, flags=re.I)
    if not m:
        raise RuntimeError(f"Q218_REPLICATION_ACCEPTANCE_MISSING:{accession}")
    local = datetime.strptime(m.group(1), "%Y%m%d%H%M%S").replace(
        tzinfo=ZoneInfo("America/New_York")
    )
    return local.isoformat()


def load_submissions(cik: str) -> tuple[dict, dict[str, str]]:
    raw = fetch(
        f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json",
        {"User-Agent": SEC_UA, "Accept": "application/json", "Accept-Encoding": "identity"},
    )
    rel = Path("sec/submissions") / f"CIK{int(cik):010d}.json"
    return json.loads(raw.decode("utf-8")), {rel.as_posix(): sha256_bytes(raw)}


def prior_filing_boundary(rows: list[dict]) -> str | None:
    prior = [
        r for r in rows
        if r["form"] == "10-K" and r.get("filing_date") and r["filing_date"] < START
    ]
    return max((r["filing_date"] for r in prior), default=None)


def parent_date_hint(primary_text: str) -> str | None:
    m = re.search(
        r"(?:Initial Form 8-K|Current Report on Form 8-K).*?"
        r"filed with the Securities and Exchange Commission\s+on "
        r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
        primary_text,
        flags=re.I | re.S,
    )
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat()
    except ValueError:
        return None


def discover_issuer(symbol: str, cik: str, root: Path) -> tuple[list[dict], list[dict], dict[str, str]]:
    data, source_hashes = load_submissions(cik)
    recent = data.get("filings", {}).get("recent", {})
    keys = ["form", "filingDate", "reportDate", "accessionNumber", "primaryDocument", "items"]
    length = len(recent.get("accessionNumber", []))
    rows: list[dict] = []
    for i in range(length):
        form = str(recent.get("form", [""] * length)[i] or "")
        filing_date = str(recent.get("filingDate", [""] * length)[i] or "")
        if form not in {"10-K", "10-K/A", "8-K", "8-K/A"}:
            continue
        in_window = bool(filing_date and START <= filing_date <= END)
        if not in_window:
            continue
        accession = str(recent.get("accessionNumber", [""] * length)[i] or "")
        doc = str(recent.get("primaryDocument", [""] * length)[i] or "")
        items = str(recent.get("items", [""] * length)[i] or "")
        row = {
            "symbol": symbol,
            "cik": cik,
            "form": form,
            "filing_date": filing_date,
            "report_date": recent.get("reportDate", [""] * length)[i],
            "accession": accession,
            "primary_document": doc,
            "items": items,
        }
        row["eligible_item_2_02"] = bool(
            form == "8-K" and re.search(r"(^|[,;\s])2\.02([,;\s]|$)", items, flags=re.I)
        )
        rows.append(row)

    prior_date = prior_filing_boundary(rows + [
        {
            "form": form,
            "filing_date": str(recent.get("filingDate", [""] * length)[i] or ""),
        }
        for i, form in enumerate(recent.get("form", []))
        if form == "10-K" and i < len(recent.get("filingDate", []))
    ])
    if prior_date:
        for i in range(length):
            form = str(recent.get("form", [""] * length)[i] or "")
            filing_date = str(recent.get("filingDate", [""] * length)[i] or "")
            if form == "10-K" and filing_date == prior_date and not any(
                x["accession"] == recent.get("accessionNumber", [""] * length)[i] for x in rows
            ):
                rows.append({
                    "symbol": symbol,
                    "cik": cik,
                    "form": "10-K",
                    "filing_date": filing_date,
                    "report_date": recent.get("reportDate", [""] * length)[i],
                    "accession": str(recent.get("accessionNumber", [""] * length)[i] or ""),
                    "primary_document": str(recent.get("primaryDocument", [""] * length)[i] or ""),
                    "items": "",
                    "eligible_item_2_02": False,
                    "prior_boundary": True,
                })
                break

    tenks = [r for r in rows if r["form"] == "10-K" and START <= r["filing_date"] <= END]
    eightks = [r for r in rows if r["form"] == "8-K" and r["eligible_item_2_02"]]
    tenk_ams = [r for r in rows if r["form"] == "10-K/A"]
    eightk_ams = [r for r in rows if r["form"] == "8-K/A"]

    for row in [*tenk_ams, *eightk_ams]:
        raw = fetch(
            archive_base(cik, row["accession"]) + row["primary_document"],
            {"User-Agent": SEC_UA, "Accept": "text/html", "Accept-Encoding": "identity"},
        )
        row["parent_filing_date_hint"] = parent_date_hint(raw.decode("utf-8", errors="replace"))
        header = fetch(
            archive_base(cik, row["accession"]) + f"{row['accession']}-index-headers.html",
            {"User-Agent": SEC_UA, "Accept": "text/html", "Accept-Encoding": "identity"},
        )
        row["acceptance_datetime"] = _parse_acceptance(header, row["accession"])
        source_hashes[f"sec/amendments/{row['accession']}.html"] = sha256_bytes(raw)

    for row in [*tenks, *eightks]:
        header = fetch(
            archive_base(cik, row["accession"]) + f"{row['accession']}-index-headers.html",
            {"User-Agent": SEC_UA, "Accept": "text/html", "Accept-Encoding": "identity"},
        )
        row["acceptance_datetime"] = _parse_acceptance(header, row["accession"])

    tenks = sorted(tenks, key=lambda x: (x["acceptance_datetime"], x["accession"]))
    eightks = sorted(eightks, key=lambda x: (x["acceptance_datetime"], x["accession"]))
    pairs: list[dict] = []
    unmatched: list[str] = []
    all_10k = sorted(
        [x for x in rows if x["form"] == "10-K"],
        key=lambda x: (x.get("acceptance_datetime", ""), x["accession"]),
    )
    for tenk in tenks:
        lower = max(
            (
                x.get("acceptance_datetime")
                for x in all_10k
                if x.get("acceptance_datetime") and x["acceptance_datetime"] < tenk["acceptance_datetime"]
            ),
            default=None,
        )
        candidates = [
            e for e in eightks
            if e["acceptance_datetime"] <= tenk["acceptance_datetime"]
            and (lower is None or e["acceptance_datetime"] > lower)
        ]
        if not candidates:
            unmatched.append(tenk["accession"])
            continue
        event = max(candidates, key=lambda x: (x["acceptance_datetime"], x["accession"]))
        pairs.append({
            "ten_k_accession": tenk["accession"],
            "ten_k_acceptance_datetime": tenk["acceptance_datetime"],
            "item_2_02_8k_accession": event["accession"],
            "item_2_02_8k_acceptance_datetime": event["acceptance_datetime"],
            "pairing_lower_bound_acceptance": lower,
            "exact_report_date_match": event.get("report_date") == tenk.get("report_date"),
            "acceptance_order_valid": True,
        })

    if unmatched:
        raise RuntimeError(f"Q218_REPLICATION_UNMATCHED_10K:{symbol}:{','.join(unmatched)}")

    for pair in pairs:
        for row in (next(x for x in tenks if x["accession"] == pair["ten_k_accession"]),
                    next(x for x in eightks if x["accession"] == pair["item_2_02_8k_accession"])):
            document = fetch(
                archive_base(cik, row["accession"]) + row["primary_document"],
                {"User-Agent": SEC_UA, "Accept": "text/html", "Accept-Encoding": "identity"},
            )
            rel = Path("sec/documents") / f"{row['accession']}.html"
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(document)
            row["document_path"] = rel.as_posix()
            row["document_sha256"] = sha256_bytes(document)
            head_raw = fetch(
                archive_base(cik, row["accession"]) + f"{row['accession']}-index-headers.html",
                {"User-Agent": SEC_UA, "Accept": "text/html", "Accept-Encoding": "identity"},
            )
            head_rel = Path("sec/headers") / f"{row['accession']}.html"
            (root / head_rel).parent.mkdir(parents=True, exist_ok=True)
            (root / head_rel).write_bytes(head_raw)
            row["header_path"] = head_rel.as_posix()
            row["header_sha256"] = sha256_bytes(head_raw)
    return pairs, rows, source_hashes


def _parse_acceptance(raw: bytes, accession: str) -> str:
    text = raw.decode("utf-8", errors="replace")
    m = re.search(r"<ACCEPTANCE-DATETIME>\s*([0-9]{14})", text, flags=re.I)
    if not m:
        raise RuntimeError(f"Q218_REPLICATION_ACCEPTANCE_MISSING:{accession}")
    local = datetime.strptime(m.group(1), "%Y%m%d%H%M%S").replace(
        tzinfo=ZoneInfo("America/New_York")
    )
    return local.isoformat()


def next_xnys_session(closure: datetime) -> str:
    cal = xcals.get_calendar("XNYS")
    schedule = cal.schedule.loc[START:END]
    ts = pd.Timestamp(closure).tz_convert("UTC") if pd.Timestamp(closure).tzinfo else pd.Timestamp(closure).tz_localize("UTC")
    opens = schedule["market_open"] if "market_open" in schedule.columns else schedule["open"]
    eligible = schedule[opens > ts]
    if eligible.empty:
        raise RuntimeError(f"Q218_REPLICATION_NO_ACTION_SESSION:{closure.isoformat()}")
    return eligible.index[0].date().isoformat()


def yahoo(symbol: str, session: str, root: Path) -> dict:
    from datetime import date
    d = date.fromisoformat(session)
    p1 = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) - 3 * 86400
    p2 = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) + 4 * 86400
    query = urllib.parse.urlencode({
        "period1": p1, "period2": p2, "interval": "1d", "events": "div,splits", "includePrePost": "false",
    })
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?{query}"
    raw = fetch(url, {"User-Agent": YAHOO_UA, "Accept": "application/json", "Accept-Encoding": "identity"})
    payload = json.loads(raw.decode("utf-8"))
    result = payload["chart"]["result"][0]
    tz = ZoneInfo(result.get("meta", {}).get("exchangeTimezoneName", "America/New_York"))
    rows = []
    quote = result["indicators"]["quote"][0]
    for ts, op, cl in zip(result["timestamp"], quote["open"], quote["close"]):
        local_date = datetime.fromtimestamp(int(ts), tz=tz).date().isoformat()
        rows.append({"session": local_date, "open": op, "close": cl})
    matches = [x for x in rows if x["session"] == session]
    if len(matches) != 1:
        raise RuntimeError(f"Q218_REPLICATION_MARKET_ROW_MISSING:{symbol}:{session}")
    row = matches[0]
    if any(row[k] is None or not math.isfinite(float(row[k])) or float(row[k]) <= 0 for k in ("open", "close")):
        raise RuntimeError(f"Q218_REPLICATION_MARKET_INVALID:{symbol}:{session}")
    rel = Path("market_raw") / f"{symbol}_{session}.json"
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_bytes(raw)
    row.update({
        "symbol": symbol,
        "session": session,
        "open": float(row["open"]),
        "close": float(row["close"]),
        "raw_response_path": rel.as_posix(),
        "raw_response_sha256": sha256_bytes(raw),
        "source_url": url,
    })
    return row


def freeze(output_root: Path, receipt_path: Path) -> dict:
    contract = load_contract()
    source_hashes: dict[str, str] = {}
    all_pairs: list[dict] = []
    documents: list[dict] = []
    issuer_summaries: dict[str, dict] = {}

    for symbol, cik in ISSUERS.items():
        pairs, rows, hashes = discover_issuer(symbol, cik, output_root)
        source_hashes.update(hashes)
        issuer_summaries[symbol] = {
            "cik": cik,
            "ten_k_count": sum(1 for x in rows if x["form"] == "10-K" and START <= x["filing_date"] <= END),
            "item_2_02_8k_count": sum(1 for x in rows if x["form"] == "8-K" and x.get("eligible_item_2_02")),
            "amendment_count": sum(1 for x in rows if str(x["form"]).endswith("/A")),
            "event_pair_count": len(pairs),
        }
        for pair in pairs:
            tenk = next(x for x in rows if x["accession"] == pair["ten_k_accession"])
            voluntary = next(x for x in rows if x["accession"] == pair["item_2_02_8k_accession"])
            closure = max(
                datetime.fromisoformat(pair["ten_k_acceptance_datetime"]),
                datetime.fromisoformat(pair["item_2_02_8k_acceptance_datetime"]),
            )
            action = next_xnys_session(closure)
            pair = {
                "issuer": symbol,
                "ten_k_accession": pair["ten_k_accession"],
                "item_2_02_8k_accession": pair["item_2_02_8k_accession"],
                "ten_k_acceptance_datetime": pair["ten_k_acceptance_datetime"],
                "item_2_02_8k_acceptance_datetime": pair["item_2_02_8k_acceptance_datetime"],
                "pair_closure_clock": closure.isoformat(),
                "action_session": action,
                "pairing_lower_bound_acceptance": pair["pairing_lower_bound_acceptance"],
                "exact_report_date_match": pair["exact_report_date_match"],
                "acceptance_order_valid": pair["acceptance_order_valid"],
            }
            all_pairs.append(pair)
            for row in (tenk, voluntary):
                documents.append({
                    "issuer": symbol,
                    "cik": cik,
                    "accession": row["accession"],
                    "form": row["form"],
                    "primary_document": row["primary_document"],
                    "path": row["document_path"],
                    "sha256": row["document_sha256"],
                    "header_path": row["header_path"],
                    "header_sha256": row["header_sha256"],
                    "acceptance_datetime": row["acceptance_datetime"],
                })

            if not any(b.get("symbol") == symbol and b.get("session") == action for b in []):
                pass

    # Re-fetch unique market inputs after event closure is known.
    market: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for event in all_pairs:
        key = (event["issuer"], event["action_session"])
        if key not in seen:
            market.append(yahoo(*key, output_root))
            seen.add(key)

    bundle = {
        "schema_version": "1.0",
        "record_type": "q218_independent_replication_input_bundle",
        "candidate_id": "Q218",
        "replication_trial_id": TRIAL_ID,
        "source_performance_trial_id": contract["lineage"]["source_performance_trial_id"],
        "source_performance_report_fingerprint": contract["lineage"]["source_performance_report_fingerprint"],
        "fixed_window": {"start": START, "end": END},
        "future_cutoff_utc": CUTOFF,
        "fresh_symbol_disjoint": True,
        "issuer_ciks": ISSUERS,
        "issuer_summaries": issuer_summaries,
        "events": all_pairs,
        "documents": sorted(
            {d["accession"]: d for d in documents}.values(), key=lambda x: x["accession"]
        ),
        "market_bars": market,
        "source_hashes": sorted(source_hashes.items()),
        "executor_network_access": False,
        "reuse_of_performance_output_for_rule_changes": False,
        "post_pass_optimization": False,
        "governance": contract["governance"],
        "safety": contract["safety"],
    }
    bundle["bundle_fingerprint"] = fp(bundle)
    bundle_path = output_root / "input_bundle_manifest.json"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    receipt = {
        "schema_version": "1.0",
        "record_type": "q218_independent_replication_input_bundle_receipt",
        "candidate_id": "Q218",
        "replication_trial_id": TRIAL_ID,
        "status": "FRESH_SYMBOL_INPUT_BUNDLE_FROZEN",
        "bundle_fingerprint": bundle["bundle_fingerprint"],
        "event_count": len(all_pairs),
        "document_count": len(bundle["documents"]),
        "market_bar_count": len(market),
        "fresh_symbol_disjoint": True,
        "issuer_ciks": ISSUERS,
        "fixed_window": {"start": START, "end": END},
        "executor_network_access": False,
        "reuse_of_performance_output_for_rule_changes": False,
        "post_pass_optimization": False,
        "performance_authorization": False,
        "safety": contract["safety"],
    }
    receipt["receipt_fingerprint"] = fp(receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.output_root, args.receipt), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
