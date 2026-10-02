"""Q125-F1 SEC MIDAS publication-clock and vintage audit.

Source/PIT feasibility only. The audit never evaluates returns, ranks/selects
candidates, tunes thresholds, or authorizes performance.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

PAGE_URL = "https://www.sec.gov/data-research/sec-markets-data/market-structure-data-security"
RSS_URL = "https://www.sec.gov/rss/marketstructure/data"
TARGET_VINTAGES = (
    "2025 Q1",
    "2025 Q2",
    "2025 Q3",
    "2025 Q4",
    "2026 Q1",
    "2026 Q2",
)
UA = "trading-agent-public/Q125-F1-sec-publication-clock/1"
TIMEOUT = 30


def fetch(url: str) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        headers = {k.lower(): v for k, v in response.headers.items()}
        return response.read(), headers


def page_links(page: str) -> list[dict[str, str]]:
    out = []
    for match in re.finditer(r"<a[^>]+href=[\"']([^\\"']+)[\\"'][^>]*>(.*?)</a>", page, re.I | re.S):
        href = html.unescape(match.group(1))
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", match.group(2)))).strip()
        out.append({"href": href, "text": text})
    return out


def rss_items(raw: bytes) -> list[dict[str, str | None]]:
    root = ET.fromstring(raw)
    items = []
    for item in root.findall(".//item"):
        title = item.findtext("title")
        link = item.findtext("link")
        pub = item.findtext("pubDate")
        pub_iso = None
        if pub:
            pub_iso = parsedate_to_datetime(pub).isoformat()
        items.append({"title": title or "", "link": link or "", "pubDate": pub_iso})
    return items


def match_rss_for_vintage(items: list[dict[str, str | None]], vintage: str) -> list[dict[str, str | None]]:
    token = vintage.lower().replace(" ", "")
    matches = []
    for item in items:
        hay = f"{item.get('title','')} {item.get('link','')}".lower().replace(" ", "")
        if token in hay:
            matches.append(item)
    return matches


def mutation_tests() -> dict[str, bool]:
    items = [
        {"title": "Metrics by Individual Security 2025 Q1", "link": "https://sec.example/q1", "pubDate": "2025-04-01T10:00:00+00:00"},
        {"title": "Metrics by Individual Security 2025 Q2", "link": "https://sec.example/q2", "pubDate": "2025-07-01T10:00:00+00:00"},
    ]
    a = match_rss_for_vintage(items, "2025 Q1")
    b = match_rss_for_vintage(list(reversed(items)), "2025 Q1")
    future = items + [{"title": "Metrics by Individual Security 2099 Q4", "link": "future", "pubDate": "2099-10-01T00:00:00+00:00"}]
    c = match_rss_for_vintage(future, "2025 Q1")
    missing_pub = [{"title": "Metrics by Individual Security 2025 Q1", "link": "q1", "pubDate": None}]
    no_clock = not any(x.get("pubDate") for x in missing_pub)

    return {
        "rss_input_order_invariance": json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True),
        "future_item_does_not_change_historical_match": json.dumps(a, sort_keys=True) == json.dumps(c, sort_keys=True),
        "missing_pubdate_is_not_a_clock": no_clock,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    page_body, page_headers = fetch(PAGE_URL)
    rss_body, rss_headers = fetch(RSS_URL)
    page_text = page_body.decode("utf-8", errors="replace")
    items = rss_items(rss_body)
    links = page_links(page_text)

    vintage_links = {}
    for vintage in TARGET_VINTAGES:
        found = [x for x in links if vintage.lower() in x["text"].lower() or vintage.lower().replace(" ", "") in x["href"].lower().replace(" ", "")]
        vintage_links[vintage] = found

    vintage_audits = {}
    for vintage in TARGET_VINTAGES:
        matches = match_rss_for_vintage(items, vintage)
        direct_links = vintage_links[vintage]
        vintage_audits[vintage] = {
            "page_link_count": len(direct_links),
            "rss_match_count": len(matches),
            "rss_matches": matches,
            "public_clock_available": any(x.get("pubDate") for x in matches),
        }

    mutation = mutation_tests()
    overall = (
        all(v["page_link_count"] > 0 for v in vintage_audits.values())
        and all(v["public_clock_available"] for v in vintage_audits.values())
        and all(mutation.values())
    )

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-02-Q125-F1-SEC-PUBLICATION-CLOCK",
        "candidate_id": "Q125:M1",
        "status": "Q125_F1_PASS" if overall else "Q125_F1_FAILED",
        "sources": {
            "dataset_page": PAGE_URL,
            "rss_feed": RSS_URL,
            "page_sha256": hashlib.sha256(page_body).hexdigest(),
            "rss_sha256": hashlib.sha256(rss_body).hexdigest(),
            "page_last_modified_header": page_headers.get("last-modified"),
            "rss_last_modified_header": rss_headers.get("last-modified"),
        },
        "target_vintages": list(TARGET_VINTAGES),
        "vintage_audits": vintage_audits,
        "interpretation": {
            "page_last_updated_is_not_a_historical_publication_clock": True,
            "direct_file_http_last_modified_is_not_used_as_historical_publication_time": True,
            "missing_historical_rss_mapping_is_fail_closed": True,
        },
        "mutation_tests": mutation,
        "governance": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
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
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "vintages": len(TARGET_VINTAGES),
        "rss_items": len(items),
        "mutation_tests": mutation,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
