from automation.q104_i19_xbrl_pit_compiler import EXACT_CONCEPTS, _bundle, compile_issuer_state, mutation_tests, parse_utc, synthetic_bundle

def test_i19_synthetic_and_mutation_contracts_pass():
    assert all(synthetic_bundle().values())
    assert all(mutation_tests(_bundle()).values())

def test_i19_missing_prior_assets_fails_closed():
    b=_bundle(); filing=dict(b["filings"][0],facts=[x for x in b["filings"][0]["facts"] if x.get("instant")!="2024-12-31"])
    r=compile_issuer_state([filing],[],symbol="SPGI",cutoff=parse_utc("2025-04-02T00:00:00Z"))
    assert r["status"]=="MISSING" and "I19_PRIOR_ASSETS_MISSING" in r["reason"]

def test_i19_exact_concepts_are_frozen():
    assert EXACT_CONCEPTS=={"net_income_loss":"us-gaap:NetIncomeLoss","operating_cash_flow":"us-gaap:NetCashProvidedByUsedInOperatingActivities","assets":"us-gaap:Assets"}

def test_i19_amendment_form_outside_frozen_contract_is_rejected():
    b=_bundle(); bad=dict(b["filings"][1],form="10-Q/A")
    try: compile_issuer_state([bad],[],symbol="SPGI",cutoff=parse_utc("2025-04-04T00:00:00Z"))
    except ValueError as exc: assert "I19_FORM_NOT_ELIGIBLE" in str(exc)
    else: raise AssertionError("10-Q/A must remain outside the frozen base-form contract until explicitly expanded")