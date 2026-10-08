from automation.q104_i19_xbrl_pit_compiler import EXACT_CONCEPTS, _bundle, compile_issuer_state, mutation_tests, parse_edgar_eastern_to_utc, parse_utc, synthetic_bundle

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


def test_parse_utc_rejects_naive_timestamps():
    import pytest

    with pytest.raises(ValueError, match="TIMEZONE_REQUIRED"):
        parse_utc("2025-03-11T16:57:59")


def test_edgar_eastern_clock_normalizes_daylight_and_standard_time():
    daylight = parse_edgar_eastern_to_utc("2019-03-11T16:57:59")
    standard = parse_edgar_eastern_to_utc("2025-02-04T15:41:40")

    assert daylight.isoformat() == "2019-03-11T20:57:59+00:00"
    assert standard.isoformat() == "2025-02-04T20:41:40+00:00"


def test_edgar_eastern_clock_rejects_ambiguous_or_nonexistent_local_times():
    import pytest

    with pytest.raises(ValueError, match="AMBIGUOUS_OR_NONEXISTENT"):
        parse_edgar_eastern_to_utc("2024-11-03T01:30:00")
    with pytest.raises(ValueError, match="AMBIGUOUS_OR_NONEXISTENT"):
        parse_edgar_eastern_to_utc("2024-03-10T02:30:00")
