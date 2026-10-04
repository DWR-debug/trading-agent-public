"""Q104:I19 deterministic XBRL PIT compiler, pre-performance only."""
from __future__ import annotations
import argparse, copy, hashlib, json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
import exchange_calendars as xcals

EXACT_CONCEPTS = {"net_income_loss":"us-gaap:NetIncomeLoss","operating_cash_flow":"us-gaap:NetCashProvidedByUsedInOperatingActivities","assets":"us-gaap:Assets"}
ELIGIBLE_FORMS = frozenset({"10-K","10-Q"})
USD_UNIT = "USD"
XNYS = xcals.get_calendar("XNYS")

def canonical(value: Any) -> str: return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
def fingerprint(value: Any) -> str: return hashlib.sha256(canonical(value).encode()).hexdigest()
def parse_utc(value: str) -> datetime: return datetime.fromisoformat(str(value).replace("Z","+00:00")).astimezone(timezone.utc)
def first_xnys_after(value: datetime) -> str:
    d=value.date(); s=XNYS.sessions_in_range((d+timedelta(days=1)).isoformat(), (d+timedelta(days=14)).isoformat())
    if not len(s): raise ValueError("I19_NO_NEXT_XNYS_SESSION")
    return s[0].date().isoformat()

@dataclass(frozen=True)
class Filing:
    symbol: str; cik: str; accession: str; form: str; acceptance_datetime: datetime; facts: tuple[dict[str,Any],...]

def parse_filing(raw: dict[str,Any]) -> Filing:
    required=("symbol","cik","accession","form","acceptance_datetime","facts"); missing=[x for x in required if raw.get(x) in (None,"",[])]
    if missing: raise ValueError("I19_MISSING_FILING_FIELDS:"+",".join(missing))
    form=str(raw["form"]).upper()
    if form not in ELIGIBLE_FORMS: raise ValueError("I19_FORM_NOT_ELIGIBLE:"+form)
    if not isinstance(raw["facts"],list) or not all(isinstance(x,dict) for x in raw["facts"]): raise ValueError("I19_FACTS_MUST_BE_OBJECT_LIST")
    return Filing(str(raw["symbol"]).upper(),str(raw["cik"]).zfill(10),str(raw["accession"]),form,parse_utc(str(raw["acceptance_datetime"])),tuple(dict(x) for x in raw["facts"]))

def eligible_filings(filings: list[dict[str,Any]], symbol: str, cutoff: datetime) -> list[Filing]:
    parsed=[parse_filing(x) for x in filings if str(x.get("symbol","")).upper()==symbol.upper()]
    return sorted((x for x in parsed if x.acceptance_datetime<=cutoff), key=lambda x:(x.acceptance_datetime,x.accession))

def valid_fact(fact: dict[str,Any], concept: str) -> bool:
    return fact.get("concept")==concept and fact.get("unit")==USD_UNIT and fact.get("consolidated",True) is True and fact.get("dimensions",[]) in ([],None)

def decimal_value(fact: dict[str,Any], label: str) -> Decimal:
    try: return Decimal(str(fact["value"]))
    except (KeyError,InvalidOperation) as exc: raise ValueError("I19_INVALID_NUMERIC_VALUE:"+label) from exc

def compile_filing_state(filing: Filing) -> dict[str,Any]:
    ni=[x for x in filing.facts if valid_fact(x,EXACT_CONCEPTS["net_income_loss"]) and x.get("start") and x.get("end")]
    cfo=[x for x in filing.facts if valid_fact(x,EXACT_CONCEPTS["operating_cash_flow"]) and x.get("start") and x.get("end")]
    assets=[x for x in filing.facts if valid_fact(x,EXACT_CONCEPTS["assets"]) and x.get("instant")]
    if not ni: raise ValueError("I19_REQUIRED_CONCEPT_MISSING:"+EXACT_CONCEPTS["net_income_loss"])
    if not cfo: raise ValueError("I19_REQUIRED_CONCEPT_MISSING:"+EXACT_CONCEPTS["operating_cash_flow"])
    pairs=[(n,c) for n in ni for c in cfo if n.get("start")==c.get("start") and n.get("end")==c.get("end") and n.get("fiscal_period")==c.get("fiscal_period")]
    if not pairs: raise ValueError("I19_DURATION_ALIGNMENT_FAILED")
    pairs.sort(key=lambda p:(str(p[0]["end"]),str(p[0].get("fiscal_period","")))); n,c=pairs[-1]; end=str(n["end"])
    current=[x for x in assets if str(x["instant"])==end]
    if not current: raise ValueError("I19_CURRENT_ASSETS_MISSING:"+end)
    signatures={canonical({k:v for k,v in x.items() if k!="source_fragment"}) for x in current}
    if len(signatures)!=1: raise ValueError("I19_FACT_CONFLICT:"+EXACT_CONCEPTS["assets"]+":current")
    prior=[x for x in assets if str(x["instant"])<end]
    if not prior: raise ValueError("I19_PRIOR_ASSETS_MISSING:"+end)
    prior.sort(key=lambda x:str(x["instant"])); ca=decimal_value(current[0],"assets_current"); pa=decimal_value(prior[-1],"assets_prior")
    denom=(ca+pa)/Decimal(2)
    if denom==0: raise ValueError("I19_ASSETS_DENOMINATOR_ZERO")
    accr=decimal_value(n,"net_income_loss")-decimal_value(c,"operating_cash_flow"); intensity=accr/denom
    state="POSITIVE_ACCRUAL" if intensity>0 else ("NEGATIVE_ACCRUAL" if intensity<0 else "ZERO_ACCRUAL")
    return {"filing_accession":filing.accession,"filing_form":filing.form,"acceptance_datetime":filing.acceptance_datetime.isoformat(),"eligible_xnys_session":first_xnys_after(filing.acceptance_datetime),"period_start":str(n["start"]),"period_end":end,"fiscal_period":str(n.get("fiscal_period","")),"prior_assets_instant":str(prior[-1]["instant"]),"accrual_amount":str(accr),"accrual_intensity":str(intensity),"accrual_state":state,"concepts":dict(EXACT_CONCEPTS),"missingness":"COMPLETE"}

def institutional_state(transitions: list[dict[str,Any]], symbol: str, cutoff: datetime) -> dict[str,Any]:
    eligible=[dict(x) for x in transitions if str(x.get("symbol","")).upper()==symbol.upper() and x.get("acceptance_datetime") and parse_utc(str(x["acceptance_datetime"]))<=cutoff]
    allowed={"INCREASE","NEW","DECREASE","EXIT","UNCHANGED"}
    if any(x.get("state") not in allowed for x in eligible): raise ValueError("I19_INVALID_13F_TRANSITION_STATE")
    if not eligible: return {"state":"MISSING","period_of_report":None,"increase_new_count":0,"decrease_exit_count":0,"eligible_transition_count":0}
    periods=sorted({str(x["period_of_report"]) for x in eligible if x.get("period_of_report")})
    if not periods: return {"state":"MISSING","period_of_report":None,"increase_new_count":0,"decrease_exit_count":0,"eligible_transition_count":0}
    period=periods[-1]; selected=[x for x in eligible if str(x["period_of_report"])==period]; pos=sum(x["state"] in {"INCREASE","NEW"} for x in selected); neg=sum(x["state"] in {"DECREASE","EXIT"} for x in selected); net=pos-neg
    state="POSITIVE_INSTITUTIONAL_DEMAND" if net>0 else ("NEGATIVE_INSTITUTIONAL_DEMAND" if net<0 else "ZERO_INSTITUTIONAL_DEMAND"); latest=max(parse_utc(str(x["acceptance_datetime"])) for x in selected)
    return {"state":state,"period_of_report":period,"increase_new_count":pos,"decrease_exit_count":neg,"eligible_transition_count":len(selected),"latest_transition_acceptance_datetime":latest.isoformat(),"latest_transition_eligible_xnys_session":first_xnys_after(latest)}

def compile_issuer_state(filings:list[dict[str,Any]], transitions:list[dict[str,Any]], *, symbol:str, cutoff:datetime)->dict[str,Any]:
    accepted=eligible_filings(filings,symbol,cutoff)
    if not accepted: return {"symbol":symbol.upper(),"status":"MISSING","reason":"NO_ELIGIBLE_FILING","scientific_evidence":False}
    try: fs=compile_filing_state(accepted[-1])
    except ValueError as exc: return {"symbol":symbol.upper(),"status":"MISSING","reason":str(exc),"filing_accession":accepted[-1].accession,"scientific_evidence":False}
    try: ins=institutional_state(transitions,symbol,cutoff)
    except ValueError as exc: return {"symbol":symbol.upper(),"status":"MISSING","reason":str(exc),"filing_accession":accepted[-1].accession,"scientific_evidence":False}
    return {"symbol":symbol.upper(),"status":"COMPLETE" if ins["state"]!="MISSING" else "MISSING","filing_state":fs,"institutional_state":ins,"decision_cutoff":cutoff.isoformat(),"scientific_evidence":False,"performance_authorized":False,"promotion":False,"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}

def _bundle()->dict[str,Any]:
    base=[{"concept":EXACT_CONCEPTS["net_income_loss"],"unit":"USD","value":"120","start":"2025-01-01","end":"2025-03-31","fiscal_period":"Q1"},{"concept":EXACT_CONCEPTS["operating_cash_flow"],"unit":"USD","value":"80","start":"2025-01-01","end":"2025-03-31","fiscal_period":"Q1"},{"concept":EXACT_CONCEPTS["assets"],"unit":"USD","value":"1100","instant":"2025-03-31"},{"concept":EXACT_CONCEPTS["assets"],"unit":"USD","value":"1000","instant":"2024-12-31"}]
    amended=[dict(x) for x in base]; amended[0]=dict(amended[0],value="60")
    filings=[{"symbol":"SPGI","cik":"0000064040","accession":"0000000000-25-000001","form":"10-Q","acceptance_datetime":"2025-04-01T18:00:00Z","facts":base},{"symbol":"SPGI","cik":"0000064040","accession":"0000000000-25-000002","form":"10-Q","acceptance_datetime":"2025-04-03T18:00:00Z","facts":amended}]
    transitions=[{"symbol":"SPGI","period_of_report":"2025-03-31","state":"INCREASE","acceptance_datetime":"2025-05-01T12:00:00Z"},{"symbol":"SPGI","period_of_report":"2025-03-31","state":"NEW","acceptance_datetime":"2025-05-02T12:00:00Z"},{"symbol":"SPGI","period_of_report":"2025-03-31","state":"DECREASE","acceptance_datetime":"2025-05-03T12:00:00Z"}]
    before=compile_issuer_state(filings,transitions,symbol="SPGI",cutoff=parse_utc("2025-04-02T00:00:00Z")); after=compile_issuer_state(filings,transitions,symbol="SPGI",cutoff=parse_utc("2025-05-04T00:00:00Z"))
    return {"filings":filings,"transitions":transitions,"before":before,"after":after}

def synthetic_bundle()->dict[str,bool]:
    b=_bundle(); return {"before_amendment_original":b["before"]["filing_state"]["filing_accession"].endswith("000001"),"after_amendment_later":b["after"]["filing_state"]["filing_accession"].endswith("000002"),"amendment_boundary_changes_state":b["before"]["filing_state"]["accrual_state"]=="POSITIVE_ACCRUAL" and b["after"]["filing_state"]["accrual_state"]=="NEGATIVE_ACCRUAL","institutional_state_positive":b["after"]["institutional_state"]["state"]=="POSITIVE_INSTITUTIONAL_DEMAND","future_transition_excluded":b["after"]["institutional_state"]["eligible_transition_count"]==3}

def mutation_tests(bundle:dict[str,Any])->dict[str,bool]:
    filings,transitions=bundle["filings"],bundle["transitions"]; cutoff=parse_utc("2025-05-04T00:00:00Z"); base=compile_issuer_state(filings,transitions,symbol="SPGI",cutoff=cutoff)
    ordered=compile_issuer_state(list(reversed(filings)),list(reversed(transitions)),symbol="SPGI",cutoff=cutoff)
    future_filing=dict(filings[0],accession="FUTURE-FILING",acceptance_datetime="2026-01-01T18:00:00Z"); future_transition=dict(transitions[0],acceptance_datetime="2026-01-01T12:00:00Z",state="DECREASE")
    future=compile_issuer_state(filings+[future_filing],transitions+[future_transition],symbol="SPGI",cutoff=cutoff)
    missing_prior=copy.deepcopy(filings[0]); missing_prior["facts"]=[x for x in missing_prior["facts"] if x.get("instant")!="2024-12-31"]; missing=compile_issuer_state([missing_prior],[],symbol="SPGI",cutoff=parse_utc("2025-04-02T00:00:00Z"))
    mismatch=copy.deepcopy(filings[0]); mismatch["facts"][1]["end"]="2025-03-30"; mismatched=compile_issuer_state([mismatch],[],symbol="SPGI",cutoff=parse_utc("2025-04-02T00:00:00Z"))
    return {"input_order_invariance":canonical(base)==canonical(ordered),"future_data_invariance":canonical(base)==canonical(future),"missing_prior_assets_fail_closed":missing["status"]=="MISSING" and "I19_PRIOR_ASSETS_MISSING" in missing["reason"],"duration_mismatch_fail_closed":mismatched["status"]=="MISSING" and "I19_DURATION_ALIGNMENT_FAILED" in mismatched["reason"]}

def compile_contract_receipt()->dict[str,Any]:
    mutations=mutation_tests(_bundle()); checks=synthetic_bundle(); result={"schema_version":"1.0","task_id":"Q-2026-10-04-104-I19-XBRL-PIT-COMPILER","status":"I19_PIT_COMPILER_CONTRACT_COMPLETED_NO_PERFORMANCE" if all(mutations.values()) and all(checks.values()) else "I19_PIT_COMPILER_CONTRACT_FAILED","exact_concepts":dict(EXACT_CONCEPTS),"eligible_forms":sorted(ELIGIBLE_FORMS),"historical_data_compiled":False,"synthetic_mutation_tests":mutations,"synthetic_bundle_checks":checks,"governance":{"performance":False,"holdout":False,"selection":False,"ranking":False,"parameter_search":False,"threshold_search":False,"horizon_search":False,"asset_search":False,"variant_search":False,"performance_authorized":False,"automatic_promotion":False},"safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},"notes":["Deterministic compiler contract only; historical SEC filing-instance archive completeness remains open.","Independent reproduction remains mandatory.","No performance, ranking, tuning, holdout selection or promotion is authorized."]}; result["receipt_fingerprint"]=fingerprint(result); return result

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,required=True); args=p.parse_args(); result=compile_contract_receipt(); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8"); print(json.dumps({"status":result["status"],"mutations":result["synthetic_mutation_tests"]},sort_keys=True)); return 0 if result["status"]=="I19_PIT_COMPILER_CONTRACT_COMPLETED_NO_PERFORMANCE" else 2

if __name__=="__main__": raise SystemExit(main())