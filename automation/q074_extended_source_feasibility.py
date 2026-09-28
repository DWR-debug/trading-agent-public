from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

TIMEOUT = 30
USER_AGENT = "trading-agent-public/Q074 source-feasibility contact=research"

PROBES = [
    {
        "id": "I7",
        "family": "SEC_13F_INSTITUTIONAL_CROWDING_CHANGE",
        "url": "https://www.sec.gov/Archives/edgar/data/1418814/000141881426000002/0001418814-26-000002-index-headers.html",
        "checks": ["<ACCEPTANCE-DATETIME>", "CONFORMED SUBMISSION TYPE:", "13F-HR"],
        "pit_semantics": "EDGAR acceptance datetime is the public-availability anchor; report period is not the action date.",
    },
    {
        "id": "I8",
        "family": "SEC_8K_EARNINGS_INFORMATION_FLOW",
        "url": "https://www.sec.gov/Archives/edgar/data/1130464/000119312526226896/0001193125-26-226896-index-headers.html",
        "checks": ["<ACCEPTANCE-DATETIME>", "CONFORMED SUBMISSION TYPE:", "8-K"],
        "pit_semantics": "EDGAR acceptance datetime is the public-availability anchor; later amendments/revisions are not retroactive information.",
    },
    {
        "id": "I9A",
        "family": "CBOE_VIX_DAILY",
        "url": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
        "checks": ["DATE,OPEN,HIGH,LOW,CLOSE"],
        "pit_semantics": "Use completed daily observations only and act on the next eligible trading session.",
    },
    {
        "id": "I9B",
        "family": "CBOE_VVIX_DAILY",
        "url": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv",
        "checks": ["DATE,OPEN,HIGH,LOW,CLOSE"],
        "pit_semantics": "Use completed daily observations only and act on the next eligible trading session.",
    },
]


def _fetch(url: str) -> tuple[int, bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            return int(response.status), response.read(), response.headers.get("content-type")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), None


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _probe(item: dict) -> dict:
    status, data, content_type = _fetch(item["url"])
    result = {
        "id": item["id"],
        "family": item["family"],
        "url": item["url"],
        "http_status": status,
        "content_type": content_type,
        "response_bytes": len(data),
        "response_sha256": _sha256(data),
        "pit_semantics": item["pit_semantics"],
        "status": "BLOCKED",
        "checks": {},
    }
    if status != 200:
        result["reason"] = f"HTTP_{status}"
        return result

    text = data.decode("utf-8", "replace")
    if item["id"].startswith("I9"):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        header = lines[0] if lines else ""
        result["checks"] = {
            "has_header": header == "DATE,OPEN,HIGH,LOW,CLOSE",
            "has_rows": len(lines) > 1,
            "first_data_row_has_five_fields": bool(lines[1].split(",")) and len(lines[1].split(",")) == 5 if len(lines) > 1 else False,
        }
        result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
        result["sample_first_data_row"] = lines[1] if len(lines) > 1 else None
    else:
        result["checks"] = {needle: needle.lower() in text.lower() for needle in item["checks"]}
        result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"

    return result


def main() -> int:
    results = []
    for item in PROBES:
        try:
            results.append(_probe(item))
        except Exception as exc:
            results.append({
                "id": item["id"],
                "family": item["family"],
                "url": item["url"],
                "status": "ACCESS_ERROR",
                "reason": f"{type(exc).__name__}: {exc}",
            })

    summary = {
        "schema_version": "1.0",
        "task_id": "Q-2026-09-28-074-EXTENDED-SEC-CBOE-FEASIBILITY",
        "status": "SOURCE_FEASIBILITY_ONLY",
        "selection_used": False,
        "performance_evaluation": False,
        "holdout_used_for_selection": False,
        "results": results,
        "governance": {
            "no_parameter_search": True,
            "no_asset_search": True,
            "no_family_ranking": True,
            "fresh_disjoint_validation_required": True,
            "coverage_before_pit": True,
            "pit_before_performance": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    out = Path("research/runs/q074_extended_source_feasibility/source_feasibility.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Q074_STATUS:", summary["status"])
    for item in results:
        print(item["id"], item["status"], item.get("reason", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
