"""Deterministic SEC filing-review correspondence source gate for Q228.

Source/PIT structure only. No market outcomes, ranking, tuning or authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = "https://www.sec.gov/search-filings/edgar-search-assistance/how-search-edgar-correspondence"
SEARCH = "https://www.sec.gov/edgar/search/"
UA = "TradingAgent-Public-Q228-SEC-Correspondence-Gate/1.0"
CONTEXT_RADIUS = 100


def fetch(url):
    """Return a bounded source response tuple including the final redirect URL."""
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,*/*",
            "Accept-Encoding": "identity",
        },
    )
    ctx = ssl.create_default_context()
    with urlopen(req, timeout=45, context=ctx) as response:
        body = response.read()
        final_url = response.geturl() if hasattr(response, "geturl") else url
        return int(getattr(response, "status", 200)), dict(response.headers.items()), body, final_url


def _header(headers, wanted):
    for key, value in headers.items():
        if str(key).lower() == wanted.lower():
            return str(value)
    return None


def _element_text(body, element):
    match = re.search(
        rf"<{element}\b[^>]*>(.*?)</{element}\s*>",
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    value = re.sub(r"<[^>]+>", " ", match.group(1))
    value = html.unescape(value)
    return " ".join(value.split())[:240] or None


def _marker_context(body, marker):
    match = re.search(re.escape(marker), body, flags=re.IGNORECASE)
    if not match:
        return None
    start = max(0, match.start() - CONTEXT_RADIUS)
    end = min(len(body), match.end() + CONTEXT_RADIUS)
    value = re.sub(r"<[^>]+>", " ", body[start:end])
    value = html.unescape(value)
    return " ".join(value.split())[:2 * CONTEXT_RADIUS + len(marker)] or None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = []
    for name, url, markers in [
        ("SEC_CORRESPONDENCE_GUIDANCE", ROOT, ["publicly releases", "20 business days", "UPLOAD", "CORRESP"]),
        ("SEC_EDGAR_SEARCH", SEARCH, ["Filing review correspondence", "Last 10 years"]),
    ]:
        rec = {
            "name": name,
            "url": url,
            "reachable": False,
            "status": None,
            "content_type": None,
            "final_url": None,
            "title": None,
            "h1": None,
            "bytes": 0,
            "sha256": None,
            "missing_markers": [],
            "marker_diagnostics": [],
        }
        try:
            status_code, headers, raw_body, final_url = fetch(url)
            body = raw_body.decode("utf-8", "replace")
            lower_body = body.lower()
            rec.update(
                reachable=(status_code == 200),
                status=status_code,
                content_type=_header(headers, "Content-Type"),
                final_url=final_url,
                title=_element_text(body, "title"),
                h1=_element_text(body, "h1"),
                bytes=len(raw_body),
                sha256=hashlib.sha256(raw_body).hexdigest(),
                missing_markers=[marker for marker in markers if marker.lower() not in lower_body],
                marker_diagnostics=[
                    {
                        "marker": marker,
                        "found": marker.lower() in lower_body,
                        "context": _marker_context(body, marker) if marker.lower() in lower_body else None,
                    }
                    for marker in markers
                ],
            )
        except Exception as error:
            rec["error"] = f"{type(error).__name__}:{error}"
        rows.append(rec)

    good = all(row["reachable"] and not row["missing_markers"] for row in rows)
    payload = {
        "schema_version": 1,
        "task_id": "Q-2026-10-06-Q228-SEC-CORRESPONDENCE-SOURCE-GATE",
        "candidate_id": "Q228",
        "status": "SOURCE_STRUCTURE_READY_NO_PERFORMANCE" if good else "SOURCE_STRUCTURE_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_contract": {
            "public_release_start": "SEC public release program documented in 2005; guidance covers filing reviews for applicable filings after Aug 1 2004",
            "public_observation": "EDGAR public release boundary of the correspondence record",
            "post_review_delay": "SEC guidance describes at least 20 business days after review completion/effectiveness before public release",
            "forms": {"UPLOAD": "SEC-originated letters to filers", "CORRESP": "filer response letters"},
        },
        "results": rows,
        "pit_contract": {
            "public_observation_clock_proven": False,
            "latent_review_start_tradable": False,
            "same_day_use_allowed": False,
            "review_cycle_filing_join_completed": False,
            "future_correspondence_mutation_allowed": False,
        },
        "next_gate": "historical correspondence archive census + deterministic filing/review-cycle identity compiler + public release clock reconstruction + amendment/closure lineage + independent PIT reproduction",
        "scientific_boundary": {
            "performance_authorized": False,
            "holdout_selection_allowed": False,
            "ranking_allowed": False,
            "tuning_allowed": False,
            "promotion_allowed": False,
            "live_execution_allowed": False,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["receipt_fingerprint"] = hashlib.sha256(canonical.encode()).hexdigest()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "receipt_fingerprint": payload["receipt_fingerprint"]}, sort_keys=True))


if __name__ == "__main__":
    main()
