"""Q119 deterministic Treasury auction demand-shape compiler (design/feasibility only).

The signal uses only Treasury-published low/median/high competitive yields.
It measures the shape of the public auction demand schedule, not aggregate
demand magnitude such as bid-to-cover. No parameter fitting or performance
evaluation occurs here.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

SENTINEL_TERM = "10-Year"
SENTINEL_TYPE = "Note"

def _dec(value: Any, field: str) -> Decimal:
    try:
        x = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Q119_INVALID_{field.upper()}") from exc
    if not x.is_finite():
        raise ValueError(f"Q119_INVALID_{field.upper()}")
    return x

def compile_states(rows: list[dict[str, Any]], *, cutoff: date | None = None) -> list[dict[str, Any]]:
    valid: list[dict[str, Any]] = []
    for row in rows:
        required = ("auction_date","record_date","cusip","security_type","security_term","high_yield","median_yield","low_yield")
        missing = [field for field in required if row.get(field) in (None, "")]
        if missing:
            raise ValueError("Q119_MISSING_FIELDS:" + ",".join(missing))
        auction = date.fromisoformat(str(row["auction_date"]))
        record = date.fromisoformat(str(row["record_date"]))
        if record < auction:
            raise ValueError("Q119_PIT_DATE_ORDER")
        if cutoff is not None and record > cutoff:
            continue
        if row["security_type"] != SENTINEL_TYPE or row["security_term"] != SENTINEL_TERM:
            raise ValueError("Q119_UNEXPECTED_SECURITY")
        high = _dec(row["high_yield"], "high_yield")
        median = _dec(row["median_yield"], "median_yield")
        low = _dec(row["low_yield"], "low_yield")
        if not (high >= median >= low):
            raise ValueError("Q119_YIELD_ORDER_INVALID")
        upper = high - median
        lower = median - low
        delta_bps = (upper - lower) * Decimal("100")
        state = "UPPER_WIDE" if delta_bps > 0 else "LOWER_WIDE" if delta_bps < 0 else "FLAT"
        valid.append({"auction_date":auction.isoformat(),"record_date":record.isoformat(),"cusip":str(row["cusip"]),"security_type":row["security_type"],"security_term":row["security_term"],"high_yield":str(high),"median_yield":str(median),"low_yield":str(low),"upper_spread_yield":str(upper),"lower_spread_yield":str(lower),"shape_delta_bps":str(delta_bps),"demand_shape_state":state,"pit_record_date":record.isoformat(),"pit_eligible":True})
    valid.sort(key=lambda x: (x["auction_date"], x["cusip"]))
    return valid

def synthetic_contract() -> dict[str, bool]:
    rows = [
        {"auction_date":"2026-01-01","record_date":"2026-01-01","cusip":"A","security_type":"Note","security_term":"10-Year","high_yield":"4.20","median_yield":"4.10","low_yield":"4.00"},
        {"auction_date":"2026-02-01","record_date":"2026-02-01","cusip":"B","security_type":"Note","security_term":"10-Year","high_yield":"4.20","median_yield":"4.15","low_yield":"4.00"},
        {"auction_date":"2026-03-01","record_date":"2026-03-01","cusip":"C","security_type":"Note","security_term":"10-Year","high_yield":"4.20","median_yield":"4.10","low_yield":"4.00"},
    ]
    out = compile_states(rows)
    return {
        "flat_state": out[0]["demand_shape_state"] == "FLAT",
        "lower_wide": out[1]["demand_shape_state"] == "LOWER_WIDE",
        "raw_spreads_preserved": out[1]["upper_spread_yield"] == "0.05" and out[1]["lower_spread_yield"] == "0.15",
        "pit_anchor_preserved": all(row["pit_eligible"] for row in out),
        "cutoff_is_deterministic": len(compile_states(rows, cutoff=date(2026, 2, 15))) == 2,
    }
