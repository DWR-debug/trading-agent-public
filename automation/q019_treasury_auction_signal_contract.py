"""Q019 Treasury 10-Year auction signal/PIT contract validation.

Coverage-only. No performance, P&L, forward returns, holdout use, candidate
ranking, parameter search, asset search, or promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from bisect import bisect_right
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from config import settings
import exchange_calendars as xcals
import pandas as pd
from research.asset_universes import get_universe

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = "q018_official_event_source_validation"
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
REQUESTED_CANDLES = 3520
TARGET_COMMON_CANDLES = 3500
TREASURY_API = (
    "https://api.fiscaldata.treasury.gov/services/api/"
    "fiscal_service/v1/accounting/od/auctions_query"
)


class SourceError(RuntimeError):
    pass


def _fetch_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "trading-agent-public research"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"{url}: {exc}") from exc


def _fingerprint(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _treasury_rows() -> list[dict]:
    params = {
        "fields": "record_date,security_type,security_term,auction_date,cusip,bid_to_cover_ratio",
        "filter": (
            f"security_type:eq:Note,security_term:eq:10-Year,"
            f"record_date:gte:{STUDY_START.isoformat()},record_date:lte:{STUDY_END.isoformat()}"
        ),
        "sort": "auction_date",
        "page[size]": 2000,
    }
    url = TREASURY_API + "?" + urlencode(params)
    payload = _fetch_json(url)
    return payload.get("data", [])


def _validate_treasury_contract(rows: list[dict], common_dates: list[date]) -> dict:
    expected_fields = {
        "record_date",
        "security_type",
        "security_term",
        "auction_date",
        "cusip",
        "bid_to_cover_ratio",
    }
    valid = []
    errors = []
    seen = set()
    for row in rows:
        missing = sorted(expected_fields - set(row))
        if missing:
            errors.append({"reason": "missing_fields", "fields": missing, "row": row})
            continue
        if row["security_type"] != "Note" or row["security_term"] != "10-Year":
            errors.append({"reason": "unexpected_security", "row": row})
            continue
        key = (row["auction_date"], row["cusip"])
        if key in seen:
            errors.append({"reason": "duplicate_auction_key", "key": key})
            continue
        seen.add(key)
        try:
            record = date.fromisoformat(row["record_date"])
            auction = date.fromisoformat(row["auction_date"])
            btc = float(row["bid_to_cover_ratio"])
        except (TypeError, ValueError) as exc:
            errors.append({"reason": "invalid_value", "row": row, "error": str(exc)})
            continue
        if not math.isfinite(btc) or btc <= 0.0:
            errors.append({"reason": "invalid_bid_to_cover", "row": row})
            continue
        if record < auction:
            errors.append({"reason": "publication_before_auction", "row": row})
            continue
        if not (STUDY_START <= record <= STUDY_END):
            errors.append({"reason": "record_date_outside_window", "row": row})
            continue
        valid.append(
            {
                **row,
                "record_date_parsed": record,
                "auction_date_parsed": auction,
                "bid_to_cover_float": btc,
            }
        )

    valid.sort(key=lambda x: (x["auction_date_parsed"], x["cusip"]))
    common_sorted = sorted(common_dates)
    previous = None
    mapped = 0
    terminal = 0
    signals = []
    for row in valid:
        current = row["bid_to_cover_float"]
        if previous is None:
            signal = None
        else:
            delta = current - previous
            signal = 1 if delta > 0 else -1 if delta < 0 else 0
        previous = current
        idx = bisect_right(common_sorted, row["record_date_parsed"])
        next_bar = common_sorted[idx] if idx < len(common_sorted) else None
        if next_bar is None:
            terminal += 1
        else:
            mapped += 1
            if next_bar <= row["record_date_parsed"]:
                errors.append(
                    {
                        "reason": "pit_violation",
                        "row": row,
                        "next_bar": next_bar.isoformat(),
                    }
                )
        signals.append(
            {
                "auction_date": row["auction_date"],
                "cusip": row["cusip"],
                "record_date": row["record_date"],
                "bid_to_cover_ratio": current,
                "signal": signal,
                "next_eligible_common_trading_date": (
                    next_bar.isoformat() if next_bar else None
                ),
            }
        )

    status = (
        "COVERAGE_VALIDATED"
        if valid and not errors and mapped > 0
        else "DATA_INSUFFICIENT"
    )
    return {
        "status": status,
        "raw_row_count": len(rows),
        "valid_row_count": len(valid),
        "mapped_event_count": mapped,
        "terminal_event_count": terminal,
        "error_count": len(errors),
        "errors": errors[:50],
        "signal_event_count": max(0, len(signals) - 1),
        "first_event": signals[0] if signals else None,
        "last_event": signals[-1] if signals else None,
        "signals_fingerprint": _fingerprint(signals),
    }


def run(*, output_path: str | Path) -> dict:
    if (
        settings.PAPER_ONLY is not True
        or settings.LIVE_TRADING_ENABLED is not False
        or settings.ORDERS_ENABLED is not False
    ):
        raise RuntimeError("Q019 requires paper-only safety configuration.")

    universe = get_universe(UNIVERSE)
    output = ROOT / Path(output_path)

    calendar = xcals.get_calendar("XNYS")
    sessions = calendar.sessions_in_range(
        pd.Timestamp(STUDY_START.isoformat(), tz="UTC"),
        pd.Timestamp(STUDY_END.isoformat(), tz="UTC"),
    )
    common_dates = [stamp.date() for stamp in sessions]
    if not common_dates:
        raise RuntimeError("Q019 XNYS session calendar is empty")
    if common_dates[0] < STUDY_START or common_dates[-1] > STUDY_END:
        raise RuntimeError("Q019 XNYS session calendar escaped fixed study window")

    rows = _treasury_rows()
    contract = _validate_treasury_contract(rows, common_dates)
    result = {
        "schema_version": "1.0",
        "task_id": "Q-019-TREASURY-AUCTION-SIGNAL-CONTRACT",
        "status": contract["status"],
        "study_window": {
            "start": STUDY_START.isoformat(),
            "end": STUDY_END.isoformat(),
        },
        "universe": {"name": UNIVERSE, "symbols": list(universe.symbols)},
        "source": {
            "provider": "U.S. Treasury Fiscal Data",
            "dataset": "Treasury Securities Auctions Data",
            "endpoint": TREASURY_API,
        },
        "pit_calendar": {
            "source": "exchange_calendars",
            "calendar": "XNYS",
            "session_count": len(common_dates),
            "rule": "first XNYS session strictly after record_date",
        },
        "contract": contract,
        "governance": {
            "coverage_only": True,
            "performance_evaluation": False,
            "holdout_used": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "feature_search": False,
            "horizon_search": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["fingerprint"] = _fingerprint(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "task_id": result["task_id"],
                "status": result["status"],
                "mapped_events": contract["mapped_event_count"],
                "terminal_events": contract["terminal_event_count"],
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="research/runs/source_feasibility/q019_treasury_signal_contract.json",
    )
    args = parser.parse_args()
    try:
        run(output_path=args.output)
    except (SourceError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "DATA_INSUFFICIENT", "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
