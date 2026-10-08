"""Fresh-symbol, fixed-rule Q218 independent replication.

This is a separate replication implementation. It never imports the original
Q218 gate functions or performance output, and it never changes the parent
trial. It produces one immutable per-symbol receipt for GOOGL/META/ORCL/PFE.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "research/governance/q218_independent_replication_contract_2026_10_08.json"
PARENT_CONTRACT_PATH = ROOT / "research/governance/q218_performance_contract_2026_10_08.json"
TRIAL_ID = "T-2026-10-08-Q218-REPLICATION-01"
PARENT_TRIAL_ID = "T-2026-10-08-Q218-PERFORMANCE-01"
SYMBOLS = {"GOOGL": "1652044", "META": "1326801", "ORCL": "1341439", "PFE": "78003"}
START = "2025-01-01"
END = "2026-10-05"
CUTOFF = "2026-10-05T23:59:59Z"
SEC_UA = "DWR-debug/trading-agent-public Q218 independent replication/1.0 research@example.invalid"
YAHOO_UA = "DWR-debug/trading-agent-public Q218 independent replication market/1.0 research@example.invalid"
MAX_ATTEMPTS = 5
BUCKETS = 64
TOKEN_RE = re.compile(r"[a-z0-9]+")
NY = ZoneInfo("America/New_York")


def canonical(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fp(v: Any) -> str:
    return hashlib.sha256(canonical(v).encode("utf-8")).hexdigest()


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url: str, headers: dict[str, str]) -> bytes:
    last: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                raise
            last = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(min(16, 2 ** (attempt - 1)))
    raise RuntimeError(f"FETCH_FAILED:{url}:{last}")


def load_contract() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    parent = json.loads(PARENT_CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract.get("replication_trial_id") != TRIAL_ID or contract.get("status") != "FROZEN_REPLICATION_CONTRACT":
        raise RuntimeError("replication contract not frozen")
    if parent.get("trial_id") != PARENT_TRIAL_ID:
        raise RuntimeError("parent trial identity mismatch")
    if sha_file(PARENT_CONTRACT_PATH) != contract.get("parent_contract_sha256"):
        raise RuntimeError("parent contract fingerprint mismatch")
    if contract.get("fresh_symbol_disjoint") is not True:
        raise RuntimeError("fresh_symbol_disjoint must be true")
    parent_features = parent.get("feature_construction", {})
    inherited_features = contract.get("feature_construction_inheritance", {})
    if inherited_features.get("topic_hash_buckets") != parent_features.get("fixed_constants", {}).get("topic_hash_buckets"):
        raise RuntimeError("feature bucket inheritance mismatch")
    if inherited_features.get("features") != list(parent_features.get("features", {}).keys()):
        raise RuntimeError("feature identity inheritance mismatch")
    for key in ("holding_sessions", "entry", "exit", "outcome", "trading_calendar"):
        if contract.get("outcome_inheritance", {}).get(key) != parent.get("outcome_contract", {}).get(key):
            raise RuntimeError(f"outcome inheritance mismatch:{key}")
    return contract


def acceptance_datetime(header: bytes) -> tuple[str, str]:
    text = header.decode("utf-8", errors="replace")
    m = re.search(r"<ACCEPTANCE-DATETIME>\s*([0-9]{14})", text, re.I)
    if not m:
        raise RuntimeError("ACCEPTANCE_DATETIME_MISSING")
    raw = m.group(1)
    aware = datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=NY)
    return raw, aware.isoformat()


def get_header(cik: str, accession: str, out_root: Path) -> dict[str, str]:
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{accession}-index-headers.html"
    raw = fetch(url, {"User-Agent": SEC_UA, "Accept-Encoding": "identity"})
    rel = Path("sec/headers") / f"{accession}.html"
    path = out_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    raw14, aware = acceptance_datetime(raw)
    return {"accession": accession, "url": url, "path": str(rel), "sha256": sha_bytes(raw), "acceptance_raw": raw14, "acceptance_datetime": aware}


def get_doc(cik: str, accession: str, document: str, out_root: Path) -> dict[str, str]:
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{document}"
    raw = fetch(url, {"User-Agent": SEC_UA, "Accept-Encoding": "identity"})
    rel = Path("sec/documents") / f"{accession}__{document}"
    path = out_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {"accession": accession, "url": url, "path": str(rel), "sha256": sha_bytes(raw)}


def submission_snapshot(cik: str, out_root: Path) -> dict[str, Any]:
    url = f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
    raw = fetch(url, {"User-Agent": SEC_UA, "Accept-Encoding": "identity"})
    rel = Path("sec/submissions") / f"CIK{int(cik):010d}.json"
    path = out_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {"data": json.loads(raw.decode("utf-8")), "manifest": {"url": url, "path": str(rel), "sha256": sha_bytes(raw)}}


def next_xnys_session(closure_iso: str) -> str:
    closure = pd.Timestamp(closure_iso)
    if closure.tzinfo is None:
        closure = closure.tz_localize("UTC")
    else:
        closure = closure.tz_convert("UTC")
    cal = xcals.get_calendar("XNYS")
    schedule = cal.schedule.loc[START:str((pd.Timestamp(END) + pd.Timedelta(days=10)).date())]
    column = "market_open" if "market_open" in schedule.columns else "open"
    eligible = schedule[schedule[column] > closure]
    if eligible.empty:
        raise RuntimeError(f"NO_XNYS_SESSION_AFTER:{closure_iso}")
    return eligible.index[0].date().isoformat()


def yahoo_bar(symbol: str, session: str, out_root: Path) -> dict[str, Any]:
    from datetime import date
    d = date.fromisoformat(session)
    period1 = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) - 3 * 86400
    period2 = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) + 4 * 86400
    query = urllib.parse.urlencode({"period1": period1, "period2": period2, "interval": "1d", "events": "div,splits", "includePrePost": "false"})
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol, safe='')}?{query}"
    raw = fetch(url, {"User-Agent": YAHOO_UA, "Accept": "application/json", "Accept-Encoding": "identity"})
    rel = Path("market_raw") / f"{symbol}_{session}.json"
    path = out_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    payload = json.loads(raw.decode("utf-8"))
    result = payload["chart"]["result"][0]
    tz = ZoneInfo(result.get("meta", {}).get("exchangeTimezoneName", "America/New_York"))
    timestamps = result.get("timestamp") or []
    quote = result.get("indicators", {}).get("quote", [{}])[0]
    matches = []
    for ts, op, cl in zip(timestamps, quote.get("open", []), quote.get("close", [])):
        local = datetime.fromtimestamp(int(ts), tz=tz).date().isoformat()
        if local == session:
            matches.append((op, cl))
    if len(matches) != 1:
        raise RuntimeError(f"YAHOO_SESSION_BAR_NOT_UNIQUE:{symbol}:{session}:{len(matches)}")
    op, cl = matches[0]
    if op is None or cl is None or not math.isfinite(float(op)) or not math.isfinite(float(cl)) or float(op) <= 0 or float(cl) <= 0:
        raise RuntimeError(f"YAHOO_INVALID_BAR:{symbol}:{session}")
    return {
        "symbol": symbol,
        "session": session,
        "open": float(op),
        "close": float(cl),
        "raw_response_path": str(rel),
        "raw_response_sha256": sha_bytes(raw),
        "source_url": url,
    }


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self.skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self.skip:
            self.skip -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.parts.append(data)


def tokens(raw: bytes) -> list[str]:
    decoded = html.unescape(raw.decode("utf-8", errors="replace"))
    p = TextParser()
    p.feed(decoded)
    return TOKEN_RE.findall(re.sub(r"\s+", " ", " ".join(p.parts)).strip().lower())


def bucket(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16) % BUCKETS


def freq(values: list[str]) -> list[float]:
    counts = [0] * BUCKETS
    for v in values:
        counts[bucket(v)] += 1
    total = sum(counts)
    return [x / total for x in counts] if total else [0.0] * BUCKETS


def feature_state(mandatory_raw: bytes, voluntary_raw: bytes) -> dict[str, float]:
    m = tokens(mandatory_raw)
    v = tokens(voluntary_raw)
    mp = {bucket(x) for x in m}
    vp = {bucket(x) for x in v}
    union = len(mp | vp)
    coverage = 1.0 - (len(mp & vp) / union if union else 1.0)
    mf, vf = freq(m), freq(v)
    omission = sum(abs(a - b) for a, b in zip(mf, vf)) / BUCKETS
    mb = [" ".join(p) for p in zip(m, m[1:])]
    vb = [" ".join(p) for p in zip(v, v[1:])]
    aa, bb = freq(mb), freq(vb)
    na = math.sqrt(sum(x*x for x in aa)); nb = math.sqrt(sum(x*x for x in bb))
    framing = 1.0 if (na == 0 or nb == 0) and (any(aa) or any(bb)) else (
        0.0 if na == 0 and nb == 0 else 1.0 - sum(x*y for x,y in zip(aa,bb))/(na*nb)
    )
    return {
        "topic_coverage_gap_mandatory_vs_voluntary": coverage,
        "omission_asymmetry_by_topic": omission,
        "secondary_framing_gap": framing,
    }


def event_pairs(data: dict[str, Any], cik: str, out_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", [])
    reports = recent.get("reportDate", [])
    items = recent.get("items", [])
    target_10k_indices = [i for i, f in enumerate(forms) if f == "10-K" and i < len(dates) and START <= str(dates[i]) <= END]
    prior_indices = [i for i, f in enumerate(forms) if f == "10-K" and i < len(dates) and str(dates[i]) < START]
    latest_prior = max(prior_indices, key=lambda i: dates[i]) if prior_indices else None

    tenks = []
    prior_boundary = []
    eligible_8k = []
    amendments = []
    for i, form in enumerate(forms):
        fd = dates[i] if i < len(dates) else None
        if not fd:
            continue
        in_window = START <= fd <= END
        is_prior = i == latest_prior
        if not (in_window or is_prior):
            continue
        accession = str(accessions[i])
        report = reports[i] if i < len(reports) else None
        item_field = str(items[i] if i < len(items) else "")
        if form == "10-K":
            row = {"form": form, "filing_date": fd, "report_date": report, "accession": accession, "primary_document": docs[i] if i < len(docs) else None, **get_header(cik, accession, out_root), "in_control_window": in_window, "prior_boundary_10k": is_prior}
            tenks.append(row)
            if is_prior:
                prior_boundary.append(row)
        elif form == "10-K/A":
            amendments.append({"form": form, "filing_date": fd, "accession": accession})
    for i, form in enumerate(forms):
        fd = dates[i] if i < len(dates) else None
        if form != "8-K" or not fd or not (START <= fd <= END):
            if form == "8-K/A" and fd and START <= fd <= END:
                amendments.append({"form": form, "filing_date": fd, "accession": str(accessions[i])})
            continue
        item_field = str(items[i] if i < len(items) else "")
        if not re.search(r"(^|[,;\s])2\.02([,;\s]|$)", item_field, flags=re.I):
            continue
        accession = str(accessions[i])
        eligible_8k.append({
            "form": form, "filing_date": fd, "report_date": reports[i] if i < len(reports) else None,
            "accession": accession, "primary_document": docs[i] if i < len(docs) else None,
            "items": item_field, **get_header(cik, accession, out_root)
        })

    ordered = sorted(tenks, key=lambda r: (r["acceptance_raw"], r["accession"]))
    prior_annual = sorted([*prior_boundary, *ordered], key=lambda r: (r["acceptance_raw"], r["accession"]))
    pairs = []
    unmatched = []
    for tenk in ordered:
        lower = max(
            (r["acceptance_raw"] for r in prior_annual if r["acceptance_raw"] and r["acceptance_raw"] < tenk["acceptance_raw"]),
            default=None,
        )
        candidates = [
            e for e in eligible_8k
            if e["acceptance_raw"] <= tenk["acceptance_raw"] and (lower is None or e["acceptance_raw"] > lower)
        ]
        event = max(candidates, key=lambda r: (r["acceptance_raw"], r["accession"])) if candidates else None
        if not event:
            unmatched.append({"ten_k_accession": tenk["accession"], "report_date": tenk.get("report_date"), "lower_bound_acceptance": lower})
            continue
        closure_raw = max(tenk["acceptance_datetime"], event["acceptance_datetime"])
        session = next_xnys_session(closure_raw)
        pairs.append({
            "issuer": None,
            "ten_k_accession": tenk["accession"],
            "ten_k_acceptance_datetime": tenk["acceptance_datetime"],
            "item_2_02_8k_accession": event["accession"],
            "item_2_02_8k_acceptance_datetime": event["acceptance_datetime"],
            "pair_closure_clock": closure_raw,
            "action_session": session,
            "report_date": tenk.get("report_date"),
            "event_report_date": event.get("report_date"),
            "exact_report_date_match": event.get("report_date") == tenk.get("report_date"),
            "lower_bound_acceptance": lower,
            "acceptance_order_valid": event["acceptance_raw"] <= tenk["acceptance_raw"] and (lower is None or event["acceptance_raw"] > lower),
        })
    if unmatched:
        raise RuntimeError("UNMATCHED_10K:" + json.dumps(unmatched, sort_keys=True))
    return pairs, tenks, eligible_8k


def replicate(symbol: str, output_root: Path) -> dict[str, Any]:
    if symbol not in SYMBOLS:
        raise ValueError(symbol)
    contract = load_contract()
    cik = SYMBOLS[symbol]
    output_root.mkdir(parents=True, exist_ok=True)
    snap = submission_snapshot(cik, output_root)
    pairs, tenks, eligible_8k = event_pairs(snap["data"], cik, output_root)
    docs_manifest: list[dict[str, Any]] = []
    bars: list[dict[str, Any]] = []
    for pair in pairs:
        pair["issuer"] = symbol
        for source in (next(r for r in tenks if r["accession"] == pair["ten_k_accession"]), next(r for r in eligible_8k if r["accession"] == pair["item_2_02_8k_accession"])):
            doc = get_doc(cik, source["accession"], source["primary_document"], output_root)
            docs_manifest.append({
                **source, **doc
            })
        bars.append(yahoo_bar(symbol, pair["action_session"], output_root))
    by_acc = {d["accession"]: d for d in docs_manifest}
    events = []
    for pair in pairs:
        m = by_acc[pair["ten_k_accession"]]
        v = by_acc[pair["item_2_02_8k_accession"]]
        outcome = float(next(b for b in bars if b["session"] == pair["action_session"])["close"]) / float(next(b for b in bars if b["session"] == pair["action_session"])["open"]) - 1.0
        events.append({
            **pair,
            "features": feature_state((output_root / m["path"]).read_bytes(), (output_root / v["path"]).read_bytes()),
            "outcome": outcome,
        })
    receipt = {
        "schema_version": "1.0",
        "record_type": "q218_independent_replication_symbol_receipt",
        "candidate_id": "Q218",
        "replication_trial_id": TRIAL_ID,
        "parent_trial_id": PARENT_TRIAL_ID,
        "symbol": symbol,
        "cik": cik,
        "fixed_window": {"start": START, "end": END},
        "future_cutoff_utc": CUTOFF,
        "event_count": len(events),
        "events": events,
        "documents": docs_manifest,
        "market_bars": bars,
        "source_snapshot": snap["manifest"],
        "acceptance_clock": "America/New_York raw 14-digit preserved; aware conversion before XNYS comparison",
        "feature_construction": {"bucket_count": BUCKETS, "deterministic": True, "no_learned_vocabulary": True, "no_weighting": True},
        "performance_evaluation": True,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "parameter_search": False,
        "threshold_search": False,
        "horizon_search": False,
        "asset_search": False,
        "variant_search": False,
        "post_pass_optimization": False,
        "performance_output_reuse_for_rule_changes": False,
        "candidate_ranking": False,
        "promotion_decision": False,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    if any(e["action_session"] > END for e in events):
        raise RuntimeError("ACTION_SESSION_AFTER_CUTOFF")
    receipt["receipt_fingerprint"] = fp(receipt)
    target = output_root / f"q218_replication_{symbol}.json"
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", choices=sorted(SYMBOLS), required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    result = replicate(args.symbol, args.output_dir)
    print(json.dumps({"symbol": result["symbol"], "event_count": result["event_count"], "receipt_fingerprint": result["receipt_fingerprint"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
