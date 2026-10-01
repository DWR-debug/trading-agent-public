"""Q114 deterministic SEC 13F manager-position transition compiler."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Any
from automation.q111_security_identity_contract import canonical_security_key

@dataclass(frozen=True)
class Position:
    manager_cik: str
    accession: str
    acceptance_datetime: datetime
    period_of_report: str
    security_key: str
    shares: Decimal
    reported_value: Decimal

def parse_dt(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text)

def parse_position(row: dict[str, Any]) -> Position:
    required = ("manager_cik","accession","acceptance_datetime","period_of_report","shares","reported_value")
    missing=[k for k in required if row.get(k) in (None,"")]
    if missing: raise ValueError("Q114_MISSING_FIELDS:"+",".join(missing))
    key=canonical_security_key(row)
    return Position(
        manager_cik=str(row["manager_cik"]).zfill(10),
        accession=str(row["accession"]),
        acceptance_datetime=parse_dt(str(row["acceptance_datetime"])),
        period_of_report=str(row["period_of_report"]),
        security_key=key,
        shares=Decimal(str(row["shares"])),
        reported_value=Decimal(str(row["reported_value"])),
    )

def deduplicate_positions(rows: list[dict[str,Any]]) -> list[Position]:
    seen: dict[tuple[str,str,str], Position] = {}
    for row in rows:
        pos=parse_position(row)
        identity=(pos.manager_cik,pos.period_of_report,pos.security_key)
        old=seen.get(identity)
        if old is None:
            seen[identity]=pos
            continue
        if old != pos:
            raise ValueError("Q114_POSITION_CONFLICT:"+repr(identity))
    return [seen[key] for key in sorted(seen)]

def transition(previous: Position|None, current: Position) -> dict[str,Any]:
    if previous is None:
        state="NEW"
        delta_shares=current.shares
        delta_value=current.reported_value
    else:
        delta_shares=current.shares-previous.shares
        delta_value=current.reported_value-previous.reported_value
        if delta_shares > 0: state="INCREASE"
        elif delta_shares < 0: state="DECREASE"
        else: state="UNCHANGED"
        if current.shares == 0 and previous.shares != 0: state="EXIT"
    return {
        "manager_cik":current.manager_cik,
        "security_key":current.security_key,
        "period_of_report":current.period_of_report,
        "accession":current.accession,
        "acceptance_datetime":current.acceptance_datetime.isoformat(),
        "state":state,
        "shares":str(current.shares),
        "reported_value":str(current.reported_value),
        "delta_shares":str(delta_shares),
        "delta_reported_value":str(delta_value),
        "pit_eligible_at":current.acceptance_datetime.isoformat(),
    }

def compile_transitions(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    positions=deduplicate_positions(rows)
    groups: dict[tuple[str,str], list[Position]]={}
    for p in positions:
        groups.setdefault((p.manager_cik,p.security_key),[]).append(p)
    out=[]
    for key, seq in sorted(groups.items()):
        seq.sort(key=lambda p:(p.period_of_report,p.acceptance_datetime,p.accession))
        prev=None
        for cur in seq:
            out.append(transition(prev,cur))
            prev=cur
    return out

def synthetic_contract()->dict[str,bool]:
    rows=[
      {"manager_cik":"1067983","accession":"A1","acceptance_datetime":"2026-05-01T10:00:00+00:00","period_of_report":"2026-03-31","name_of_issuer":"Apple Inc.","title_of_class":"Common Stock","cusip":"037833100","shares":"100","reported_value":"10000"},
      {"manager_cik":"1067983","accession":"A2","acceptance_datetime":"2026-08-01T10:00:00+00:00","period_of_report":"2026-06-30","name_of_issuer":"Apple Inc.","title_of_class":"Common Stock","cusip":"037833100","shares":"140","reported_value":"15000"},
      {"manager_cik":"1067983","accession":"A2","acceptance_datetime":"2026-08-01T10:00:00+00:00","period_of_report":"2026-06-30","name_of_issuer":"APPLE INC","title_of_class":"COMMON STOCK","cusip":"037833100","shares":"140","reported_value":"15000"}
    ]
    states=[x["state"] for x in compile_transitions(rows)]
    return {
      "normalized_duplicate_collapsed": len(deduplicate_positions(rows))==2,
      "transition_is_increase": states==["NEW","INCREASE"],
      "pit_acceptance_preserved": compile_transitions(rows)[1]["pit_eligible_at"].startswith("2026-08-01T10:00:00"),
      "accession_lineage_preserved": compile_transitions(rows)[1]["accession"]=="A2",
    }
