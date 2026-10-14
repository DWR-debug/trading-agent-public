"""Combine the pinned eight-row Q104 R1/R2 date-change probe with the six R3 rows.

This is descriptive evidence consolidation only. It never applies field precedence,
updates frozen receipts, repairs accession identities, or clears acceptance/PIT gates.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRIOR_RUN_ID = "38304249742"
PRIOR_ARTIFACT = "q104-i19-filing-date-change-header-probe-38304249742-1"
PRIOR_FP = "17fa46e3f49b4bb296122a1f6e80b7fbe7e3c134868803b2ddb910f898521412"
R1_FP = "c0881b295d37fa34925103b30acbb893a78bbbe230af6e637576dfda4fac86f7"
R2_FP = "d85ad092296b38f29fa25147537f52804f9a32d9969051c7f9e9cadff283fe04"
R3_FP = "f4c309fe9f5389fdd726fbdb9aa969a46e376d1bd212c3654cc7ec1a6682015a"
R3_HEADER_FP_KEY = "analysis_fingerprint"

class AggregateError(ValueError): pass

def digest(v: Any) -> str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")).hexdigest()

def receipt_fingerprint(v: dict[str, Any]) -> str:
    p=dict(v); p.pop("receipt_fingerprint",None)
    return digest(p)

def find_receipt(root: Path, expected_name: str | None = None) -> Path:
    if root.is_file(): return root
    files=sorted(root.rglob(expected_name)) if expected_name else sorted(root.rglob("*.json"))
    if len(files)!=1: raise AggregateError(f"RECEIPT_COUNT_INVALID:{len(files)}")
    return files[0]

def route_summary(sample: dict[str, Any], source_label: str) -> dict[str, Any]:
    accession=str(sample.get("accession") or "")
    if not accession: raise AggregateError("ACCESSION_MISSING")
    probes=sample.get("probes",[])
    by_route={str(p.get("route")):p for p in probes}
    required={"index_headers","raw_sgml_header","complete_submission_header_prefix"}
    if set(by_route)!=required: raise AggregateError("ROUTE_SET_MISMATCH:"+accession)
    fields={r:(by_route[r].get("observed_fields") or {}) for r in required}
    bulk=sample.get("bulk_filing_date",sample.get("bulk_date"))
    header_values=[fields[r].get("filing_date") for r in sorted(required) if fields[r].get("filing_date")]
    acceptance_values=[fields[r].get("acceptance_datetime") for r in sorted(required) if fields[r].get("acceptance_datetime")]
    changes=[fields[r].get("date_of_filing_date_change") for r in sorted(required) if fields[r].get("date_of_filing_date_change")]
    distinct_header=sorted(set(header_values))
    distinct_accept=sorted(set(acceptance_values))
    distinct_change=sorted(set(changes))
    identity_ok=all(
        fields[r].get("accession")==accession
        and bool(fields[r].get("filer_cik"))
        and (not fields[r].get("form") or fields[r].get("form")==sample.get("form","13F-HR"))
        for r in required
    )
    if not bulk or not distinct_header or not distinct_accept:
        raise AggregateError("REQUIRED_DATE_OR_ACCEPTANCE_FIELD_MISSING:"+accession)
    return {
        "source_label":source_label,"accession":accession,
        "filer_cik":fields["index_headers"].get("filer_cik"),
        "form":sample.get("form") or fields["index_headers"].get("form"),
        "bulk_filing_date":bulk,"edgar_header_filing_dates":distinct_header,
        "edgar_header_filing_date_route_count":len(header_values),
        "acceptance_datetimes":distinct_accept,"acceptance_route_count":len(acceptance_values),
        "date_change_values":distinct_change,"date_change_route_count":len(changes),
        "date_change_observed":bool(changes),
        "date_change_equals_header_filing_date":(distinct_change[0]==distinct_header[0]) if len(distinct_change)==1 and len(distinct_header)==1 else None,
        "date_change_routes_agree_where_observed":len(distinct_change)<=1,
        "bulk_date_differs_from_header":len(distinct_header)==1 and bulk!=distinct_header[0],
        "identity_fields_consistent":identity_ok,
        "header_filing_date_routes_agree":len(distinct_header)==1 and len(header_values)==3,
        "acceptance_routes_agree":len(distinct_accept)==1 and len(acceptance_values)==3,
    }

def build_aggregate(prior: dict[str, Any], r3: dict[str, Any]) -> dict[str, Any]:
    if prior.get("record_type")!="q104_i19_filing_date_change_header_probe" or prior.get("status")!="DATE_CHANGE_HEADER_PROBE_COMPLETE":
        raise AggregateError("PRIOR_FIELD_PROBE_NOT_COMPLETE")
    if prior.get("receipt_fingerprint")!=PRIOR_FP or receipt_fingerprint(prior)!=PRIOR_FP:
        raise AggregateError("PRIOR_FIELD_PROBE_FINGERPRINT_MISMATCH")
    if prior.get("source_r1_receipt_fingerprint")!=R1_FP or prior.get("source_r2_receipt_fingerprint")!=R2_FP or prior.get("sample_count")!=8 or prior.get("probe_count_captured")!=24:
        raise AggregateError("PRIOR_FIELD_PROBE_UPSTREAM_CONTRACT_MISMATCH")
    if r3.get("record_type")!="q104_i19_r3_date_change_header_probe" or r3.get("status")!="R3_DATE_CHANGE_HEADER_PROBE_COMPLETE":
        raise AggregateError("R3_HEADER_PROBE_NOT_COMPLETE")
    if r3.get("receipt_fingerprint")!=receipt_fingerprint(r3):
        raise AggregateError("R3_HEADER_PROBE_FINGERPRINT_MISMATCH")
    if r3.get("source_receipt_fingerprint")!=R3_FP or r3.get("source_sample_count")!=6 or r3.get("probe_count_captured")!=18:
        raise AggregateError("R3_HEADER_PROBE_UPSTREAM_CONTRACT_MISMATCH")
    if r3.get("receipt_fingerprint")!=receipt_fingerprint(r3):
        raise AggregateError("R3_HEADER_PROBE_FINGERPRINT_MISMATCH")
    rows=[route_summary(s,"R1_R2_2015_2017_2020_2025") for s in prior["samples"]]
    rows.extend(route_summary(s,"R3_2016Q4") for s in r3["samples"])
    if len(rows)!=14 or len({r["accession"] for r in rows})!=14:
        raise AggregateError("COMBINED_SAMPLE_IDENTITY_MISMATCH")
    counts={
        "sample_count":len(rows),
        "bulk_date_differs_from_header":sum(x["bulk_date_differs_from_header"] for x in rows),
        "header_filing_date_routes_agree":sum(x["header_filing_date_routes_agree"] for x in rows),
        "acceptance_routes_agree":sum(x["acceptance_routes_agree"] for x in rows),
        "date_change_observed":sum(x["date_change_observed"] for x in rows),
        "date_change_routes_agree_where_observed":sum(x["date_change_routes_agree_where_observed"] for x in rows),
        "date_change_equals_header_filing_date":sum(x["date_change_equals_header_filing_date"] is True for x in rows),
        "date_change_differs_from_header_filing_date":sum(x["date_change_equals_header_filing_date"] is False for x in rows),
    }
    core={
        "schema_version":1,"record_type":"q104_i19_cross_vintage_date_change_aggregate",
        "candidate_id":"Q104:I19","status":"FIELD_PRECEDENCE_EXTENDED_DIAGNOSTIC_ONLY_NOT_APPLIED",
        "source_prior_run_id":PRIOR_RUN_ID,"source_prior_artifact":PRIOR_ARTIFACT,
        "source_prior_receipt_fingerprint":PRIOR_FP,"source_r1_receipt_fingerprint":R1_FP,
        "source_r2_receipt_fingerprint":R2_FP,"source_r3_lineage_receipt_fingerprint":R3_FP,
        "counts":counts,"samples":rows,
        "interpretation_scope":{
            "descriptive_not_causal":True,"field_precedence_applied":False,"source_receipts_modified":False,
            "acceptance_time_gate_cleared":False,"historical_archive_gate_cleared":False,
            "production_join_changed":False,"census_restarted":False,
            "performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,
            "promotion":False,"live_execution":False,
        },
        "next_gate":"Review the six R3 date-change observations together with the prior eight. Do not apply a precedence rule to the 53 residuals without exact-population validation and separate approval.",
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
    }
    core["analysis_fingerprint"]=digest(core)
    return core

def run(prior_path: Path, r3_path: Path, output: Path, expected_analysis_fingerprint: str | None=None) -> dict[str,Any]:
    prior=json.loads(find_receipt(prior_path,"q104-date-change-receipt.json").read_text(encoding="utf-8"))
    r3=json.loads(find_receipt(r3_path,"receipt.json").read_text(encoding="utf-8"))
    core=build_aggregate(prior,r3)
    if expected_analysis_fingerprint and core["analysis_fingerprint"]!=expected_analysis_fingerprint:
        raise AggregateError("CROSS_ARCH_ANALYSIS_FINGERPRINT_MISMATCH")
    result={**core,"generated_at_utc":datetime.now(timezone.utc).isoformat()}
    result["receipt_fingerprint"]=receipt_fingerprint(result)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"analysis_fingerprint":result["analysis_fingerprint"],"receipt_fingerprint":result["receipt_fingerprint"],"counts":result["counts"]},sort_keys=True))
    return result

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--prior-probe",type=Path,required=True)
    ap.add_argument("--r3-probe",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--expected-analysis-fingerprint",default=None)
    args=ap.parse_args()
    run(args.prior_probe,args.r3_probe,args.output,args.expected_analysis_fingerprint)
    return 0

if __name__=="__main__": raise SystemExit(main())
