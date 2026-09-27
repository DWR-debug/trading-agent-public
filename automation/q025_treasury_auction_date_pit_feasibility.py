"""Q025 Treasury auction-date point-in-time feasibility.

Consumes the immutable Q019 event population and the verified Q024 result-PDF
identity evidence. No performance, P&L, or holdout access is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
TREASURY_API = (
    "https://api.fiscaldata.treasury.gov/services/api/"
    "fiscal_service/v1/accounting/od/auctions_query"
)
Q024_EVIDENCE = (
    ROOT / "research/evidence/"
    "q024_treasury_auction_result_timestamp_pit_feasibility_2026_09_27.json"
)
MIN_LAG_DAYS = 1


class SourceError(RuntimeError):
    pass


def _fp(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _fetch_json(url: str) -> dict:
    req = Request(
        url,
        headers={"User-Agent": "trading-agent-public Q025 research"},
    )
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"{url}: {exc}") from exc


def _q019_events() -> list[dict]:
    params = {
        "fields": (
            "record_date,security_type,security_term,auction_date,"
            "cusip,bid_to_cover_ratio"
        ),
        "filter": (
            "security_type:eq:Note,"
            "security_term:eq:10-Year,"
            f"record_date:gte:{STUDY_START.isoformat()},"
            f"record_date:lte:{STUDY_END.isoformat()}"
        ),
        "sort": "auction_date",
        "page[size]": 2000,
    }
    url = TREASURY_API + "?" + urlencode(params)
    rows = _fetch_json(url).get("data", [])
    rows.sort(key=lambda row: (row.get("auction_date", ""), row.get("cusip", "")))
    return rows


def run(*, output_path: str | Path) -> dict:
    events = _q019_events()
    if not events:
        raise SourceError("Q019 event population is empty")
    if not Q024_EVIDENCE.exists():
        raise SourceError("verified Q024 evidence record is missing")

    q024 = json.loads(Q024_EVIDENCE.read_text(encoding="utf-8"))
    q024_identity_count = q024["result_pdf_identity"]["validated_events"]
    if q024_identity_count != len(events):
        raise SourceError(
            f"Q024 result-PDF identity count {q024_identity_count} "
            f"!= current Q019 event count {len(events)}"
        )

    rows: list[dict] = []
    lags: list[int] = []
    for event in events:
        auction = date.fromisoformat(event["auction_date"])
        record = date.fromisoformat(event["record_date"])
        lag = (record - auction).days
        lags.append(lag)
        rows.append({
            "record_date": event["record_date"],
            "auction_date": event["auction_date"],
            "cusip": event["cusip"],
            "bid_to_cover_ratio": event.get("bid_to_cover_ratio"),
            "record_date_minus_auction_date_days": lag,
            "record_date_after_auction_date": record > auction,
        })

    status = (
        "DATE_PIT_VALIDATED"
        if all(lag >= MIN_LAG_DAYS for lag in lags)
        else "DATA_INSUFFICIENT"
    )

    result = {
        "schema_version": "1.0",
        "task_id": "Q-025-TREASURY-AUCTION-DATE-PIT-FEASIBILITY",
        "status": status,
        "study_window": {
            "start": STUDY_START.isoformat(),
            "end": STUDY_END.isoformat(),
        },
        "population": {
            "source": "Q019 fixed Treasury 10-Year auction result events",
            "events": len(events),
        },
        "q024_identity_dependency": {
            "evidence_record": str(Q024_EVIDENCE.relative_to(ROOT)),
            "workflow_run_id": q024["workflow_run_id"],
            "artifact_id": q024["artifact_id"],
            "result_fingerprint": q024["result_fingerprint"],
            "result_pdf_identity_validated_events": q024_identity_count,
        },
        "historical_release_semantics": {
            "source": "TreasuryDirect Auction Timeline",
            "post_2004_result_release": "within 2 minutes +/- 30 seconds",
            "q019_scope_starts": "2011-01-01",
            "interpretation": (
                "For the fixed Q019 population the official auction result was "
                "released on the auction date; exact historical intraday "
                "timestamps are not required to reject the later record_date "
                "as the earliest information-date anchor."
            ),
        },
        "date_validation": {
            "all_record_dates_after_auction_dates": all(lag >= MIN_LAG_DAYS for lag in lags),
            "minimum_lag_days": min(lags),
            "maximum_lag_days": max(lags),
            "lag_distribution_days": {
                str(k): lags.count(k) for k in sorted(set(lags))
            },
        },
        "governance": {
            "source_feasibility_only": True,
            "performance_evaluation": False,
            "pnl_evaluation": False,
            "holdout_used": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "variant_search": False,
            "research_gate_changes": False,
            "promotion_decision": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "events": rows,
    }
    result["fingerprint"] = _fp(result)

    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "task_id": result["task_id"],
        "status": result["status"],
        "events": len(events),
        "q024_identity_validated_events": q024_identity_count,
        "min_lag_days": min(lags),
        "max_lag_days": max(lags),
        "fingerprint": result["fingerprint"],
    }, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="research/runs/source_feasibility/q025_treasury_auction_date_pit_feasibility.json",
    )
    args = parser.parse_args()
    try:
        run(output_path=args.output)
    except (SourceError, ValueError, OSError) as exc:
        print(json.dumps({"status": "DATA_INSUFFICIENT", "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
