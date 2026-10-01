"""Q115 deterministic Treasury auction demand-state compiler."""
from __future__ import annotations
from decimal import Decimal
from typing import Any

def compile_states(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    valid=[]
    for row in rows:
        required=("auction_date","record_date","cusip","security_type","security_term","bid_to_cover_ratio")
        missing=[k for k in required if row.get(k) in (None,"")]
        if missing: raise ValueError("Q115_MISSING_FIELDS:"+",".join(missing))
        if row["security_type"]!="Note" or row["security_term"]!="10-Year":
            raise ValueError("Q115_UNEXPECTED_SECURITY")
        auction=str(row["auction_date"]); record=str(row["record_date"])
        if record < auction: raise ValueError("Q115_PIT_DATE_ORDER")
        btc=Decimal(str(row["bid_to_cover_ratio"]))
        if not btc.is_finite() or btc<=0: raise ValueError("Q115_INVALID_BID_TO_COVER")
        valid.append({**row,"btc":btc})
    valid.sort(key=lambda x:(x["auction_date"],x["cusip"]))
    out=[]; prev=None
    for row in valid:
        delta=None; state="FIRST" if prev is None else None
        if prev is not None:
            delta=row["btc"]-prev["btc"]
            state="IMPROVED" if delta>0 else "WEAKENED" if delta<0 else "FLAT"
        out.append({
            "auction_date":row["auction_date"],
            "record_date":row["record_date"],
            "cusip":row["cusip"],
            "bid_to_cover_ratio":str(row["btc"]),
            "prior_auction_date":prev["auction_date"] if prev else None,
            "prior_cusip":prev["cusip"] if prev else None,
            "delta_bid_to_cover":None if delta is None else str(delta),
            "demand_state":state,
            "pit_record_date":row["record_date"],
            "pit_eligible":True
        })
        prev=row
    return out

def synthetic_contract()->dict[str,bool]:
    rows=[
      {"auction_date":"2026-01-01","record_date":"2026-01-01","cusip":"A","security_type":"Note","security_term":"10-Year","bid_to_cover_ratio":"2.5"},
      {"auction_date":"2026-02-01","record_date":"2026-02-01","cusip":"B","security_type":"Note","security_term":"10-Year","bid_to_cover_ratio":"2.3"},
      {"auction_date":"2026-03-01","record_date":"2026-03-01","cusip":"C","security_type":"Note","security_term":"10-Year","bid_to_cover_ratio":"2.3"}
    ]
    out=compile_states(rows)
    return {
      "first_state":out[0]["demand_state"]=="FIRST",
      "weakening_state":out[1]["demand_state"]=="WEAKENED",
      "flat_state":out[2]["demand_state"]=="FLAT",
      "raw_delta_preserved":out[1]["delta_bid_to_cover"]=="-0.2",
      "pit_anchor_preserved":all(x["pit_eligible"] for x in out),
    }
