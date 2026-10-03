"""Q130-R1 Wikimedia Pageviews historical attention source probe.

Source/PIT feasibility only. No prices, returns, holdouts, ranking, selection,
tuning, performance authorization, promotion or live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ARTICLES = {
    "SPGI": "S&P Global",
    "NDAQ": "Nasdaq",
    "AMP": "Ameriprise Financial",
    "RJF": "Raymond James",
    "WMB": "Williams Companies",
    "VLO": "Valero Energy",
    "DVN": "Devon Energy",
    "EMN": "Eastman Chemical",
}
START = "20250920"
END = "20250924"
BASE_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"
UA = "trading-agent-public/Q130R1-wikimedia-attention-source/1"

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def article_url(title: str) -> str:
    encoded = urllib.parse.quote(title.replace(" ", "_"), safe="_")
    return f"{BASE_URL}/{encoded}/daily/{START}/{END}"

def fetch(url: str) -> tuple[int, bytes, dict[str, str]]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return int(getattr(response, "status", 200)), response.read(), {
                k.lower(): v for k, v in response.headers.items()
            }
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), {}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"WIKIMEDIA_TRANSPORT_ERROR:{url}:{exc}") from exc

def parse_items(body: bytes) -> list[dict[str, object]]:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("WIKIMEDIA_INVALID_JSON") from exc
    items = payload.get("items")
    if not isinstance(items, list):
        raise RuntimeError("WIKIMEDIA_ITEMS_MISSING")
    out: list[dict[str, object]] = []
    for item in items:
        if not isinstance(item, dict):
            raise RuntimeError("WIKIMEDIA_ITEM_NOT_OBJECT")
        timestamp = item.get("timestamp")
        views = item.get("views")
        if not isinstance(timestamp, str) or not timestamp:
            raise RuntimeError("WIKIMEDIA_TIMESTAMP_MISSING")
        if not isinstance(views, (int, float)) or isinstance(views, bool) or not math.isfinite(float(views)) or views < 0:
            raise RuntimeError(f"WIKIMEDIA_VIEWS_INVALID:{timestamp}")
        out.append({"timestamp": timestamp, "views": int(views)})
    return out

def compile_items(items: list[dict[str, object]]) -> dict[str, int]:
    compiled: dict[str, int] = {}
    for item in sorted(items, key=lambda x: str(x["timestamp"])):
        ts = str(item["timestamp"])
        compiled[ts] = int(item["views"])
    return compiled

def mutation_tests() -> dict[str, bool]:
    base = [
        {"timestamp": "20250920", "views": 12},
        {"timestamp": "20250921", "views": 18},
    ]
    future = base + [{"timestamp": "20250925", "views": 999999}]
    return {
        "input_order_invariance": compile_items(base) == compile_items(list(reversed(base))),
        "future_date_invariance": compile_items(base) == {
            k: v for k, v in compile_items(future).items() if k <= END,
        },
    }

def run(output: Path) -> dict[str, object]:
    observations: dict[str, object] = {}
    for symbol, title in ARTICLES.items():
        url = article_url(title)
        status, body, headers = fetch(url)
        if status != 200:
            raise RuntimeError(f"WIKIMEDIA_HTTP_{status}:{symbol}")
        items = parse_items(body)
        compiled = compile_items(items)
        observations[symbol] = {
            "article": title,
            "source_url": url,
            "source_sha256": sha256(body),
            "response_headers": {
                "content_type": headers.get("content-type"),
                "last_modified": headers.get("last-modified"),
                "etag": headers.get("etag"),
            },
            "item_count": len(items),
            "compiled_daily_values": compiled,
            "status": "PASS" if compiled else "FAIL_NO_DATA",
        }
        if not compiled:
            raise RuntimeError(f"WIKIMEDIA_NO_DATA:{symbol}")

    mutation = mutation_tests()
    result: dict[str, object] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-130R1-WIKIMEDIA-ATTENTION-SOURCE",
        "status": "Q130R1_SOURCE_FEASIBILITY_COMPLETED",
        "fixed_articles": ARTICLES,
        "feasibility_window": {"start": START, "end": END},
        "source": {
            "provider": "Wikimedia",
            "dataset": "public pageviews",
            "endpoint_template": f"{BASE_URL}/{{ARTICLE}}/daily/{START}/{END}",
            "coverage_start_documented": "2015-05-01",
            "granularity": "daily",
        },
        "observations": observations,
        "mutation_tests": mutation,
        "pit": {
            "historical_source_available": True,
            "exact_first_publication_time_proven": False,
            "revision_lineage_proven": False,
            "same_day_formal_use_allowed": False,
        },
        "scientific_boundary": {
            "performance": False,
            "holdout": False,
            "ranking": False,
            "selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "promotion": False,
            "live_execution": False,
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
        "symbols": len(ARTICLES),
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
