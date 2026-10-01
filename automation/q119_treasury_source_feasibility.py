"""Q119 live Treasury source/PIT feasibility compiler.

Research-only. Fetches a fixed historical 10-Year Note auction population from
the official Treasury Fiscal Data API and maps the published median yield
field into the Q119 deterministic demand-shape compiler. No performance,
holdout selection, search, ranking, or promotion is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from automation.q119_treasury_demand_shape import compile_states

API = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
START = "2011-01-01"
END = "2025-09-24"
UA = "trading-agent-public/Q119-source-feasibility"
FIELDS = ",".join(
    [
        "record_date",
        "auction_date",
        "cusip",
        "security_type",
        "security_term",
        "high_yield",
        "median_yield",
        "low_yield",
    ]
)


def fetch() -> tuple[str, bytes, list[dict]]:
    params = {
        "fields": FIELDS,
        "filter": (
            f"security_type:eq:Note,security_term:eq:10-Year,"
            f"record_date:gte:{START},record_date:lte:{END}"
        ),
        "sort": "auction_date",
        "page[size]": "2000",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        body = response.read()
    payload = json.loads(body.decode("utf-8"))
    rows = payload.get("data", [])
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Q119_EMPTY_TREASURY_POPULATION")
    return url, body, rows


def validate(rows: list[dict]) -> dict:
    required = {
        "record_date",
        "auction_date",
        "cusip",
        "security_type",
        "security_term",
        "high_yield",
        "median_yield",
        "low_yield",
    }
    normalized = []
    for row in rows:
        if not required.issubset(row):
            raise RuntimeError("Q119_REQUIRED_FIELD_MISSING")
        if any(row.get(field) in (None, "") for field in required):
            raise RuntimeError("Q119_REQUIRED_FIELD_EMPTY")
        if row["security_type"] != "Note" or row["security_term"] != "10-Year":
            raise RuntimeError("Q119_UNEXPECTED_SECURITY")
        if str(row["record_date"]) < str(row["auction_date"]):
            raise RuntimeError("Q119_PIT_DATE_ORDER")
        normalized.append(
            {
                **row,
                "median_yield": row["median_yield"],
            }
        )

    compiled = compile_states(normalized, cutoff=date.fromisoformat(END))
    if len(compiled) != len(rows):
        raise RuntimeError("Q119_COMPILED_COUNT_MISMATCH")

    future = list(normalized)
    future.append(
        {
            **normalized[-1],
            "auction_date": "2025-12-01",
            "record_date": "2025-12-01",
            "cusip": "FUTURE-Q119",
        }
    )
    baseline = compile_states(normalized, cutoff=date.fromisoformat(END))
    mutated = compile_states(future, cutoff=date.fromisoformat(END))
    if baseline != mutated:
        raise RuntimeError("Q119_FUTURE_MUTATION_FAILED")

    return {
        "raw_row_count": len(rows),
        "compiled_row_count": len(compiled),
        "first_event": compiled[0],
        "last_event": compiled[-1],
        "future_mutation_invariance": True,
        "yield_fields": [
            "high_yield",
            "avg_median_yield",
            "low_yield",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/runs/q119_treasury/q119_source_pit_result.json"),
    )
    args = parser.parse_args()

    url, body, rows = fetch()
    validation = validate(rows)
    result = {
        "schema_version": 1,
        "task_id": "Q-2026-10-01-119-TREASURY-DEMAND-SHAPE-FEASIBILITY",
        "status": "Q119_SOURCE_PIT_FEASIBILITY_COMPLETED",
        "source_url": url,
        "source_response_sha256": hashlib.sha256(body).hexdigest(),
        "study_window": {"start": START, "end": END},
        "validation": validation,
        "governance": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
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
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Q119_STATUS=" + result["status"])
    print("Q119_ROWS=" + str(validation["raw_row_count"]))
    print("Q119_RECEIPT_FINGERPRINT=" + result["receipt_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
